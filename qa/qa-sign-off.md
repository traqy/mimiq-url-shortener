# QA Sign-off — URL Shortener

**Tester:** Mark  
**Date:** 2026-04-24  
**Round:** 2  
**Verdict: FAIL — NOT APPROVED FOR RELEASE**

---

## Bug fix verification

Issue #1 (click counter decrementing): **Fixed.** `click_count+1` confirmed at `engineering/main.py:137`. ✓

---

## Blocker — CHARS revert not applied

The decision log records *"Reverted CHARS from base62 to base36"* but `main.py:16` still reads:

```python
CHARS = string.ascii_lowercase + string.ascii_uppercase + string.digits  # base62
```

The code was not changed. The auto-slug uppercase roundtrip failure from round 1 is still present. ~66% of auto-generated slugs will 404 on redirect and stats lookup.

---

## Required before re-approval

Apply the one-line fix that was declared but not committed:

```python
# Option A — lowercase at generation time
def gen_slug() -> str:
    return "".join(random.choices(CHARS, k=6)).lower()

# Option B — restrict CHARS to lowercase+digits
CHARS = string.ascii_lowercase + string.digits
```

Then re-submit for QA round 3.

---

## Minor notes (not blocking re-approval)

1. `refreshStats()` — no error feedback on fetch failure.
2. Result panel stays visible on subsequent create failure.
3. AC-S4/AC-S6 spec contradiction (single-char allowed vs min 3); code behaviour is correct, spec is inconsistent.
4. Concurrent auto-slug INSERT race — negligible at this scale.
