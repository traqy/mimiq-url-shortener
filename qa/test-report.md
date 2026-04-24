# QA Test Report — URL Shortener

**Tester:** Mark  
**Date:** 2026-04-24  
**Method:** Static code review (main.py + index.html vs discovery/brief.md ACs)  
**Verdict: FAIL**

---

## Primary bug under test: AC-R2 — click count decrement

Fix confirmed at `engineering/main.py:137`:

```python
conn.execute("UPDATE links SET click_count=click_count+1 WHERE slug=?", (slug,))
```

`+1` is in place. Original bug is gone. ✓

---

## BLOCKER: AC-S1 / AC-R2 — Auto-slug uppercase roundtrip failure

**Severity: FAIL — blocks release.**

The engineer changed `CHARS` to base62 to match the spec:

```python
# main.py line 16
CHARS = string.ascii_lowercase + string.ascii_uppercase + string.digits  # base62
```

However, `gen_slug()` returns slugs with original casing and the `create_link` path stores them as-is — no `.lower()` on auto-generated slugs:

```python
def gen_slug() -> str:
    return "".join(random.choices(CHARS, k=6))  # may return e.g. "aBcDeF"

# stored verbatim:
conn.execute("INSERT INTO links (slug, url) VALUES (?,?)", (slug, url))
```

But `redirect()` lowercases before lookup:

```python
def redirect(slug: str):
    slug = slug.lower()  # "aBcDeF" → "abcdef"
    row = conn.execute("SELECT url FROM links WHERE slug=?", (slug,)).fetchone()
    # looks up "abcdef"; stored key is "aBcDeF" — NOT FOUND → 404
```

`get_stats()` has the same problem (`slug.lower()` at line 118).

**Reproduces:** Create a link without a custom slug. If the auto-generated slug contains any uppercase letter (base62 → ~66% chance on first char), every subsequent redirect and stats lookup returns 404/not-found. The create response shows the correct slug and click count of 0, but the link is permanently broken.

**Fix:** Either lowercase the generated slug before insert in `gen_slug()` or `create_link()`, or restrict `CHARS` back to `string.ascii_lowercase + string.digits`.

---

## 1. URL Validation

### AC-V1 — Non-http(s) schemes rejected with 422
**PASS**

`normalize_url` checks scheme via `urlparse` before storing:
- `javascript:alert(1)` → 422 ✓
- `ftp://example.com` → 422 ✓
- `data:text/html,x` → 422 ✓
- `file:///etc/passwd` → 422 ✓

### AC-V2 — No-scheme input auto-prefixed with https://
**PASS** — empty scheme → `https://` prepended. ✓

### AC-V3 — Double-prefix guard
**PASS** — `urlparse("https://example.com")` → scheme in whitelist → no second prefix. ✓

### AC-V4 — Empty URL rejected with 422
**PASS** — blank/whitespace-only URL rejected before `normalize_url`. ✓

---

## 2. Auto-slug Generation

### AC-S1 — 6-char slug, base62
**FAIL** — see BLOCKER above. CHARS is base62 but stored slugs are mixed-case while lookups are lowercased. A slug containing any uppercase letter is unreachable.

### AC-S2 — 5 candidates on collision; 503 on exhaustion
**PASS** — `for _ in range(5)` loop with fall-through to `HTTPException(503)`. ✓

---

## 3. Custom Slug Validation

### AC-S3 — Normalised to lowercase
**PASS** — `slug = req.slug.strip().lower()` before validation and insert. ✓

### AC-S4 — Regex pattern
**PASS** — `^[a-z0-9]([a-z0-9-]*[a-z0-9])?$` matches spec; single-char allowed. ✓

### AC-S5 — Leading/trailing hyphens rejected
**PASS** — covered by regex. ✓

### AC-S6 — Length 3–50 chars
**PASS** — explicit length check before regex. ✓

### AC-S7 — Duplicate slug → 409
**PASS** — `SELECT 1` before insert; `HTTPException(409)` on hit. ✓

### AC-S8 — Reserved paths rejected
**PASS** — `RESERVED` set checked after normalisation. ✓

---

## 4. Redirect

### AC-R1 — Valid slug returns 302
**PASS** — `RedirectResponse(..., status_code=302)`. ✓

### AC-R2 — Click count increments on every visit
**PASS (original bug fixed)** — `click_count+1` confirmed at line 137. ✓  
*However, if slug is unreachable due to the BLOCKER above, the counter never fires.*

### AC-R3 — Unknown slug returns HTML 404
**PASS** — `HTMLResponse(_404_html(slug), ...)` not JSON. ✓

---

## 5. Stats

### AC-T1 — Click count displayed inline after creation
**PASS** — API returns `click_count`; frontend sets `clickCount` textContent. ✓

### AC-T2 — Manual refresh button
**PASS** — `refreshStats()` calls `GET /api/links/{slug}/stats` on button click. ✓  
**Minor:** no error feedback — network failure silently leaves count stale.

### AC-T3 — No automatic polling
**PASS** — no `setInterval`, no `setTimeout` loop. ✓

---

## 6. Frontend UX
**PASS**
- Inputs cleared after successful create. ✓
- Error shown on failed create. ✓
- Lookup panel independent and functional. ✓
- XSS: `esc()` helper sanitises before `innerHTML`. ✓

**Minor:** Result panel stays visible when a subsequent create fails — user sees stale short URL alongside the new error.

---

## Summary Table

| AC | Area | Verdict |
|----|------|---------|
| V1 | Scheme whitelist | PASS |
| V2 | No-scheme prefix | PASS |
| V3 | Double-prefix guard | PASS |
| V4 | Empty URL rejection | PASS |
| S1 | Auto-slug 6-char base62 | **FAIL — uppercase case mismatch** |
| S2 | Collision retry / 503 | PASS |
| S3 | Slug lowercase | PASS |
| S4 | Slug regex | PASS |
| S5 | No leading/trailing hyphens | PASS |
| S6 | Slug length 3–50 | PASS |
| S7 | Duplicate → 409 | PASS |
| S8 | Reserved paths | PASS |
| R1 | 302 redirect | PASS |
| R2 | Click count increment | PASS (original bug fixed) |
| R3 | HTML 404 | PASS |
| T1 | Inline click count | PASS |
| T2 | Refresh button | PASS |
| T3 | No polling | PASS |

---

## Blockers requiring engineering fix

**B1 — Auto-slug uppercase roundtrip (AC-S1, AC-R2, AC-T2):**  
`CHARS` includes uppercase but `redirect()` and `get_stats()` lowercase before lookup. Auto-generated slugs containing uppercase are permanently unreachable. ~66% of auto-slugs are affected on first generation.

Fix in `gen_slug()`:
```python
def gen_slug() -> str:
    return "".join(random.choices(CHARS, k=6)).lower()
```
Or restrict CHARS: `CHARS = string.ascii_lowercase + string.digits`

---

## Minor notes (not blocking)

1. `refreshStats()` — no error feedback on fetch failure; count goes silently stale.
2. Result panel stays visible on subsequent create failure — stale short URL alongside error.
3. Concurrent auto-slug INSERT race — negligible probability at 6-char space; would surface as unhandled 500.
