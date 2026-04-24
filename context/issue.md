# Issue #1: Click counter decrements instead of incrementing on each redirect

## Bug report

**Describe the bug**
Every time a short link is visited, the click counter goes negative instead of counting up. After 3 clicks the count shows `-3` instead of `3`.

**To reproduce**
1. Create a short link (e.g. `test` → `https://example.com`)
2. Click the short link or visit `/test` directly
3. Check stats — click count is `-1`
4. Click again — count is `-2`

**Expected behaviour**
Click count should increment by 1 on each redirect.

**Actual behaviour**
Click count decrements by 1 on each redirect.

**Likely location**
`main.py` in the redirect handler — the SQL update that tracks clicks.

**URL:** https://github.com/traqy/mimiq-url-shortener/issues/1
