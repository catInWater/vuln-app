# Software Implementation Plan — App Foundation

**Project:** Vulnerable Web Application — Security Lab
**Document type:** Step-by-step implementation plan (planning artifact only)
**Sources:** `docs/PRD.md` · `docs/TDD.md` · `.claude/specs/app-foundation.md` (spec v1.1)
**Branch:** `newfeature/foundation`
**Status:** Draft v1.0 — 2026-10-25

---

## 0. How to Use This Plan

This document describes **how to build** the application foundation in 10 ordered
phases. Each phase lists the exact files to create/modify and the key implementation
decisions. Phases are sequential: Phase N depends on Phases 1..N−1.

> **VULNERABILITY POLICY — READ FIRST.** This is an intentionally insecure
> educational application (DVWA/Juice Shop class). All eight vulnerabilities listed
> below are **deliberate, required features**, not mistakes to avoid:
>
> 1. **SQL Injection** — login and signup via **raw string concatenation**
> 2. **Stored XSS** — unescaped username on the dashboard
> 3. **Reflected XSS** — unescaped query parameter in search
> 4. **Session Hijacking** — hardcoded weak secret key
> 5. **Weak Password Storage** — MD5 without salt
> 6. **Exposed Database** — unauthenticated `/download/db`
> 7. **No Rate Limiting** — on any endpoint
> 8. **CSRF** — no token validation on any form
>
> Implementation must therefore use string concatenation for **every** SQL query in
> `auth_service.py` and `auth.py`. Parameterized queries, input escaping, salting,
> rate limiting, and CSRF tokens are **prohibited** in this foundation — they would
> remove the lab's learning targets. Never deploy this application beyond an
> isolated educational environment.

**Vulnerability placement map** (which phase lands which flaw):

| # | Vulnerability | Where introduced | Phase |
| --- | --- | --- | --- |
| 1 | SQL Injection | `auth_service.py` (login + signup), `auth.py` (search) | 4, 5 |
| 2 | Stored XSS | `auth.py:welco­me` → `html.replace('{{username}}', …)` | 5, 7 |
| 3 | Reflected XSS | `auth.py` search: raw `q` interpolated into HTML | 5 |
| 4 | Session Hijacking | `main.py`: `SECRET_KEY = "super-secret-key-12345"` | 6 |
| 5 | Weak Password Storage | `core/security.py`: unsalted MD5 | 3 |
| 6 | Exposed Database | `auth.py`: `/download/db` with no auth check | 5 |
| 7 | No Rate Limiting | Absence by design — add no throttling anywhere | all |
| 8 | CSRF | Absence by design — no tokens on any form | 5, 7 |

**Spec traceability:** RB = runtime behavior, FR = functional req, AP = alternate
path, TC = test case, all from `app-foundation.md`. Section refs like §5 point to
that spec (normative source for all visual values).

---

## Phase 1: Project Structure

**Goal:** create the two-package layout (backend Python app + frontend assets) with
all Python module skeletons in place, importable but not yet functional.

**Files to create:**

```
backend/
├── pyproject.toml
└── app/
    ├── __init__.py                  # empty
    ├── main.py                      # placeholder (Phase 6)
    ├── core/
    │   ├── __init__.py              # empty
    │   └── security.py              # placeholder (Phase 3)
    ├── db/
    │   ├── __init__.py              # empty
    │   └── session.py               # placeholder (Phase 2)
    ├── services/
    │   ├── __init__.py              # empty
    │   └── auth_service.py          # placeholder (Phase 4)
    └── api/
        ├── __init__.py              # empty
        └── routes/
            ├── __init__.py          # empty
            └── auth.py              # placeholder (Phase 5)

frontend/
├── templates/                       # empty dir now; login/signup/dashboard.html in Phase 7
└── static/
    ├── css/                         # empty dir now; styles.css in Phase 8
    └── images/                      # logo files already present — do not touch
```

**`backend/pyproject.toml` key details:**

- Build system: **hatchling** (`[build-system] requires = ["hatchling"]`).
- `[project]` — name (e.g. `vuln-app-backend`), version `0.1.0`,
  `requires-python = ">=3.9"`.
- Dependencies (versions per PRD §10.1 / TDD §2.2):
  - `fastapi>=0.109.0`
  - `uvicorn>=0.27.0`
  - `python-multipart>=0.0.6` (Form parsing — required for POST /signup, /login)
  - `itsdangerous>=2.0.0` (session signing, pulled in for SessionMiddleware)
- Optional dev dependency group `dev = ["pytest"]`.
- Hatch wheel target must point at the package: `[tool.hatch.build.targets.wheel]
  packages = ["app"]` so `uv sync` builds/installs without layout surprises.

**Steps:**

1. Create the `backend/app/{core,db,services,api/routes}` tree; add an empty
   `__init__.py` in every package directory (all are namespace-less regular
   packages).
2. Create `backend/pyproject.toml` as specified.
3. Create the empty `frontend/templates/`, `frontend/static/css/`,
   `frontend/static/images/` directories (images/ must retain the three existing
   logo files: `PUCIT_Logo.png`, `blue-logo-scl2.png`, `excaliat-logo.png`).
4. Add placeholder stub files for the modules listed above (real content comes in
   Phases 2–6).
5. Verify `uv sync` resolves from `backend/` and the `app` package imports.

**Do NOT** create `vulnerable_app.db` manually — it is generated at first startup
(RB-01/RB-02).

---

## Phase 2: Database Layer

**File:** `backend/app/db/session.py`

**Key implementation details:**

- Database file: **`vulnerable_app.db` at the project root** (two levels above
  `session.py` — resolve with `Path(__file__).resolve().parents[3] / "vulnerable_app.db"`
  or an equivalent root-relative constant; document the choice in a comment).
- `get_db() -> sqlite3.Connection`:
  - `sqlite3.connect(DB_PATH, check_same_thread=False)` — allows the connection to
    be shared across the app's threads (simplifies the educational code; required
    per TDD §3.1.4).
  - Set `conn.row_factory = sqlite3.Row` so results support both index and
    name access (TDD uses `row[0]`/`row[1]` style access in search output).
  - No connection pooling — open/close per operation is the intended pattern.
- `init_db() -> None`:
  - Executes exactly:

    ```sql
    CREATE TABLE IF NOT EXISTS users (
        id       INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        email    TEXT,
        password TEXT
    );
    ```

  - `CREATE TABLE IF NOT EXISTS` + file auto-creation by `sqlite3.connect` gives
    RB-01 (auto-init at startup) and RB-02 (missing file recreated) **for free** —
    no extra logic needed.
- The `users` columns `username, email, password` are the only data the app
  writes; `UNIQUE` on `username` is the sole uniqueness enforcement (BR-06, §7).

**Checkpoint:** calling `init_db()` twice from a clean state creates the file +
table and is idempotent; deleting the file and re-running recreates it (pre-test
of EC-07).

---

## Phase 3: Security Utilities

**File:** `backend/app/core/security.py`

**Key implementation details (Vulnerability #5 — INTENTIONAL):**

- `import hashlib` only — no bcrypt/argon2/passlib, no `os.urandom`, no salt.
- Two functions:

  ```python
  def hash_password(password: str) -> str:
      return hashlib.md5(password.encode()).hexdigest()

  def verify_password(plain: str, hashed: str) -> bool:
      return hashlib.md5(plain.encode()).hexdigest() == hashed
  ```

- Unsalted MD5 hexdigest — this is the learning target (rainbow-table reversible).
  Add a comment marking it as **intentionally vulnerable**, but the weakness must
  not be fixed.
- Note: `login()` in Phase 4 does **not** call `verify_password` — it hashes the
  input and compares inside SQL (that's how VULN-1 stays exploitable). Keep
  `verify_password` present per TDD's function table; it documents the secure-ish
  comparison path students can contrast against.

**Checkpoint:** `hash_password("admin")` returns the known MD5 hexdigest
`21232f297a57a5a743894a0e4a801fc3`; no salt parameter exists anywhere.

---

## Phase 4: Business Logic — `auth_service.py`

**File:** `backend/app/services/auth_service.py`

**Imports:** `fastapi.responses` (`RedirectResponse`, `JSONResponse`, `HTMLResponse`),
`fastapi.Request`, `hashlib` indirectly via `hash_password`, `get_db`.

### 4.1 `signup(username, email, password)` (Vulnerability #1 — INTENTIONAL)

Steps:

1. Receive values as `Form` parameters (the route in Phase 5 declares them; the
   service takes plain strings).
2. Validate all fields are present/non-null (per TDD §3.1.3 this is the **only**
   validation — no length, charset, or escaping checks; keep it that way).
3. `hashed = hash_password(password)`.
4. Build the INSERT **by raw string concatenation** — never `?` placeholders:

   ```python
   query = ("INSERT INTO users (username, email, password) VALUES ('"
            + username + "', '" + email + "', '" + hashed + "')")
   ```

5. Execute + `conn.commit()`.
6. Success → `RedirectResponse(url="/login", status_code=302)` (SP-01).
7. Wrap the execute in `except sqlite3.IntegrityError:` (the UNIQUE constraint on
   `username` raises this) → return
   `HTMLResponse` containing a visible **"Username already exists"** message.
   This resolves spec gap §17.2 — the constraint violation is caught and surfaced,
   matching AP-01/TC-03 — and it **explicitly reveals username existence**
   (intentional information leakage per TDD §3.1.3).
8. Because `username` reaches both the DB and later the dashboard unsanitized,
   stored XSS (Vulnerability #2) is *enabled here* and *triggered in* Phase 5's
   `/welcome`.

### 4.2 `login(request, username, password)` (Vulnerability #1 — INTENTIONAL)

Steps:

1. `Form` parameters, same minimal presence-only validation.
2. `hashed = hash_password(password)`.
3. Build the SELECT **by raw string concatenation** (the auth-bypass surface):

   ```python
   query = ("SELECT * FROM users WHERE username = '" + username
            + "' AND password = '" + hashed + "'")
   row = conn.execute(query).fetchone()
   ```

   A payload like `' OR '1'='1' --` in `username` must be able to return a row —
   that is the point; do not neutralize it.
4. **On match (row is not None):**
   - `request.session["user_id"] = row["id"]`
   - `request.session["username"] = row["username"]`
   - `request.session["email"] = row["email"]`
   - Return `JSONResponse({"success": True, "redirect": "/welcome"})`.
     The **client JS performs the navigation** (Phase 7) — this fixes the
     navigation-ownership ambiguity (spec §17.1): server never 302s the fetch.
5. **On no match:**
   - Return `JSONResponse({"success": False, "error": "Invalid credentials"},
     status_code=401)`. JS reads `data.error` and shows it inline (AP-02, FR-04).
6. No throttling, no lockout, no CSRF check anywhere in this module
   (Vulnerabilities #7, #8 by design).

**Checkpoint:** unit-style manual test — `login(request, "admin' OR '1'='1' --",
"whatever")` authenticates whenever **any** user row exists (SQLi works);
`signup` twice with the same username returns "Username already exists".

---

## Phase 5: Route Handlers — `auth.py`

**File:** `backend/app/api/routes/auth.py` — all nine routes on **one**
`APIRouter()`.

Template paths: resolve `frontend/templates/…` relative to project root (same
root-resolution pattern as Phase 2's DB path). **Read templates with plain
`open(...).read()` on every request** — no `JinjaTemplates`, no lru_cache, no
`StaticFiles` for templates (RB-05: edits visible without restart).

| Method | Path | Handler behavior |
| --- | --- | --- |
| GET | `/` | `RedirectResponse("/signup", status_code=302)` — entry redirect (RB-08). |
| GET | `/signup` | Read `frontend/templates/signup.html`; return `HTMLResponse`. |
| POST | `/signup` | `username/email/password: str = Form(...)` → delegate to `auth_service.signup(...)`; return its response. (No `confirm_password` server-side — confirmation is client-only, §6.1/§7.) |
| GET | `/login` | Read `login.html`; return `HTMLResponse`. |
| POST | `/login` | `request: Request`, `username: str = Form(...)`, `password: str = Form(...)` → `auth_service.login(request, username, password)`; return its JSON response. |
| GET | `/download/db` | **Vulnerability #6 — INTENTIONAL.** `FileResponse(vulnerable_app.db path, media_type="application/octet-stream")` with **no session check at all**. Anyone can download the DB. |
| GET | `/search` | `q: str` query param (required → missing gives FastAPI 422, satisfying §7/AP-04). Build `SELECT * FROM users WHERE username LIKE '%' + q + '%' OR email LIKE '%' + q + '%'` by **string concatenation** (also VULN-1 surface). Construct the HTML body as an f-string that **interpolates `q` directly, unescaped** (**Vulnerability #3 — INTENTIONAL**, reflected XSS) and renders each row as `<li>{row[0]} ({row[1]})</li>` (username, email) — matching FR-05/TC-13's "username (email)" contract. Wrap the DB call in `except Exception as e:` and return the error **including `str(e)`** in the page (information leakage, intentional). Return `HTMLResponse`. |
| GET | `/welcome` | **Protected.** `if "user_id" not in request.session: return RedirectResponse("/login", 302)` (FR-03, AP-03, EC-04). Otherwise read `dashboard.html`, do `html = html.replace("{{username}}", request.session["username"])` (**Vulnerability #2 delivery — INTENTIONAL**: stored XSS fires because the session username is substituted raw, with no escaping; RB-06/BR-02), return `HTMLResponse`. |
| GET | `/logout` | `request.session.clear()`; `RedirectResponse("/login", 302)` (SP-04). |

Notes:

- Only `/welcome` checks the session; `/`, `/signup`, `/login`, `/search`,
  `/download/db`, `/logout` are open (FR-03, §14.14).
- No CSRF tokens on any POST; no rate limiting on any route (VULN-7/8 by absence —
  verify nothing added later introduces them by accident).
- The `q` concatenation must survive as written; `q` is a plain string param, and
  SQLite errors on crafted input should reach the page via `str(e)`.

---

## Phase 6: Application Entry Point — `main.py`

**File:** `backend/app/main.py`

Steps, in order within the file:

1. **Path bootstrap before app imports** (top of file):

   ```python
   import sys
   from pathlib import Path
   BASE_DIR = Path(__file__).resolve().parent.parent   # backend/
   if str(BASE_DIR) not in sys.path:
       sys.path.insert(0, str(BASE_DIR))
   ```

   This makes the `app` package resolvable regardless of launch directory
   (`uv run backend/app/main.py` from project root **or** `python app/main.py`
   from `backend/`). All `from app.…` imports come **after** this block.

2. Imports: `FastAPI`, `SessionMiddleware` (from `starlette.middleware.sessions`),
   `os`, router from `app.api.routes.auth`, `init_db` from `app.db.session`.
3. **Vulnerability #4 — INTENTIONAL:**

   ```python
   SECRET_KEY = "super-secret-key-12345"
   ```

   Hardcoded module-level weak secret; fed to
   `app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)`. Signed,
   client-held cookie sessions; no expiry/rotation settings beyond defaults
   (RB-07 presence-only model). No `https_only`/`samesite` hardening — CSRF
   (#8) requires the cookie remain attachable to cross-site posts.
4. `app = FastAPI(title="Vulnerable Web Application - Security Lab")`.
5. `app.include_router(auth_router)`.
6. Static mounts (RB-04):
   - `app.mount("/static/css", StaticFiles(directory=frontend/static/css), name="css")`
   - `app.mount("/static/images", StaticFiles(directory=frontend/static/images), name="images")`
   - Paths resolved against the project root (same helper pattern as Phase 2/5).
7. `init_db()` at **module level** — runs on import, before serving (RB-01).
8. `if __name__ == "__main__":` → `uvicorn.run(app, host="0.0.0.0",
   port=int(os.getenv("PORT", "3001")))`.

**Checkpoint:** from a clean checkout (no DB file), `python app/main.py` boots,
creates `vulnerable_app.db`, and serves the root redirect on :3001.

---

## Phase 7: Frontend Templates

**Files:** `frontend/templates/login.html`, `signup.html`, `dashboard.html`.

**Shared header (all three files — plain duplicated markup, no templating):**
fixed bar, app title left, three `<img>` logos right (54×54) referencing
`/static/images/PUCIT_Logo.png`, `/static/images/blue-logo-scl2.png`,
`/static/images/excaliat-logo.png`; link `styles.css` from `/static/css/`.

### 7.1 `login.html` — split-screen + AJAX (spec §5.3)

- Left panel: gradient branding — badge label, welcome heading, description,
  bullet list; decorative semi-transparent white circles (~7% opacity).
- Right panel: max-400px form — title, subtitle, `username` input, `password`
  input, an empty `<div id="error-message">` area, full-width login button,
  signup link to `/signup`.
- **Form must not submit natively.** JS: `form.addEventListener('submit', …)` →
  `e.preventDefault()` → `fetch('/login', { method: 'POST', body: new FormData(form) })`
  → `const data = await res.json()`:
  - `data.success` → `window.location.href = data.redirect` (the `/welcome`
    navigation is **client-side**, per spec §17.1 resolution and Phase 4.2).
  - else → render `data.error` into the error area with the red error styling;
    **no page reload** (FR-04, TC-06/TC-08).
- Cookie handling: same-origin fetch sends the session cookie automatically —
  do **not** set `credentials: 'omit'` (would break SP-02).

### 7.2 `signup.html` — same layout, native POST + client validation (spec §5.4)

- Identical split-screen shell and styling.
- **Standard HTML form:** `<form action="/signup" method="POST">` — native submit,
  no fetch (contrast with login; BR-04's two response formats depend on this).
- Fields: `username`, `email` (`type="email"`), `password`, `confirm_password`
  (name it `confirm_password` or omit server-side — server ignores it; **do not**
  send an unexpected fourth Form param the route doesn't accept… actually
  FastAPI ignores extra form fields, so it is safe to include).
- Client JS on submit: compare `password` vs `confirm_password`; on mismatch,
  `e.preventDefault()` and show an inline red `<span>` **below the confirm
  field** — without a page reload (EC from §6.1, TC-02). Match → let the native
  POST proceed.
- Duplicate-username feedback arrives as the server's full HTML error page
  (Phase 4.1/AP-01) — different mechanism from the client-side mismatch span.

### 7.3 `dashboard.html` — protected page (spec §5.5)

- Body background `#eef1f8`.
- Hero banner under the header, gradient `#1a237e → #3949ab`:
  - Left: main title (e.g. "Security Vulnerability Lab") + subtitle.
  - Right: `Logged in as {{username}}` — the **literal token** `{{username}}`
    that the server replaces (RB-06). Keep the token exactly; a typo silently
    breaks substitution.
  - Logout button: semi-transparent white, links to `/logout` (GET link is fine —
    no CSRF defense exists or should).
- Content area max-width 1100px, centered:
  1. White mission card (section title + description).
  2. Uppercase small-bold "VULNERABILITIES TO DISCOVER" header; two-column grid
     of **8 vulnerability cards**, each = colored pill tag + short description;
     tag hues per spec §5.5 table (SQLi yellow, XSS red ×2, Session purple,
     Brute orange, Crypto green, Exposed blue, CSRF pink).
  3. Three process step cards (`#1a237e` background, circular numbered badges,
     white text): **1 Find · 2 Exploit · 3 Mitigate**.
- No JS needed on this page beyond native link clicks.

**Checkpoint:** the three templates load as HTML files with no server state; the
only dynamic artifact is the `{{username}}` token consumed in Phase 5.

---

## Phase 8: Styling — `styles.css`

**File:** `frontend/static/css/styles.css`

**Normative source:** spec `app-foundation.md` §5 (Complete Visual Design
Specification). Implement **all** of §5.1–§5.6; the plan lists the structure, the
spec lists the exact values:

1. **Design-system layer** — CSS custom properties for the palette
   (`#1a237e #3949ab #283593 #0f172a #eef1f8 #ffffff`; text `#1e293b #475569
   #64748b #c5cae9`), the font stack `"Segoe UI", system-ui, -apple-system,
   sans-serif`, the typography scale table (2rem/800 … 0.82rem/600), radii
   (inputs 8px, buttons 8px, cards 10–12px, tags 6px), and the three shadow
   definitions (header / card-hover / focus-glow).
2. **Header** — fixed, 70px, white, bottom border + shadow; logo row 54×54;
   `padding-top: 70px` (or equivalent) offset on `body`.
3. **Auth split-screen** — CSS Grid `1fr 1fr`, `min-height: 100vh`; left panel
   gradient `#0d1b5e → #1a237e → #283593`; absolutely positioned decorative
   circles at `rgba(255,255,255,0.07)`; right panel white, form column
   `max-width: 400px` centered.
4. **Forms** — inputs `#f8f9ff` bg, `1.5px solid #c5cae9`, 8px radius;
   `:focus` → border `#3949ab` + glow `0 0 0 3px rgba(57,73,171,0.12)`;
   full-width primary button `#1a237e`/white; error area light-red bg / red
   border / dark-red text; mismatch span and inline error classes.
5. **Dashboard** — body `#eef1f8`; hero gradient with left/right flex sections;
   translucent white logout button; 1100px centered content; white cards with
   hover shadow; two-column vulnerability grid; the seven pill-tag color
   classes; three step cards (`#1a237e`, numbered circular badges).
6. **Responsive (`@media (max-width: 768px)` — breakpoint is implementer's
   choice; outcomes are mandatory per §5.6):** auth panels stack vertically;
   vulnerability grid → single column; step cards → vertical column; logos
   shrink; no horizontal scroll.

**Checkpoints:** every page renders without layout errors; card hover shadow,
input focus glow, and mobile stacking match spec §5.

---

## Phase 9: CLAUDE.md

**File:** `CLAUDE.md` at project root. Sections to include:

1. **Project context** — intentionally vulnerable FastAPI/SQLite security-education
   lab; OWASP Top 10 teaching tool; never deploy externally; use only on systems
   you own/authorize (mirror PRD §6.2 warnings).
2. **Development commands** — `cd backend && uv sync`; run via `python app/main.py`
   from `backend/` or `uv run app/main.py` from root; server on `:3001`
   (`PORT` env var overrides); DB reset = delete `vulnerable_app.db` + restart.
3. **Architecture overview** — three layers (templates / routes+services / SQLite
   session layer) with the file map from TDD §2.1.
4. **Vulnerability map** — table of all 8 vulnerabilities, their file locations,
   and the warning that they are **deliberate**: any code review, "cleanup," or
   dependency upgrade must NOT parameterize SQL, escape output, salt hashes,
   strengthen the secret, protect `/download/db`, or add rate limiting/CSRF.
5. **Frontend–backend integration** — login is fetch→JSON→`window.location.href`;
   signup is native POST→redirect/HTML-error; dashboard username arrives via the
   literal `{{username}}` string replace (renaming the token on one side breaks
   the other); templates are read per request (edit-and-refresh works).
6. **Security education context** — point to `docs/PRD.md`, `docs/TDD.md`,
   `docs/EXPLOITS.md` (when it exists), and the safety guidelines.
7. **Specification hierarchy** — PRD (product) → TDD (technical design) →
   `.claude/specs/app-foundation.md` (implementation addendum, normative for
   behavior/visuals) → `.claude/specs/app-foundation-plan.md` (this plan).
   When documents conflict, the spec + this plan govern implementation.

---

## Phase 10: Testing and Validation

Manual end-to-end verification against the spec's acceptance criteria and test
cases. Start with a clean state (no `vulnerable_app.db`).

**Functional sequence:**

1. **Boot:** `python app/main.py` from `backend/` → app listens on `:3001`;
   `vulnerable_app.db` appears at project root with `users` table (RB-01/02,
   AC-06). Visiting `/` lands on `/signup` (RB-08).
2. **Pages load:** `/signup`, `/login` render the split-screen layout with
   header, gradient panel, circles, logos; `/static/css/styles.css` and logo
   images return 200 (RB-04).
3. **Registration (TC-01, AC-01):** create `alice` — mismatched confirms are
   blocked client-side with the inline span (TC-02); valid submit → user in DB
   (password column shows an unsalted MD5 hexdigest, confirming VULN-5) →
   redirect to `/login`.
4. **Duplicate username (TC-03, AP-01):** re-register `alice` → "Username already
   exists" HTML response; no second row.
5. **Login success (TC-05, TC-08, AC-02):** correct credentials → network tab
   shows an async `fetch` POST (not a form navigation), JSON consumed, browser
   lands on `/welcome` (SP-02).
6. **Dashboard (TC-09, AC-03):** hero shows "Logged in as alice" — the
   `{{username}}` token was substituted; 8 vulnerability cards + 3 step cards
   visible (SP-03).
7. **Session protection (TC-10, AP-03, AC-03):** open `/welcome` in a fresh
   private window → 302 to `/login`; no protected content in the response body.
8. **Invalid login (TC-06, AP-02, AC-02):** wrong password → inline error,
   no reload, still on `/login`, no session cookie set.
9. **Empty submissions (TC-04, TC-07, EC-02/03):** blanks refused client-side or
   by `Form(...)` validation; nothing authenticates or inserts.
10. **Logout (TC-11, TC-12, AC-04):** logout → back on `/login`; immediate
    `/welcome` attempt redirects again; session cookie yields no identity (SP-04).
11. **Search (TC-13/TC-14, AC-05):** `/search?q=ali` → HTML page echoing the
    query with `<li>alice (alice@…)</li>` row; `/search` without `q` → 422
    handled, no crash.
12. **Exposed DB (VULN-6, §10 step):** unauthenticated `curl http://localhost:3001/download/db`
    → downloads the SQLite file readable by `sqlite3`.
13. **Restart persistence (TC-15, AC-06, EC-07/08):** restart → `alice` can log
    in again (RB-03). Delete the DB file → restart → app still boots, file and
    table recreate, `alice` is gone, fresh signup works (RB-02, EC-07).
14. **Template hot-edit (RB-05, BR-05):** edit a heading in `login.html`, refresh
    the browser — change visible with no restart.
15. **Vulnerability presence (must PASS as "vulnerable" — do not fix):**
    - SQLi: username `admin' OR '1'='1' --` + any password logs in (VULN-1).
    - Stored XSS: register username `<img src=x onerror=alert('XSS')>`, log in,
      dashboard fires the handler (VULN-2).
    - Reflected XSS: `/search?q=<img src=x onerror=alert('XSS')>` executes
      (VULN-3).
    - Weak session: copy the `session` cookie to another browser → dashboard
      access without credentials (VULN-4).
    - No rate limiting / no CSRF token present on any form (VULN-7/8 by absence).

**Exit criteria:** all 15 steps behave as written, and none of the eight
vulnerabilities has been "helpfully" mitigated. Deviations that *reduce*
exploitability are defects in this lab.

---

## Appendix A — Phase → Spec Traceability

| Phase | Spec IDs satisfied |
| --- | --- |
| 1 | TDD §6.5/§11.2 structure, PRD §4.4 (pyproject) |
| 2 | RB-01, RB-02, RB-03, EC-07, §14.1 |
| 3 | VULN-5 placement, §14 (persistence form) |
| 4 | FR-01, FR-04, SP-01/02, AP-01/02, BR-04, BR-06, §17.2 resolution |
| 5 | RB-06, RB-07, RB-08, FR-02, FR-03, FR-05, AP-03/04, EC-04/05/06 |
| 6 | RB-04, RB-05 (uncached static), VULN-4 placement |
| 7 | Flows §3.1–3.4, §5.3–5.5 behavior, TC-01–TC-12 |
| 8 | All of spec §5 (normative visual values) |
| 9 | Documentation policy; guards against accidental remediation |
| 10 | AC-01–AC-06, TC-01–TC-15, §14 rebuild checklist |

## Appendix B — Standing Prohibitions for Implementers

When building, **do not**: use `?`-placeholder SQL in `auth_service.py`/`auth.py`;
HTML-escape search or username output; add salt/bcrypt/argon2; move the secret key
to an env var default that is strong; require auth for `/download/db`; add
throttling/lockout middleware; add CSRF tokens or `SameSite` hardening; swap the
per-request `open()` template reads for a cached template engine; or turn the login
JSON contract into a server-side 302. Each of these would silently delete a
learning target.

---

*End of Implementation Plan.*
