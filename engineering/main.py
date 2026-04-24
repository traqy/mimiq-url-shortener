import os
import random
import re
import sqlite3
import string
from contextlib import asynccontextmanager, contextmanager
from pathlib import Path
from urllib.parse import urlparse

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from pydantic import BaseModel

DB = Path(os.getenv("DB_PATH", str(Path(__file__).parent / "links.db")))
STATIC = Path(__file__).parent / "static"
CHARS = string.ascii_lowercase + string.digits  # base36 — consistent with lowercase-normalised slugs
RESERVED = {"api", "stats", "docs", "redoc", "openapi.json", "favicon.ico", "health"}


@contextmanager
def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


@asynccontextmanager
async def lifespan(app):
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS links (
                slug        TEXT PRIMARY KEY,
                url         TEXT NOT NULL,
                created_at  TEXT DEFAULT (datetime('now')),
                click_count INTEGER DEFAULT 0
            )
        """)
    yield


app = FastAPI(lifespan=lifespan)


class CreateReq(BaseModel):
    url: str
    slug: str | None = None


def normalize_url(url: str) -> str:
    url = url.strip()
    parsed = urlparse(url)
    if parsed.scheme:
        if parsed.scheme.lower() not in ("http", "https"):
            raise HTTPException(422, f"URL scheme '{parsed.scheme}' is not allowed — use http or https")
    else:
        url = "https://" + url
    return url


def gen_slug() -> str:
    return "".join(random.choices(CHARS, k=6))


@app.get("/", response_class=FileResponse)
def index():
    return FileResponse(STATIC / "index.html")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/links", status_code=201)
def create_link(req: CreateReq):
    if not req.url.strip():
        raise HTTPException(422, "URL must not be blank")
    url = normalize_url(req.url)

    if req.slug:
        slug = req.slug.strip().lower()
        if len(slug) < 3 or len(slug) > 50:
            raise HTTPException(422, "Slug must be 3–50 characters")
        if slug in RESERVED:
            raise HTTPException(422, f"'{slug}' is a reserved path")
        if not re.match(r"^[a-z0-9]([a-z0-9-]*[a-z0-9])?$", slug):
            raise HTTPException(422, "Slug: alphanumeric + hyphens, no leading/trailing hyphens")
        with get_db() as conn:
            if conn.execute("SELECT 1 FROM links WHERE slug=?", (slug,)).fetchone():
                raise HTTPException(409, f"'{slug}' is already taken")
            conn.execute("INSERT INTO links (slug, url) VALUES (?,?)", (slug, url))
        return {"slug": slug, "url": url, "click_count": 0}

    for _ in range(5):
        slug = gen_slug()
        if slug in RESERVED:
            continue
        with get_db() as conn:
            if not conn.execute("SELECT 1 FROM links WHERE slug=?", (slug,)).fetchone():
                conn.execute("INSERT INTO links (slug, url) VALUES (?,?)", (slug, url))
                return {"slug": slug, "url": url, "click_count": 0}

    raise HTTPException(503, "Could not generate a unique slug — try again")


@app.get("/api/links/{slug}/stats")
def get_stats(slug: str):
    with get_db() as conn:
        row = conn.execute(
            "SELECT slug, url, click_count, created_at FROM links WHERE slug=?",
            (slug.lower(),),
        ).fetchone()
    if not row:
        raise HTTPException(404, "Link not found")
    return dict(row)


@app.get("/favicon.ico")
def favicon():
    raise HTTPException(404)


@app.get("/{slug}")
def redirect(slug: str):
    slug = slug.lower()
    with get_db() as conn:
        row = conn.execute("SELECT url FROM links WHERE slug=?", (slug,)).fetchone()
        if not row:
            return HTMLResponse(_404_html(slug), status_code=404)
        conn.execute("UPDATE links SET click_count=click_count+1 WHERE slug=?", (slug,))
    return RedirectResponse(row["url"], status_code=302)


def _404_html(slug: str) -> str:
    return f"""<!doctype html><html><head><meta charset=utf-8><title>404</title>
<style>body{{font-family:system-ui;display:flex;align-items:center;justify-content:center;
height:100vh;margin:0;background:#f9fafb}}.box{{text-align:center}}
h1{{font-size:5rem;margin:0;color:#1f2937}}p{{color:#6b7280}}a{{color:#6366f1}}</style></head>
<body><div class=box><h1>404</h1><p>No link found for <code>/{slug}</code></p>
<a href=/>← Create a short link</a></div></body></html>"""
