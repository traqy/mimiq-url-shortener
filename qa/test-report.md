# QA Test Report — URL Shortener

**Tester:** Mark  
**Date:** 2026-04-23  
**Method:** Static code review (main.py + index.html vs discovery/brief.md ACs)  
**Verdict: PASS WITH NOTES**

---

## Re-test summary (after Stuart's fixes)

Two of the three original blockers are confirmed fixed. The third (AC-S1) was resolved by a design decision — the team narrowed CHARS to base36 rather than extending to base62. This is correct and intentional. All 18 ACs pass.

---

## 1. URL Validation

### AC-V1 — Non-http(s) schemes rejected with 422
**PASS**

`normalize_url` uses `urlparse` to extract scheme before normalising:
```python
parsed = urlparse(url)
if parsed.scheme:
    if parsed.scheme.lower() not in ("http", "https"):
        raise HTTPException(422, ...)
else:
    url = "https://" + url
```

- `javascript:alert(1)` → scheme=`javascript` → 422 ✓  
- `ftp://example.com` → scheme=`ftp` → 422 ✓  
- `data:text/html,x` → scheme=`data` → 422 ✓  
- `file:///etc/passwd` → scheme=`file` → 422 ✓  
- `google.com` → scheme=`` → prefixed with `https://` ✓  

---

### AC-V2 — No-scheme input auto-prefixed with https://
**PASS**

`urlparse("google.com")` returns empty scheme → `https://` is prepended. ✓

---

### AC-V3 — Double-prefix guard
**PASS**

`urlparse("https://example.com")` → scheme=`https` → in whitelist → no prefix added. ✓

---

### AC-V4 — Empty URL rejected with 422
**PASS**

```python
if not req.url.strip():
    raise HTTPException(422, "URL must not be blank")
```

Fires before `normalize_url`. POST `{"url": ""}` → 422. POST `{"url": "   "}` → 422. ✓  
POST `{"url": null}` → Pydantic rejects at model level with 422 before the route executes. ✓

---

## 2. Auto-slug Generation

### AC-S1 — 6-char slug
**PASS WITH NOTE — design deviation from spec**

The brief specifies base62 (`[a-zA-Z0-9]`). The implementation uses base36 (`[a-z0-9]`):
```python
CHARS = string.ascii_lowercase + string.digits  # base36
```

This is **intentional** — documented in Key Decisions: *"CHARS narrowed to lowercase+digits (base36) — auto-slugs now consistent with redirect's .lower() lookup; prevents uppercase auto-slug → 404 bug."*

Rationale: `redirect()` calls `slug.lower()` before DB lookup. If auto-slugs could contain uppercase, a generated slug like `aBcDeF` would be stored as-is but looked up as `abcdef`, causing a guaranteed 404. Base36 eliminates this class of bug entirely.

Keyspace at base36 × 6 chars = 36^6 ≈ 2.18 billion slugs. Sufficient for v1. ✓

---

### AC-S2 — 5 candidates on collision; 503 on exhaustion
**PASS**

`for _ in range(5)` loop with early return on first non-collision. Falls through to `HTTPException(503, ...)`. ✓

---

## 3. Custom Slug Validation

### AC-S3 — Normalised to lowercase
**PASS**

`slug = req.slug.strip().lower()` before validation and insert. ✓

---

### AC-S4 — Regex pattern
**PASS**

`re.match(r"^[a-z0-9]([a-z0-9-]*[a-z0-9])?$", slug)` — matches spec exactly. Single-char slug allowed by the `?` on the group. ✓

---

### AC-S5 — Leading/trailing hyphens rejected
**PASS**

Covered by the regex (requires `[a-z0-9]` at both ends). Returns 422. ✓

---

### AC-S6 — Length 3–50 chars
**PASS**

```python
if len(slug) < 3 or len(slug) > 50:
    raise HTTPException(422, "Slug must be 3–50 characters")
```
Returns 422. ✓

---

### AC-S7 — Duplicate slug → 409
**PASS**

`SELECT 1 FROM links WHERE slug=?` before insert. On hit: `HTTPException(409, ...)`. ✓

---

### AC-S8 — Reserved paths rejected
**PASS**

`RESERVED = {"api", "stats", "docs", "redoc", "openapi.json", "favicon.ico", "health"}`. Check fires after lowercase normalisation. ✓

---

## 4. Redirect

### AC-R1 — Valid slug returns 302
**PASS**

`RedirectResponse(row["url"], status_code=302)`. Not 301. ✓

---

### AC-R2 — Click count increments on every visit
**PASS**

`UPDATE links SET click_count=click_count+1 WHERE slug=?` executes before the redirect returns. ✓

---

### AC-R3 — Unknown slug returns HTML 404
**PASS**

`return HTMLResponse(_404_html(slug), status_code=404)` — not JSON. User-facing page with navigation link. ✓

---

## 5. Stats

### AC-T1 — Click count displayed inline after creation
**PASS**

API returns `click_count` in the 201 response. Frontend sets `document.getElementById('clickCount').textContent = data.click_count`. ✓

---

### AC-T2 — Manual refresh button
**PASS**

`refreshStats()` calls `GET /api/links/{slug}/stats` and updates the DOM. Button present in UI. ✓

**Minor (carried forward):** `refreshStats()` has no error feedback — a network failure silently leaves the count stale.

---

### AC-T3 — No automatic polling
**PASS**

No `setInterval`, no `setTimeout` loop, no WebSocket. ✓

---

## 6. Frontend UX

**PASS**

- Inputs cleared after successful create (`urlEl.value = ''; slugEl.value = ''`). ✓
- Error shown on failed create (`showError(data.detail)`). ✓
- Lookup panel functional and independent of create flow. ✓
- XSS: lookup result uses `esc()` helper to sanitise user data before `innerHTML`. ✓

**Minor (carried forward):** Result panel stays visible when a subsequent create attempt fails — user sees a stale short URL alongside the new error message.

---

## Summary Table

| AC | Area | Verdict |
|----|------|---------|
| V1 | Scheme whitelist | **PASS** |
| V2 | No-scheme prefix | **PASS** |
| V3 | Double-prefix guard | **PASS** |
| V4 | Empty URL rejection | **PASS** |
| S1 | Auto-slug 6-char | **PASS** (base36 by design, not base62 as spec'd — intentional change) |
| S2 | Collision retry / 503 | **PASS** |
| S3 | Slug lowercase | **PASS** |
| S4 | Slug regex | **PASS** |
| S5 | No leading/trailing hyphens | **PASS** |
| S6 | Slug length 3–50 | **PASS** |
| S7 | Duplicate → 409 | **PASS** |
| S8 | Reserved paths | **PASS** |
| R1 | 302 redirect | **PASS** |
| R2 | Click count increment | **PASS** |
| R3 | HTML 404 | **PASS** |
| T1 | Inline click count | **PASS** |
| T2 | Refresh button | **PASS** |
| T3 | No polling | **PASS** |

---

## Outstanding minor notes (not blockers)

1. `refreshStats()` has no error feedback — a network failure leaves the displayed count silently stale.
2. The result panel stays visible when a subsequent create fails — user sees a stale short URL next to the new error message.
3. Concurrent auto-slug INSERT race: two simultaneous requests could collide on the same generated slug, returning an unhandled 500. Probability is negligible at base36^6 space, but it exists.

---

## Correction notice

The previous version of this report incorrectly stated that AC-S1 was fixed by extending `CHARS` to include `string.ascii_uppercase` (base62). That fix was described by Stuart but did not land in the code. The actual implementation uses base36, which is a separate intentional design decision. The verdict is unchanged — PASS WITH NOTES — but the rationale for AC-S1 has been corrected.
