# QA Sign-off — URL Shortener

**Tester:** Mark  
**Date:** 2026-04-23  
**Verdict: PASS WITH NOTES — APPROVED FOR RELEASE**

---

## Result

All three blockers from the initial FAIL report are resolved. All 18 acceptance criteria pass. Three minor notes remain — none break functionality.

---

## What was fixed

| # | AC | Fix |
|---|----|-----|
| 1 | AC-V1 | `urlparse` scheme extraction + whitelist; non-http(s) inputs now raise 422 |
| 2 | AC-V4 | Server-side blank URL guard fires before `normalize_url` |
| 3 | AC-S1 | `CHARS` extended to full base62 (`ascii_lowercase + ascii_uppercase + digits`) |
| 4 | AC-S5/S6 | Slug validation errors changed from 400 to 422 |

---

## Minor notes (not blocking release)

1. `refreshStats()` — no error feedback on fetch failure; count goes silently stale.
2. Result panel — stays visible when a subsequent create fails, showing a stale short URL alongside the error.
3. Concurrent auto-slug INSERT race — negligible probability at base62 space; would surface as an unhandled 500.

---

## Approved

The build meets all acceptance criteria. Ship it.
