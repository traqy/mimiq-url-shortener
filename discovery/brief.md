# Product Requirements Document — URL Shortener

> Status: Engineering-ready. All decisions locked.

---

## 1. Problem

Sharing long URLs is ugly and unwieldy. There is no lightweight, self-hosted tool that lets a developer paste a long URL, get a short one instantly, and watch the click counter increment in real time — without signing up for a SaaS product or deploying a heavy stack.

## 2. Target Users

**Primary:** Developers and technical users who want a self-hosted short link tool they can demo, hack on, or use day-to-day.

**Secondary:** Anyone needing a quick demo of a full-stack app with real moving parts (create, redirect, track).

## 3. v1 Scope — IN

- Create a short link from a long URL (custom slug or auto-generated)
- Redirect visitors to the original URL on slug visit
- Track click count, displayed inline after creation
- Manual stats refresh button on the result

## 4. v1 Scope — OUT

- User accounts or authentication
- Link expiry or deletion
- QR codes
- Analytics beyond raw click count (referrer, geo, device)
- Bulk creation or API keys
- Dashboard or link management UI

---

## 5. Key Flows

### Flow 1 — Create a short link

1. User pastes a URL into the input field (long URL).
2. User optionally enters a custom slug.
3. User submits.
4. Backend validates, stores, returns the short URL + initial click count (0).
5. Frontend displays the result inline. Inputs are cleared to invite the next link.

### Flow 2 — Redirect

1. Visitor hits `/{slug}`.
2. Backend looks up slug in SQLite.
3. If found: increment click count, return **302** redirect to original URL.
4. If not found: return user-facing HTML 404 error page (not raw JSON).

### Flow 3 — Stats

1. After creation, the result panel shows the short URL and current click count.
2. A **manual refresh button** lets the user re-fetch the count on demand. No polling.

---

## 6. Technical Approach

**Stack:** FastAPI + SQLite + Vanilla JS. No build step, no bundler.

**Static serving:** `FileResponse` from `Path(__file__).parent/static`. No `StaticFiles` mount.

**Database connection:** `contextmanager` wraps each SQLite connection — commit on success, rollback + close on exception.

---

## 7. Acceptance Criteria

### URL Validation

- **AC-V1:** Accept only `http://` and `https://` schemes. Reject `javascript:`, `data:`, `file://`, and any other scheme with HTTP 422.
- **AC-V2:** If input has no scheme (e.g. `google.com`), auto-prefix `https://` and store the normalised form. Show the user the stored URL.
- **AC-V3:** If input already has `http://` or `https://`, do **not** prepend again. `https://example.com` → `https://example.com`, not `https://https://example.com`.
- **AC-V4:** Empty URL submission returns HTTP 422 with a clear error message.

### Slug — Auto-generated

- **AC-S1:** Auto-slug is 6 characters, base62 (`[a-zA-Z0-9]`).
- **AC-S2:** On collision, generate up to 5 candidates. If all 5 collide, return HTTP 503.

### Slug — Custom

- **AC-S3:** Custom slugs are normalised to lowercase on creation. `MyLink` and `mylink` are the same slug.
- **AC-S4:** Valid pattern: `^[a-z0-9]([a-z0-9-]*[a-z0-9])?$` — alphanumeric plus internal hyphens only. Single-character slugs are allowed.
- **AC-S5:** Leading or trailing hyphens are rejected with HTTP 422.
- **AC-S6:** Length: 3–50 characters (post-normalisation).
- **AC-S7:** Duplicate custom slug returns HTTP 409.
- **AC-S8:** Reserved paths are rejected: `/api`, `/stats`, `/docs`, `/redoc`, `/openapi.json`, `/favicon.ico`, `/health`.

### Redirect

- **AC-R1:** `GET /{slug}` on a valid slug returns HTTP **302** (not 301 — browser caching of 301 breaks the click counter).
- **AC-R2:** Click count increments on every hit, including bot/script visits.
- **AC-R3:** `GET /{slug}` on an unknown slug returns a user-facing HTML 404 page (not `{"detail": "Not found"}`).

### Stats

- **AC-T1:** Click count is displayed inline on the creation result — no separate `/stats` page needed.
- **AC-T2:** A manual refresh button re-fetches and updates the displayed count.
- **AC-T3:** No automatic polling.

---

## 8. Open Items — Needs Human Input

- **Success metrics:** What does success look like in numbers? (e.g. links created per session, p99 redirect latency)
- **Monetisation / pricing:** Not applicable for v1, but flagged for future.
- **Launch timeline:** [NEEDS HUMAN INPUT]
- **Top business risks:** [NEEDS HUMAN INPUT]
