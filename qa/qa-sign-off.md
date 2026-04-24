# QA Sign-off — URL Shortener

**Tester:** Mark  
**Date:** 2026-04-24  
**Verdict: FAIL — NOT APPROVED FOR RELEASE**

---

## Bug fix verification

Issue #1 (click counter decrementing): **Fixed.** `click_count+1` confirmed at `engineering/main.py:137`.

---

## Blocker found during QA

**Auto-slug uppercase roundtrip failure.**

The engineer changed `CHARS` to base62 to match AC-S1, but `gen_slug()` produces mixed-case slugs that are stored verbatim. Both `redirect()` and `get_stats()` lowercase the slug before DB lookup. Any auto-generated slug containing an uppercase letter is permanently unreachable — redirect returns 404, stats returns 404. Approximately 66% of auto-slugs are broken on creation.

The original bug is fixed but this regression is introduced in the same change.

---

## Required before re-approval

Either:
- Add `.lower()` to `gen_slug()` return value, **or**
- Restrict `CHARS` to `string.ascii_lowercase + string.digits`

Then re-run QA.

---

## Minor notes (not blocking re-approval)

1. `refreshStats()` — no error feedback on fetch failure.
2. Result panel stays visible on subsequent create failure.
3. Concurrent auto-slug INSERT race — negligible probability.
