# QA Test Report — URL Shortener

**Tester:** Mark  
**Date:** 2026-04-24  
**Round:** 2 (re-test after engineering round 2)  
**Method:** Static code review (main.py + index.html vs discovery/brief.md ACs)  
**Verdict: FAIL**

---

## Primary bug under test: AC-R2 — click count decrement

Fix confirmed at `engineering/main.py:137`:

```python
conn.execute("UPDATE links SET click_count=click_count+1 WHERE slug=?", (slug,))
```

`+1` is in place. Original bug is resolved. ✓

---

## BLOCKER: AC-S1 — Auto-slug uppercase roundtrip failure (NOT FIXED)

**Severity: FAIL — blocks release.**

The decision log states: *"Reverted CHARS from base62 to base36 (lowercase + digits)"*. This change was **not applied**. The file still reads:

```python
# main.py line 16
CHARS = string.ascii_lowercase + string.ascii_uppercase + string.digits  # base62
```

`gen_slug()` produces mixed-case slugs stored verbatim in the DB. Both `redirect()` and `get_stats()` lowercase the slug before lookup:

```python
def redirect(slug: str):
    slug = slug.lower()           # "aBcDeF" → "abcdef"
    row = conn.execute("SELECT url FROM links WHERE slug=?", (slug,)).fetchone()
    # stored key is "aBcDeF" — NOT FOUND → 404
```

`get_stats()` has the identical problem (`slug.lower()` at line 119).

**Impact:** Any auto-generated slug containing one or more uppercase letters is permanently unreachable. Both redirect and stats return 404. Statistically ~66% of auto-slugs fail on first access.

**Required fix — one of:**
```python
# Option A: lowercase the output of gen_slug()
def gen_slug() -> str:
    return "".join(random.choices(CHARS, k=6)).lower()

# Option B: restrict charset to lowercase
CHARS = string.ascii_lowercase + string.digits  # base36
```

Note: Option B produces base36 slugs, which technically violates AC-S1's spec of base62 `[a-zA-Z0-9]`. However, AC-S1 and the custom slug validation regex (`[a-z0-9-]`) are in direct conflict — the custom slug path never allows uppercase. This is a spec issue, not an engineering issue; either fix resolves the live failure.

---

## 1. URL Validation

### AC-V1 — Non-http(s) schemes rejected with 422
**PASS** — `normalize_url` whitelist check via `urlparse`: `javascript:`, `data:`, `ftp://`, `file://` all rejected. ✓

### AC-V2 — No-scheme input auto-prefixed with https://
**PASS** — empty scheme → `https://` prepended. ✓

### AC-V3 — Double-prefix guard
**PASS** — scheme already in whitelist → no second prefix. ✓

### AC-V4 — Empty URL rejected with 422
**PASS** — blank/whitespace-only URL rejected before `normalize_url`. ✓

---

## 2. Auto-slug Generation

### AC-S1 — 6-char slug, base62
**FAIL** — see BLOCKER above. CHARS is base62 but the redirect/stats lookup lowercases first. Mixed-case auto-slugs are permanently unreachable.

### AC-S2 — 5 candidates on collision; 503 on exhaustion
**PASS** — `for _ in range(5)` loop with fallthrough to `HTTPException(503)`. ✓

---

## 3. Custom Slug Validation

### AC-S3 — Normalised to lowercase
**PASS** — `slug = req.slug.strip().lower()` before validation and insert. ✓

### AC-S4 — Regex pattern
**PASS** — `^[a-z0-9]([a-z0-9-]*[a-z0-9])?$` matches spec. ✓

### AC-S5 — Leading/trailing hyphens rejected
**PASS** — covered by regex. ✓

### AC-S6 — Length 3–50 chars
**PASS** — explicit length check before regex. ✓  
*Note: AC-S4 says "single-character slugs are allowed" but AC-S6 sets min=3. These contradict; the code enforces min=3 which is the safer choice.*

### AC-S7 — Duplicate slug → 409
**PASS** — `SELECT 1` before insert; `HTTPException(409)` on collision. ✓

### AC-S8 — Reserved paths rejected
**PASS** — `RESERVED` set checked after normalisation. ✓

---

## 4. Redirect

### AC-R1 — Valid slug returns 302
**PASS** — `RedirectResponse(..., status_code=302)`. ✓

### AC-R2 — Click count increments on every visit
**PASS (original bug fixed)** — `click_count+1` at line 137. ✓  
*Moot for any auto-slug containing uppercase, since those links are unreachable due to the BLOCKER.*

### AC-R3 — Unknown slug returns HTML 404
**PASS** — `HTMLResponse(_404_html(slug), ...)` not JSON. ✓

---

## 5. Stats

### AC-T1 — Click count displayed inline after creation
**PASS** — API returns `click_count`; frontend sets `clickCount` textContent. ✓

### AC-T2 — Manual refresh button
**PASS** — `refreshStats()` calls `GET api/links/{slug}/stats` on button click. ✓  
*Minor: no error feedback — network failure silently leaves count stale.*

### AC-T3 — No automatic polling
**PASS** — no `setInterval`, no `setTimeout` loop. ✓

---

## 6. Frontend UX
**PASS**
- Relative API paths: `fetch('api/links', ...)` and `fetch(\`api/links/${currentSlug}/stats\`)` — no leading slash. ✓
- Inputs cleared after successful create. ✓
- Error shown on failed create. ✓
- Lookup panel independent and functional. ✓
- XSS: `esc()` helper sanitises before `innerHTML`. ✓

*Minor: Result panel stays visible when a subsequent create fails — stale short URL shown alongside the new error.*

---

## Summary Table

| AC | Area | Round 1 | Round 2 |
|----|------|---------|---------|
| V1 | Scheme whitelist | PASS | PASS |
| V2 | No-scheme prefix | PASS | PASS |
| V3 | Double-prefix guard | PASS | PASS |
| V4 | Empty URL rejection | PASS | PASS |
| S1 | Auto-slug 6-char base62 | **FAIL** | **FAIL — not fixed** |
| S2 | Collision retry / 503 | PASS | PASS |
| S3 | Slug lowercase | PASS | PASS |
| S4 | Slug regex | PASS | PASS |
| S5 | No leading/trailing hyphens | PASS | PASS |
| S6 | Slug length 3–50 | PASS | PASS |
| S7 | Duplicate → 409 | PASS | PASS |
| S8 | Reserved paths | PASS | PASS |
| R1 | 302 redirect | PASS | PASS |
| R2 | Click count increment | PASS | PASS |
| R3 | HTML 404 | PASS | PASS |
| T1 | Inline click count | PASS | PASS |
| T2 | Refresh button | PASS | PASS |
| T3 | No polling | PASS | PASS |

---

## Blockers requiring engineering fix

**B1 — Auto-slug uppercase roundtrip (AC-S1):**  
The engineer recorded a decision to revert CHARS to base36 but the code was not changed. `main.py:16` still declares base62 with uppercase. Auto-generated slugs containing uppercase are stored verbatim but looked up lowercase — guaranteed 404 on redirect and stats. Fix is a one-line change in `gen_slug()` or the `CHARS` declaration.

---

## Minor notes (not blocking)

1. `refreshStats()` — no error feedback on fetch failure; count silently goes stale.
2. Result panel stays visible on subsequent create failure — stale URL alongside the error.
3. AC-S4/AC-S6 spec contradiction: S4 says single-char slugs are allowed, S6 sets min=3. Code enforces min=3 which is the safer behaviour.
4. Concurrent auto-slug INSERT race (negligible probability at 6-char space; unhandled 500 if it occurs).
