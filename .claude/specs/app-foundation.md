# Software Specification Document (Implementation Addendum)

**Project:** Vulnerable Web Application — Security Lab
**Document type:** Implementation-level behavioral specification
**Derived from:** `docs/PRD.md` and `docs/TDD.md`
**Status:** Draft v1.1 — baseline for the `newfeature/foundation` branch (reconciled against TDD)
**Last Updated:** 2026-10-25

---

## 1. Scope

This document captures **only implementation-level behavior** required to reproduce the
application exactly: runtime behavior, user flows, form mechanics, visual design,
validation, session semantics, and edge-case handling.

It **intentionally omits** material already documented elsewhere, specifically:

- Product goals, target audience, value propositions, success metrics (PRD)
- Architecture, module layout, and technology stack choices (PRD/TDD)
- Vulnerability descriptions, exploit vectors, and severity data (PRD)
- Database schema definitions (TDD)
- Endpoint inventories, HTTP method tables, and route handlers (TDD)
- Technology stack, module layout, and package configuration (TDD)

Where a route name is needed to make a behavior unambiguous, this addendum refers to it
only by its documented purpose (e.g., "the dashboard page"); nothing in this document
should be read as redefining those artifacts.

---

## 2. Runtime Behavior

| ID | Behavior |
| --- | --- |
| RB-01 | **Automatic database initialization on startup.** When the application boots, the database file and its table structure are created automatically if they do not exist. No manual migration step is required. |
| RB-02 | **Missing DB files recreated automatically.** If the database file is deleted while the application is stopped (or even between requests), the next startup/operation recreates it. The application never crashes at boot due to a missing database file. |
| RB-03 | **Data preserved across restarts.** Registered users and their data survive process restarts, because persistence is a file on disk that is reopened, not rebuilt, on boot. Recreating the file only occurs when it is absent. |
| RB-04 | **Static assets available after boot.** CSS files, images, and other static resources are served directly from the static directory and are reachable as soon as the server is listening — no build or compile step gates them. |
| RB-05 | **Templates loaded from disk at request time, no caching.** HTML templates are read from the filesystem on every request. Editing a template file changes the next response immediately; no restart or reload is needed. |
| RB-06 | **Dashboard content modified via runtime string substitution before response.** The dashboard body is produced by taking the template's rendered content and performing a plain string replacement — the literal `{{username}}` placeholder → the logged-in username — in memory before sending the response. |
| RB-07 | **Authentication state based solely on session presence.** A request is "authenticated" if and only if the session contains the user identity values. There is no token revalidation against the database, no expiry logic, and no secondary check on any route. |
| RB-08 | **Application root redirects to signup.** A visit to the application root does not render content; it redirects the visitor to the signup page. |

---

## 3. User Flows

### 3.1 Registration

1. User opens the signup page — new visitors arrive there via the root redirect
   (RB-08) — and sees the four-field form (§6.1).
2. **Client-side validation runs before submission:** the browser/JS checks that
   password and confirm-password match; if they do not, an inline red message appears
   below the confirm field and the form is not submitted.
3. User submits the form (standard form submission, not fetch).
4. Server creates the user record (password stored in its persisted hashed form) and
   commits it.
5. Server responds with a **redirect to the login page**. No session is created; the
   user is not logged in by registering.

### 3.2 Login

1. User opens the login page and sees the two-field form (§6.2).
2. Form submission is intercepted client-side; credentials are sent via an
   **asynchronous `fetch` request** — the page itself does not reload or navigate.
3. Response is processed dynamically in JavaScript:
   - **Success:** the server has established a session and answers with the dashboard
     redirect; the async handler follows it, landing the browser on the dashboard
     page.
   - **Failure:** JS renders the returned error message into the designated error
     area of the form; the user stays on the page and may retry.
4. A session is established only on success and is carried by a session cookie.

### 3.3 Dashboard

1. User requests the dashboard page.
2. Server checks the session for the `user_id` value. If it is absent → redirect to
   the login page (see AP-03).
3. If present: the dashboard template is loaded from disk (§RB-05).
4. The username placeholder in the rendered content is replaced at runtime with the
   session's username (§RB-06).
5. The substituted HTML is returned as the response.

### 3.4 Logout

1. User activates the logout control on the dashboard (link/button to the logout route).
2. Server clears the session (all stored values destroyed).
3. Server responds with a **redirect to the login page**.
4. Any subsequent request to a protected page finds no session and is redirected to
   login; protected resources are inaccessible until re-authentication.

---

## 4. Functional Requirements

| ID | Requirement |
| --- | --- |
| **FR-01** | **Session Management.** The application must establish a server-side-signed session on successful login, store `user_id`, `username`, and `email` in it, expose it via a cookie, and destroy it entirely on logout. |
| **FR-02** | **Dynamic User Context.** The dashboard must display the username of the currently authenticated user, injected into the page content at request time via string substitution. |
| **FR-03** | **Route Protection.** Dashboard requests must verify that `user_id` is present in the session; an unauthenticated request must be redirected to the login page rather than receiving the protected content. The dashboard is the **only** authenticated-only content — login, signup, search, and static resources are served with no session requirement. |
| **FR-04** | **Error Handling.** Failed login must surface a human-readable error message in the form's error area without a page reload. Registration validation failures must surface inline before submission. Unauthenticated access must redirect (not error). |
| **FR-05** | **Search Processing.** The search feature must accept a `q` query parameter, match it against both username and email, and return an HTML response that echoes the query and renders each match as a list item showing the username with the user's email in parentheses. |
| **FR-06** | **Persistence.** User records must be written durably so they survive application restarts and can authenticate later. |

---

## 5. Complete Visual Design Specification

This section is normative: a faithful rebuild must reproduce these values and layouts.

### 5.1 Global Design System

**Font stack (applied globally):**

```
"Segoe UI", system-ui, -apple-system, sans-serif
```

**Typography scale:**

| Role | Size | Weight |
| --- | --- | --- |
| Main titles (hero headings) | 2rem | 800 |
| Section titles | 1.4rem | 700 |
| Form titles | 1.7rem | 700 |
| Card titles | 0.95rem | 700 |
| Body text | 0.9rem | 400 |
| Labels | 0.82rem | 600 |
| Buttons | 1rem | 600 |

**Primary colors:**

| Hex | Role |
| --- | --- |
| `#1a237e` | Primary brand indigo (buttons, hero gradient start, step-card background) |
| `#3949ab` | Primary light (focus border, gradient end/accent) |
| `#283593` | Gradient deepening tone (login/signup panel end stop) |
| `#0f172a` | Darkest tone (gradient start stop) |
| `#eef1f8` | Application background (dashboard body) |
| `#ffffff` | Surface color (panels, cards, header) |

**Text colors:**

| Hex | Use |
| --- | --- |
| `#1e293b` | Primary text (headings, body on light surfaces) |
| `#475569` | Secondary text (descriptions, subtitles) |
| `#64748b` | Muted text (hints, metadata) |
| `#c5cae9` | Light indigo text on dark blue surfaces; also input default border |
| `#1a237e` | Accent/link text (signup link, emphasis) |

**Border radius:**

| Element | Radius |
| --- | --- |
| Inputs | 8px |
| Buttons | 8px |
| Cards | 10–12px |
| Status/pill tags | 6px |

**Shadows:**

| Element | Shadow |
| --- | --- |
| Header | `0 2px 10px rgba(26, 35, 126, 0.08)` |
| Card hover | `0 4px 16px rgba(26, 35, 126, 0.10)` |
| Input focus glow | `0 0 0 3px rgba(57, 73, 171, 0.12)` |

### 5.2 Shared Header (all pages)

- Position: **fixed** at top of viewport.
- Height: **70px**.
- Background: **white (`#ffffff`)**.
- Bottom border: thin light line (1px, light indigo family).
- Shadow: header shadow from §5.1 (subtle).
- **Left:** application title text.
- **Right:** **three organizational logos, each 54×54px**, in a horizontal row
  (PUCIT, Excaliat, FCCU).
- Page content must be offset so it is not hidden beneath the fixed header.

### 5.3 Login Page

**Layout:** two-column **50/50 split-screen**, full viewport height.

**Left panel (branding):**

- Background: deep blue diagonal gradient with stops
  `#0d1b5e → #1a237e → #283593`.
- Contents, vertically arranged:
  - A small **badge label** (pill-shaped tag, e.g., lab identifier).
  - **Welcome heading** (main-title scale).
  - **Description paragraph** (light text).
  - A **bullet list** of what the lab offers.
- Decorative overlays: **semi-transparent white circles** (~**7% opacity**), oversized
  and partially off-panel (corner bleed), at least one upper and one lower.

**Right panel (form):**

- Background: **white**.
- Centered form container, **max-width 400px**, containing, in order:
  1. **Form title** (form-title scale, primary text color `#1e293b`).
  2. **Subtitle** (muted `#475569`).
  3. **Username field** — label + input.
  4. **Password field** — label + input.
  5. **Error message area** — empty until a failed login populates it.
  6. **Login button** — full width, background `#1a237e`, white text, 8px radius.
  7. **Signup link** — `#1a237e` accent text leading to the registration page.

**Input styling (all forms):**

- Background `#f8f9ff`; border `1.5px solid #c5cae9`; radius 8px.
- **On focus:** border becomes `#3949ab` and the blue glow shadow (§5.1) appears.

**Error message styling:**

- Light red background, red border, dark red text; rounded; shown inside the form flow.

### 5.4 Signup Page

- **Structure is identical to the login page:** same split-screen, same gradient panel,
  same decorative circles, same white right panel with a max-400px form and the same
  input/error styling.
- Form fields, in order:
  1. **Username**
  2. **Email**
  3. **Password**
  4. **Confirm Password**
  5. **Submit (create account) button** — same full-width indigo button.
- **Password mismatch:** a red message appears **directly below the confirm field**,
  shown client-side **without a page reload**.
- **Duplicate username:** caught server-side; the response is a full HTML error page
  stating the username exists — a different mechanism from the client-side mismatch
  message, which never reaches the server.
- Includes a link back to the login page (accent style, mirroring the signup link).

### 5.5 Dashboard Page

- **Body background:** `#eef1f8`.
- **Hero banner** directly beneath the header:
  - Background: horizontal gradient `#1a237e → #3949ab`.
  - **Left:** main title (2rem/800, white) + subtitle (light text).
  - **Right:** the **logged-in username** — rendered by substituting the literal
    `{{username}}` placeholder in the template content (RB-06) — and a
    **logout button** styled semi-transparent white (white text, translucent
    white background/border, radius 8px).
- **Content area:** max-width **1100px**, horizontally centered, below the hero.
  1. **Mission card:** white card (10–12px radius, light border, card shadow on hover)
     containing a section title and a description paragraph.
  2. **"Vulnerabilities to Discover" section:** introduced by an **uppercase, small,
     bold** header. Beneath it, a **two-column grid of 8 vulnerability cards**.
     - Each card: white, rounded, light border, hover shadow; contains a
       **colored pill tag** (6px radius) and a short description.
     - Tag colors (7 distinct hues across 8 cards — the two XSS cards share red):
       | Tag | Color | Reference value |
       | --- | --- | --- |
       | SQLi | yellow | `#fbc02d` |
       | XSS (stored, reflected) | red | `#e53935` |
       | Session | purple | `#8e24aa` |
       | Brute | orange | `#fb8c00` |
       | Crypto | green | `#43a047` |
       | Exposed | blue | `#1e88e5` |
       | CSRF | pink | `#d81b60` |
  3. **Process step cards:** a row of **three** cards, each with background `#1a237e`,
     white text, and a **circular numbered badge** (1, 2, 3) above the step title:
     **Find → Exploit → Mitigate**.

### 5.6 Responsive Behavior

- **Desktop:** login/signup use the side-by-side split-screen; dashboard uses the
  two-column vulnerability grid and horizontal step row.
- **Mobile / narrow viewports:**
  - Login/signup panels **stack vertically** (branding above form, or hidden compact).
  - Vulnerability grid collapses to **single column**.
  - Process step cards stack **vertically**.
  - Header **logos shrink** (scaled down from 54px) to keep the header usable.
- Behavior contract: no horizontal scrolling at small widths; every control remains
  reachable. Exact breakpoints are implementation choices; the stacking outcomes above
  are mandatory.

---

## 6. Form Specifications

### 6.1 Registration Form

| Input | Type | Notes |
| --- | --- | --- |
| Username | text | Required |
| Email | email | Required |
| Password | password | Required |
| Confirm Password | password | Required; **must match Password, checked client-side before submit** |

- Submission: normal form POST (not fetch).
- On success: redirect to login page.
- On server-side failure (username already taken): a full HTML response presenting the
  error; the message explicitly states that the username already exists.

### 6.2 Login Form

| Input | Type | Notes |
| --- | --- | --- |
| Username | text | Required |
| Password | password | Required |

- Submission intercepted client-side and sent via **asynchronous fetch**.
- Response processed dynamically: success → navigate to dashboard; failure → render
  error message in-page. **No full-page form post, no reload.**

---

## 7. Validation Rules

| Context | Rule |
| --- | --- |
| Registration | Username, email, password, and confirm-password are all required. |
| Registration | `password === confirm_password`, enforced **client-side** before submission. |
| Registration | Username uniqueness is enforced **at the database level** (constraint violation), not by a pre-check in application code. |
| Login | Username and password are required (empty values are refused/handled without authenticating). |
| Search | The `q` query parameter is required; absent/empty handling defined by EC-04/AP-04 behavior. |

---

## 8. Session State Model

**Stored values (after successful login):**

| Key | Content |
| --- | --- |
| `user_id` | Database primary key of the authenticated user |
| `username` | Username string (drives dashboard display) |
| `email` | Email string |

**Lifecycle:**

1. **Creation** — the three values are written into the session on successful
   authentication only.
2. **Usage** — read on every protected-route request to decide access and to supply
   the username for runtime substitution.
3. **Destruction** — logout clears the session completely; after destruction no
   protected content is served to that client until it re-authenticates.

No other state is kept server-side per user; no expiry or revalidation rules exist
(authentication state is *solely* presence-based — RB-07).

---

## 9. Data Lifecycle Rules

| Rule | Behavior |
| --- | --- |
| DL-01 | A user record is **created only** through the registration flow. |
| DL-02 | **No modification workflow exists** — users cannot edit username, email, or password after creation. |
| DL-03 | **No deletion workflow exists** — there is no account-deletion feature. |
| DL-04 | **No recovery workflow exists** — no password reset or email verification. |

The user table is append-only from the product's point of view.

---

## 10. Success Paths

| ID | Path |
| --- | --- |
| **SP-01** | **Registration:** valid form + matching passwords → record persisted → redirect to login page. |
| **SP-02** | **Login:** matching credentials → session created with `user_id`, `username`, `email` → fetch response consumed → browser redirected to dashboard. |
| **SP-03** | **Dashboard:** session present → template loaded → username substituted → HTML response renders hero with the logged-in username. |
| **SP-04** | **Logout:** session cleared → redirect to login → dashboard now unreachable for that session. |

---

## 11. Alternate Paths

| ID | Path |
| --- | --- |
| **AP-01** | **Duplicate username on registration:** the database uniqueness constraint rejects the insert; no user is created and the server returns an HTML error message explicitly stating that the username already exists. |
| **AP-02** | **Invalid credentials on login:** no session is created; the login response carries a failure result rendered in the page's error area — user remains on login. |
| **AP-03** | **Unauthorized dashboard access:** request without a valid session → redirect to login; protected content never rendered. |
| **AP-04** | **Empty search:** search invoked without a usable `q` value → handled per validation rule (§7); no crash. |

---

## 12. Edge Cases

| ID | Case | Required behavior |
| --- | --- | --- |
| **EC-01** | Existing username used at registration | DB constraint blocks duplicate; existing user untouched; new record not created. |
| **EC-02** | Empty registration data | Required-field handling stops submission; no record created. |
| **EC-03** | Empty login data | No authentication performed; error surfaced in page; no session created. |
| **EC-04** | Missing session on protected page | Redirect to login (AP-03). |
| **EC-05** | Corrupted/tampered session cookie | Session data is unreadable → treated as absent → redirect to login. No crash, no privilege granted. |
| **EC-06** | Missing template file | Request for a page whose template is absent fails cleanly (server error, process survives); the application does not enter a broken state for other routes. |
| **EC-07** | Missing database file | Recreated on next startup with empty structure (RB-02); all prior users are gone and must re-register. |
| **EC-08** | Application restart with existing DB | Users and data intact (RB-03); sessions issued before restart behave per session-storage semantics of the stack. |

---

## 13. Business Rules

| ID | Rule |
| --- | --- |
| **BR-01** | Authentication depends entirely on session presence — no request-time credential or token revalidation against the database. |
| **BR-02** | The dashboard cannot render its user context without **runtime string substitution of the literal `{{username}}` placeholder**; the username exists only in the response pipeline, not in stored template content. |
| **BR-03** | User records are **immutable after creation** (no edit/delete flows exist anywhere in the application). |
| **BR-04** | **Login and registration use different response formats:** login answers the async request with a redirect/JSON result the page processes dynamically without a document navigation; registration always completes as a full-page response — a redirect on success, an HTML error page on failure. |
| **BR-05** | **Template edits are visible without restart** because templates are loaded from disk per request. |
| **BR-06** | The **database uniqueness constraint is the primary (only) mechanism** for enforcing username uniqueness — the application layer performs no prior existence check. |

---

## 14. Rebuild Requirements

A compatible implementation must reproduce all of the following behaviors:

1. Create the database file and schema automatically at startup; recreate it if the
   file is missing; keep data across restarts (RB-01–RB-03). The database is a single
   file named `vulnerable_app.db` stored at the project root.
2. Serve static assets from disk immediately after boot (RB-04).
3. Load templates per request, uncached, with visible effect without restart
   (RB-05, BR-05).
4. Build the dashboard response via runtime substitution of the literal `{{username}}`
   placeholder (RB-06,
   FR-02, BR-02).
5. Base all authentication checks on session presence alone (RB-07, BR-01).
6. Registration: four inputs; client-side password-match check before submit; DB-level
   uniqueness; success redirects to login; never auto-login (Flow 3.1, §6.1, §7).
7. Login: two inputs; async fetch submission; dynamic success/failure handling without
   page reload; success creates session with `user_id`/`username`/`email` and navigates
   to the dashboard; failure shows in-page error (Flow 3.2, §6.2, FR-04).
8. Dashboard requires a session containing `user_id`; unauthenticated requests are
   redirected to login;
   logout clears the session fully, redirects to login, and locks protected content
   (Flows 3.3–3.4, FR-01, FR-03).
9. Search accepts a required `q` parameter, matches username and email, and returns
   HTML that echoes the query and renders each match as a "username (email)" list
   item (FR-05).
10. All visual artifacts of §5: design-system tokens, fixed 70px header with three
    54×54px logos, split-screen auth pages with gradient/circles, exact input/button/
    error styling, hero + card grid + step cards on the dashboard, and responsive
    stacking outcomes.
11. No update, delete, or recovery flows for users (DL-02–DL-04).
12. Clean failure for the edge cases in §12 (no crashes, no privilege leaks).
13. Application root redirects first-time visitors to the signup page (RB-08).
14. Duplicate-username registration responds with an HTML error page explicitly
    revealing that the username exists (AP-01); login, signup, and search are
    reachable with no session (FR-03).

---

## 15. Acceptance Criteria

| ID | Area | Criterion |
| --- | --- | --- |
| **AC-01** | Registration | A new user with valid, matching-password data is created and the browser lands on the login page; duplicate usernames fail without creating a record. |
| **AC-02** | Login | Correct credentials establish a session and land on the dashboard; wrong credentials show an in-page error with no reload; empty inputs cannot authenticate. |
| **AC-03** | Dashboard | Authenticated view displays the logged-in username sourced from the session; direct visits without a session redirect to login. |
| **AC-04** | Logout | After logout the session is gone, the user is on the login page, and requesting the dashboard again redirects to login. |
| **AC-05** | Search | A search with a `q` value returns an HTML page reflecting the query and any username/email matches; a request without usable `q` is handled without error. |
| **AC-06** | Persistence | After a full restart, a previously registered user can log in; if the DB file was deleted, the app still boots and accepts fresh registration. |

---

## 16. Test Cases

| ID | Scenario | Steps | Expected Result |
| --- | --- | --- | --- |
| TC-01 | Register valid user | Submit signup with matching passwords | User persisted; redirect to login |
| TC-02 | Password mismatch | Signup with `password ≠ confirm` | Inline red error under confirm field; no submission |
| TC-03 | Duplicate username | Register an existing username | Insert rejected by DB constraint; no duplicate record; HTML error states the username exists |
| TC-04 | Empty registration | Submit with required fields empty | Submission refused; nothing created |
| TC-05 | Login success | Fetch login with valid credentials | Session created; redirect to dashboard |
| TC-06 | Login invalid | Fetch login with wrong password | Error message rendered in page; no session; no reload |
| TC-07 | Login empty | Submit blank username/password | No authentication; error handling; no session |
| TC-08 | Login async contract | Inspect network during login submit | Fetch (async) request; page not reloaded by form POST |
| TC-09 | Dashboard renders username | Log in, open dashboard | Logged-in username visible in hero (substituted) |
| TC-10 | Dashboard unauthenticated | Open dashboard with no session | Redirected to login |
| TC-11 | Logout | Click logout on dashboard | Session cleared; on login page |
| TC-12 | Post-logout protection | After logout, request dashboard | Redirected to login again |
| TC-13 | Search with results | Search a known username/email substring | HTML lists matches as "username (email)" items; query echoed |
| TC-14 | Search without q | Invoke search with `q` absent | Handled per §7/AP-04 without crash |
| TC-15 | Persistence & recreation | Restart app; try TC-05 login. Delete DB file; restart; log in; register | User still authenticates after restart; after file deletion app boots, recreation occurs, old user gone, new registration works |

---

## 17. Documentation Gaps

Four discrepancies between the documents and implementation reality:

1. **Login success navigation ownership is ambiguous.** PRD describes a server-driven
   "successful authentication redirects to the dashboard," while TDD routes login
   through an AJAX `fetch` whose handler may answer with either a redirect or a JSON
   response — the documents never settle whether the server or the client script
   performs the final navigation.
2. **Duplicate-username error path is under-specified.** TDD states the signup error
   message reveals that a username already exists, but neither document describes how
   the database constraint violation is caught or rendered (the described insert path
   would simply raise); PRD's signup UX covers only client-side password mismatch.
3. **Entry-point inconsistency.** The application root redirects to signup, while
   PRD's user stories treat login as the primary entry; the returning-user journey
   after arriving at the app is not reconciled between the documents.
4. **Caching requirements do not line up.** PRD requires static assets to be "cached
   appropriately," yet no caching behavior for static files is specified anywhere,
   while templates are explicitly loaded from disk uncached on every request — the
   two asset paths have only one documented policy.

---

*End of Implementation Addendum.*
