# QA Test Plan — URL Shortener

**Tester:** Mark  
**Date:** 2026-04-23  
**Build:** engineering/main.py + engineering/static/index.html  
**Method:** Static code review against acceptance criteria in discovery/brief.md

---

## Areas

### 1. URL Validation (AC-V1 through AC-V4)
- V1: Non-http(s) schemes rejected with 422
- V2: No-scheme input auto-prefixed with https://
- V3: Double-prefix guard (https:// not prepended when already present)
- V4: Empty URL rejected with 422

### 2. Auto-slug Generation (AC-S1, AC-S2)
- S1: 6-char, base62 charset [a-zA-Z0-9]
- S2: Up to 5 candidates on collision; 503 on exhaustion

### 3. Custom Slug Validation (AC-S3 through AC-S8)
- S3: Normalised to lowercase
- S4: Regex pattern — alphanumeric + internal hyphens, single-char allowed
- S5: Leading/trailing hyphens rejected
- S6: Length 3–50 chars
- S7: Duplicate slug → 409
- S8: Reserved paths rejected (api, stats, docs, redoc, openapi.json, favicon.ico, health)

### 4. Redirect (AC-R1 through AC-R3)
- R1: Valid slug returns 302 (not 301)
- R2: Click count increments on every visit
- R3: Unknown slug returns HTML 404 (not JSON)

### 5. Stats (AC-T1 through AC-T3)
- T1: Click count shown inline after creation
- T2: Manual refresh button re-fetches count
- T3: No automatic polling

### 6. Frontend UX
- Input cleared after successful creation
- Error shown on failed create
- Lookup panel works independently
- XSS escaping in rendered user data

### 7. Security
- No script/data URI stored and redirected
- No XSS in lookup result rendering
