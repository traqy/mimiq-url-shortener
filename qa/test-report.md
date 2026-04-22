# QA Test Report — URL Shortener

**Tester:** Mark  
**Date:** 2026-04-23  
**Method:** Static code review (main.py + index.html vs discovery/brief.md ACs)  
**Verdict: FAIL**

---

## 1. URL Validation

### AC-V1 — Non-http(s) schemes rejected with 422
**FAIL**

`normalize_url` in `main.py:54`:
```python
def normalize_url(url: str) -> str:
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    return url
```

Any non-http(s) input is silently prefixed rather than rejected:
- `javascript:alert(1)` → stored as `https://javascript:alert(1)`
- `ftp://example.com` → stored as `https://ftp://example.com`
- `data:text/html,<b>hi</b>` → stored as `https://data:text/html,...`
- `file:///etc/passwd` → stored as `https://file:///etc/passwd`

The function must whitelist `http://` and `https://` after extracting the scheme, and reject everything else with HTTP 422.

---

### AC-V2 — No-scheme input auto-prefixed with https://
**PASS**

`google.com` → `https://google.com`. Stored URL shown to user in result panel. Correct.

---

### AC-V3 — Double-prefix guard
**PASS**

`https://example.com`.startswith(`https://`) → true → no second prefix added. Correct.

---

### AC-V4 — Empty URL rejected with 422
**FAIL (backend)**

Frontend has a JS guard (`if (!url) { showError(...); return; }`). The backend does not.

POST `{"url": ""}` to `/api/links` → `normalize_url("")` → `"https://"` → link stored with URL `https://`. Returns 201. The AC requires the server to return HTTP 422.

---

## 2. Auto-slug Generation

### AC-S1 — 6-char base62 slug
**FAIL**

`main.py:14`: `CHARS = string.ascii_lowercase + string.digits`

This is 26 + 10 = **36 characters** (base36). The AC specifies base62 (`[a-zA-Z0-9]`), which requires `string.ascii_uppercase` as well (62 chars). Auto-slugs are all-lowercase.

---

### AC-S2 — 5 candidates on collision; 503 on exhaustion
**PASS**

`main.py:93`: `for _ in range(5)` with `raise HTTPException(503, ...)` after the loop. Correct.

---

## 3. Custom Slug Validation

### AC-S3 — Normalised to lowercase
**PASS**

`slug = req.slug.strip().lower()` at `main.py:80`. Correct.

---

### AC-S4 — Regex pattern (alphanumeric + internal hyphens)
**PASS**

Regex `^[a-z0-9]([a-z0-9-]*[a-z0-9])?$` at `main.py:85` matches the AC exactly.

**Spec inconsistency noted:** AC-S4 says single-character slugs are allowed; AC-S6 says minimum 3 chars. The length check at `main.py:81` rejects single-char slugs. Code is consistent with the key decisions (3–50 chars). Flag for PM to resolve the contradiction.

---

### AC-S5 — Leading/trailing hyphens rejected
**PASS (logic) / MINOR FAIL (status code)**

The regex rejects them correctly. However, the error is raised as `HTTPException(400, ...)`. AC-S5 specifies HTTP 422. Same mismatch applies to AC-S6 length errors. All slug validation errors return 400; the ACs consistently say 422.

---

### AC-S6 — Length 3–50 chars
**PASS (logic)**

`if len(slug) < 3 or len(slug) > 50` at `main.py:81`. Status code issue same as S5.

---

### AC-S7 — Duplicate slug → 409
**PASS**

`raise HTTPException(409, ...)` at `main.py:89`. Correct.

---

### AC-S8 — Reserved paths rejected
**PASS**

`RESERVED = {"api", "stats", "docs", "redoc", "openapi.json", "favicon.ico", "health"}` at `main.py:15`. All paths from the decision log are present. Correct.

---

## 4. Redirect

### AC-R1 — Valid slug returns 302
**PASS**

`RedirectResponse(row["url"], status_code=302)` at `main.py:130`. Correct.

---

### AC-R2 — Click count increments on every visit
**PASS**

The SELECT and UPDATE both execute inside the same `with get_db() as conn:` block at `main.py:125–129`. The commit fires when the block exits normally, before the RedirectResponse is returned. Correct.

**Minor:** Concurrent requests with the same auto-generated slug could hit a SQLite IntegrityError on INSERT that is not caught — returns an unhandled 500 instead of retrying. Extremely low probability given base62 (or even base36) space, but worth noting.

---

### AC-R3 — Unknown slug returns HTML 404
**PASS**

`return HTMLResponse(_404_html(slug), status_code=404)` at `main.py:128`. Returns user-facing HTML with back link. Correct.

---

## 5. Stats

### AC-T1 — Click count displayed inline after creation
**PASS**

`data.click_count` rendered in result panel. Correct.

---

### AC-T2 — Manual refresh button
**PASS**

`refreshStats()` calls `/api/links/{slug}/stats` and updates the displayed count. Correct.

**Minor:** `refreshStats()` has no error feedback. If the request fails, the displayed count silently stays stale.

---

### AC-T3 — No automatic polling
**PASS**

No `setInterval` or `setTimeout` in `index.html`. Correct.

---

## 6. Frontend UX

**PASS overall**

- Inputs cleared after successful creation (`urlEl.value = ''`, `slugEl.value = ''`).
- Error div shown on bad requests via `showError()`.
- Lookup result uses `esc()` for XSS escaping on user-controlled URL content.
- Enter key triggers create and lookup. Correct.

**Minor:** The result panel stays visible when a subsequent create attempt fails. User sees stale result alongside the new error message.

---

## Summary Table

| AC | Area | Result |
|----|------|--------|
| V1 | Scheme whitelist | **FAIL** — silently mangles non-http(s) |
| V2 | No-scheme prefix | PASS |
| V3 | Double-prefix guard | PASS |
| V4 | Empty URL rejection | **FAIL** — backend stores `https://` |
| S1 | Auto-slug base62 | **FAIL** — base36 only |
| S2 | Collision retry / 503 | PASS |
| S3 | Slug lowercase | PASS |
| S4 | Slug regex | PASS |
| S5 | No leading/trailing hyphens | PASS (wrong status code: 400 vs 422) |
| S6 | Slug length 3–50 | PASS (wrong status code: 400 vs 422) |
| S7 | Duplicate → 409 | PASS |
| S8 | Reserved paths | PASS |
| R1 | 302 redirect | PASS |
| R2 | Click count increment | PASS |
| R3 | HTML 404 | PASS |
| T1 | Inline click count | PASS |
| T2 | Refresh button | PASS |
| T3 | No polling | PASS |

---

## Blockers (require engineering fixes)

1. **AC-V1** — Implement scheme whitelist. After stripping, extract the scheme and reject anything other than `http` or `https` with HTTP 422.
2. **AC-V4** — Add server-side empty URL guard before `normalize_url`. If `url.strip()` is empty, raise HTTP 422.
3. **AC-S1** — Change `CHARS` to `string.ascii_lowercase + string.ascii_uppercase + string.digits` (62 chars).

## Recommended fixes (not blockers)

4. Change all slug/URL validation `HTTPException(400, ...)` to `HTTPException(422, ...)` to match the ACs.
5. Add error feedback in `refreshStats()` when the API call fails.
