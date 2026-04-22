# QA Test Report — URL Shortener

**Tester:** Mark  
**Date:** 2026-04-23  
**Method:** Static code review (main.py + index.html vs discovery/brief.md ACs)  
**Verdict: PASS WITH NOTES**

---

## Re-test summary (after Stuart's fixes)

All three blockers from the initial FAIL report are resolved. Minor notes carried forward — none are release blockers.

---

## 1. URL Validation

### AC-V1 — Non-http(s) schemes rejected with 422
**PASS**

`normalize_url` now uses `urlparse` to extract the scheme before deciding what to do:
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
**PASS** *(unchanged from first report)*

---

### AC-V3 — Double-prefix guard
**PASS** *(unchanged from first report)*

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

### AC-S1 — 6-char base62 slug
**PASS**

`CHARS = string.ascii_lowercase + string.ascii_uppercase + string.digits` = 26 + 26 + 10 = 62. ✓

---

### AC-S2 — 5 candidates on collision; 503 on exhaustion
**PASS** *(unchanged)*

---

## 3. Custom Slug Validation

### AC-S3 — Normalised to lowercase
**PASS** *(unchanged)*

---

### AC-S4 — Regex pattern
**PASS** *(unchanged)*

---

### AC-S5 — Leading/trailing hyphens rejected
**PASS**

Status code corrected: `HTTPException(422, ...)`. ✓

---

### AC-S6 — Length 3–50 chars
**PASS**

Status code corrected: `HTTPException(422, ...)`. ✓

---

### AC-S7 — Duplicate slug → 409
**PASS** *(unchanged)*

---

### AC-S8 — Reserved paths rejected
**PASS** *(unchanged)*

---

## 4. Redirect

### AC-R1 — Valid slug returns 302
**PASS** *(unchanged)*

---

### AC-R2 — Click count increments on every visit
**PASS** *(unchanged)*

---

### AC-R3 — Unknown slug returns HTML 404
**PASS** *(unchanged)*

---

## 5. Stats

### AC-T1 — Click count displayed inline after creation
**PASS** *(unchanged)*

---

### AC-T2 — Manual refresh button
**PASS** *(unchanged)*

**Minor (carried forward):** `refreshStats()` has no error feedback — failed fetch silently leaves count stale.

---

### AC-T3 — No automatic polling
**PASS** *(unchanged)*

---

## 6. Frontend UX

**PASS overall** *(unchanged)*

**Minor (carried forward):** Result panel stays visible when a subsequent create attempt fails — user sees stale short URL alongside the new error.

---

## Summary Table

| AC | Area | First report | Re-test |
|----|------|--------------|---------|
| V1 | Scheme whitelist | **FAIL** | **PASS** |
| V2 | No-scheme prefix | PASS | PASS |
| V3 | Double-prefix guard | PASS | PASS |
| V4 | Empty URL rejection | **FAIL** | **PASS** |
| S1 | Auto-slug base62 | **FAIL** | **PASS** |
| S2 | Collision retry / 503 | PASS | PASS |
| S3 | Slug lowercase | PASS | PASS |
| S4 | Slug regex | PASS | PASS |
| S5 | No leading/trailing hyphens | PASS (422 wrong) | PASS |
| S6 | Slug length 3–50 | PASS (422 wrong) | PASS |
| S7 | Duplicate → 409 | PASS | PASS |
| S8 | Reserved paths | PASS | PASS |
| R1 | 302 redirect | PASS | PASS |
| R2 | Click count increment | PASS | PASS |
| R3 | HTML 404 | PASS | PASS |
| T1 | Inline click count | PASS | PASS |
| T2 | Refresh button | PASS | PASS |
| T3 | No polling | PASS | PASS |

---

## Outstanding minor notes (not blockers)

1. `refreshStats()` has no error feedback — a network failure leaves the displayed count silently stale.
2. The result panel stays visible when a subsequent create fails — user sees a stale short URL next to the new error message.
3. Concurrent auto-slug INSERT race: two simultaneous requests could collide on the same generated slug, returning an unhandled 500. Probability is negligible at base62 space, but it exists.
