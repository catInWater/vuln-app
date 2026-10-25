"""HTTP route handlers.

INTENTIONAL VULNERABILITIES in this module (do NOT fix any of them):
  - VULN-1: /search builds its SQL by string concatenation.
  - VULN-3: /search interpolates the `q` parameter into the HTML response
    without escaping (reflected XSS).
  - VULN-2: /welcome substitutes the session username into the dashboard
    HTML without escaping, so a malicious stored username fires stored XSS.
  - VULN-6: /download/db serves the SQLite file with no authentication check.
  - VULN-7: no rate limiting anywhere in this module.
  - VULN-8: no CSRF token validation on any POST handler.
Templates are read from disk on every request (no caching) so edits show up
on refresh without a restart.
"""

import sqlite3
from pathlib import Path

from fastapi import APIRouter, Form, Request
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse

from app.db.session import DB_PATH, get_db
from app.services import auth_service

router = APIRouter()

# Project root is four levels above app/api/routes/ (backend/app/api/routes/)
PROJECT_ROOT = Path(__file__).resolve().parents[4]
TEMPLATES_DIR = PROJECT_ROOT / "frontend" / "templates"
STATIC_DIR = PROJECT_ROOT / "frontend" / "static"


def read_template(name: str) -> HTMLResponse:
    """Read a template from disk per request (no caching, see spec RB-05)."""
    with open(TEMPLATES_DIR / name, "r", encoding="utf-8") as f:
        return HTMLResponse(f.read())


@router.get("/")
def index():
    """Entry point: send new visitors straight to the signup page."""
    return RedirectResponse(url="/signup", status_code=302)


@router.get("/signup")
def signup_page():
    return read_template("signup.html")


@router.post("/signup")
def signup_post(
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
):
    """Standard form POST; redirects to /login on success."""
    return auth_service.signup(username, email, password)


@router.get("/login")
def login_page():
    return read_template("login.html")


@router.post("/login")
def login_post(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
):
    """Consumed by the login page's fetch() call; always answers JSON."""
    return auth_service.login(request, username, password)


@router.get("/download/db")
def download_db():
    """INTENTIONAL: no authentication — anyone can pull the database file."""
    return FileResponse(
        DB_PATH,
        media_type="application/octet-stream",
        filename="vulnerable_app.db",
    )


@router.get("/search")
def search_user(q: str):
    """INTENTIONAL: `q` is concatenated into SQL (VULN-1) and interpolated
    into the response HTML unescaped (VULN-3, reflected XSS). Exceptions
    surface str(e) — intentional information leakage."""
    try:
        conn = get_db()
        try:
            query = (
                "SELECT username, email FROM users WHERE username LIKE '%"
                + q
                + "%' OR email LIKE '%"
                + q
                + "%'"
            )
            rows = conn.execute(query).fetchall()
        finally:
            conn.close()
    except Exception as e:
        return HTMLResponse("<h2>Search Error</h2><p>" + str(e) + "</p>")

    results = "".join("<li>" + str(row[0]) + " (" + str(row[1]) + ")</li>" for row in rows)
    html = (
        "<!DOCTYPE html><html lang='en'><head>"
        "<meta charset='utf-8'>"
        "<title>Search Results</title>"
        "<link rel='stylesheet' href='/static/css/styles.css'>"
        "</head><body>"
        "<div class='search-page'>"
        "<h2>Search Results for: &quot;" + q + "&quot;</h2>"
        "<ul class='search-results'>" + results + "</ul>"
        "<p><a href='/login'>Back to login</a></p>"
        "</div>"
        "</body></html>"
    )
    return HTMLResponse(html)


@router.get("/welcome")
def welcome_page(request: Request):
    """Protected dashboard. Requires 'user_id' in the session; otherwise the
    user is redirected to /login. The username is injected by replacing the
    literal {{username}} token before responding (spec RB-06)."""
    if "user_id" not in request.session:
        return RedirectResponse(url="/login", status_code=302)

    with open(TEMPLATES_DIR / "dashboard.html", "r", encoding="utf-8") as f:
        html = f.read()

    html = html.replace("{{username}}", request.session["username"])
    return HTMLResponse(html)


@router.get("/logout")
def logout(request: Request):
    """Clear the session and return to the login page."""
    request.session.clear()
    return RedirectResponse(url="/login", status_code=302)