# QA Sign-off — URL Shortener

**Tester:** Mark  
**Date:** 2026-04-23  
**Verdict: FAIL — NOT APPROVED FOR RELEASE**

---

## Blockers

Three acceptance criteria failures require engineering fixes:

| # | AC | Issue |
|---|----|-------|
| 1 | AC-V1 | Non-http(s) URL schemes not rejected — silently mangled and stored |
| 2 | AC-V4 | Backend accepts empty URL — stores link with URL `https://` |
| 3 | AC-S1 | Auto-slug uses base36 (lowercase + digits) instead of base62 |

All three are functional correctness failures, not cosmetic issues.

---

## What passes

302 redirect, click count increment, HTML 404, custom slug validation, collision retry, stats endpoint, duplicate 409, manual refresh, no polling, inline stats, input clearing, XSS escaping.

The foundation is solid. Three targeted fixes are all that stand between this build and a passing QA run.

---

## Re-test scope

After fixes, re-verify:
- POST `{"url": "javascript:alert(1)"}` → HTTP 422
- POST `{"url": "ftp://x.com"}` → HTTP 422
- POST `{"url": "data:text/html,x"}` → HTTP 422
- POST `{"url": ""}` → HTTP 422
- POST `{"url": null}` → HTTP 422
- Auto-generated slug contains at least one uppercase letter over a sample of 20 slugs
- All existing passing ACs remain unaffected
