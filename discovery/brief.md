# PRD — URL Shortener v1 (50% Draft)

## 1. Problem

Sharing long URLs is ugly and untrackable. A URL shortener creates a compact, memorable alias and tells you how many times it was visited. This is a self-hosted, single-session demo: paste a URL, get a short link, watch the click counter increment.

## 2. Target Users

**Primary**: Developer / demo audience — someone running this locally or on a small server who wants to show a working, satisfying tool in one session.

**Secondary**: Anyone who needs a lightweight self-hosted shortener without SaaS dependencies.

## 3. v1 Scope (In)

- Create a short link from any HTTP/HTTPS URL (auto-slug or custom slug)
- Redirect `GET /{slug}` → original URL, counting each visit
- View click count for a link (inline on creation result + standalone stats page)
- Input validation with clear error messages

## 4. v1 Scope (Out)

- User accounts / authentication
- Link expiry / TTL
- Bulk creation
- QR codes
- Analytics beyond raw click count (no referrer, geo, device)
- Admin dashboard
- Rate limiting

## 5. Key Flows

### Flow 1: Create a short link
1. User pastes URL into input field, optionally enters a custom slug.
2. Frontend submits `POST /api/links` with `{ url, slug? }`.
3. Backend validates URL, generates or validates slug, stores in SQLite.
4. Frontend displays: short URL + copy button + initial click count (0).

### Flow 2: Redirect
1. Visitor hits `GET /{slug}`.
2. Backend looks up slug, increments click count, returns **302** to original URL.
3. Slug not found → user-facing HTML 404 page (not raw JSON).

### Flow 3: View stats
1. After creation, click count shown inline on the result card.
2. Manual refresh button re-fetches `GET /api/links/{slug}` and updates the count.
3. Direct URL `GET /{slug}/stats` shows the same info on a standalone page.

## 6. Technical Approach

**Stack**: FastAPI + SQLite + Vanilla JS (no build step)

**Database**: Single `links` table — `slug` (PK), `original_url`, `click_count`, `created_at`

**Redirect code**: **302** (not 301). 301 is cached permanently by browsers — the click counter stops incrementing after the first visit.

**Auto-slug**: 6-char base62. Generate up to 5 candidates, retry on collision. If all 5 collide, return HTTP 503: "Could not generate unique slug, please try again."

**Custom slug rules**:
- Allowed chars: alphanumeric + hyphens (`[a-z0-9-]`), normalized to lowercase on creation
- Length: 3–50 characters
- Leading or trailing hyphens rejected (`-abc` and `abc-` are invalid)
- Duplicate of existing slug → 409 Conflict
- Reserved and rejected at creation: `/api`, `/stats`, `/docs`, `/redoc`, `/openapi.json`, `/favicon.ico`, `/health`

**URL validation**:
- Accepted schemes: `http` and `https` only
- Reject `javascript:`, `data:`, `file://`, and any other scheme
- No-scheme input (e.g. `google.com`): auto-prefix `https://` and show the user what was stored
- Empty submission: reject with validation error

**Stats**: Manual refresh button. All hits (including bots/scripts) increment the counter.

**404**: User-facing HTML error page, not raw `{ "detail": "Not found" }`.

**Notable risks**:
- SQLite write contention under concurrent redirects — acceptable at demo scale
- No rate limiting on creation — fine for v1

---

## [NEEDS HUMAN INPUT]

- **Success metrics**: What does a successful v1 look like in numbers? (Latency targets, links created, uptime?)
- **Monetisation / pricing**: N/A for self-hosted demo — confirm?
- **Launch timeline & milestones**: Target date / session for the live demo?
- **Top business risks & mitigations**: Any constraints on deployment environment or audience?

---

*Draft PRD ~50% complete — pausing for human review. Please comment, redirect, or approve to continue.*
