# Vulnerable App — Security Lab

An **intentionally vulnerable** web application for hands-on security
education (OWASP Top 10 training). Built with FastAPI + SQLite.

> **⚠️ Educational use only.** This app contains deliberate security flaws.
> Never deploy it anywhere beyond an isolated, authorized training
> environment. Do not use it against systems you do not own or lack explicit
> permission to test.

## Development Commands

```bash
cd backend
uv sync                     # install dependencies into .venv
python app/main.py          # run from backend/
# or from the project root:
uv run backend/app/main.py
```

- Server runs on `http://localhost:3001` (override with the `PORT` env var).
- Reset the lab: delete `vulnerable_app.db` at the project root and restart —
  the app recreates the file and table automatically.
- Templates read from disk per request: edit and refresh, no restart needed.

## Architecture Overview

Three layers (see `docs/TDD.md` §2 for the full design):

- **Presentation** — `frontend/templates/` (login, signup, dashboard) +
  `frontend/static/` (css + logos), served via `main.py` static mounts.
- **Application** — `backend/app/api/routes/auth.py` (HTTP handlers) →
  `backend/app/services/auth_service.py` (business logic).
- **Data** — `backend/app/db/session.py` (SQLite, `vulnerable_app.db`).

## Vulnerability Map — DELIBERATE, do not "fix"

| # | Vulnerability | Location | Mechanism |
| --- | --- | --- | --- |
| 1 | SQL Injection | `auth_service.py` (`signup`, `login`), `auth.py` (`/search`) | Raw string-concatenated SQL, no parameterization |
| 2 | Stored XSS | `auth.py` `/welcome` | Username substituted into HTML unescaped |
| 3 | Reflected XSS | `auth.py` `/search` | `q` parameter interpolated into HTML unescaped |
| 4 | Session Hijacking | `main.py` | Hardcoded `SECRET_KEY = "super-secret-key-12345"` |
| 5 | Weak Password Storage | `core/security.py` | Unsalted MD5 hashing |
| 6 | Exposed Database | `auth.py` `/download/db` | No auth check on the file download |
| 7 | No Rate Limiting | (global) | No throttling on any endpoint |
| 8 | CSRF | (all forms) | No tokens on any POST form |

**Hard rule for contributors and reviewers:** code reviews, "cleanups," or
dependency upgrades must NOT parameterize SQL, escape output, salt hashes,
strengthen the secret key, protect `/download/db`, or add rate
limiting / CSRF defenses. Each of those removes a learning target.

## Frontend–Backend Integration

- **Login** (`frontend/templates/login.html`): the form never submits
  natively — JS `fetch()` POSTs `FormData`, the server answers JSON, and JS
  either navigates to `data.redirect` on success or renders `data.error`
  inline.
- **Signup**: native `POST /signup`; client-side JS blocks submit on password
  mismatch; success redirects to `/login`; duplicate usernames get an HTML
  "Username already exists" page.
- **Dashboard**: `dashboard.html` contains the literal token `{{username}}`;
  the server replaces it (string substitution) before responding. Renaming
  the token on either side silently breaks the display.
- **Sessions**: `SessionMiddleware` cookie carries `user_id`, `username`,
  `email`; access control is presence-of-`user_id` only.

## Specification Hierarchy

1. `docs/PRD.md` — product requirements
2. `docs/TDD.md` — technical design
3. `.claude/specs/app-foundation.md` — implementation-behavior addendum
   (normative for runtime behavior and visual design)
4. `.claude/specs/app-foundation-plan.md` — phase-by-phase build plan

When documents conflict, the spec and plan govern the implementation.