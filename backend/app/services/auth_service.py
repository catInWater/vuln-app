"""Authentication business logic.

INTENTIONAL VULNERABILITY #1: SQL Injection.
Every SQL query below is built by raw string concatenation of user input
instead of a parameterized query. This lets payloads such as
`' OR '1'='1' --` in the username bypass the password check, or a
crafted username break out of the INSERT on signup. Do NOT switch these to
parameterized queries / ORM — the injection is the lab's primary learning
target (see docs/TDD.md section 3.1.3).
"""

import sqlite3

from fastapi import Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

from app.core.security import hash_password
from app.db.session import get_db


def signup(username: str, email: str, password: str):
    """Register a new user. Success: redirect to /login.

    All fields are required (presence-only validation). On duplicate username
    the UNIQUE constraint raises IntegrityError, which is caught and surfaced
    as a visible "Username already exists" message — this also intentionally
    leaks that a given username is in use.
    """
    if not username or not email or not password:
        return HTMLResponse("All fields (username, email, password) are required.")

    hashed = hash_password(password)

    query = (
        "INSERT INTO users (username, email, password) VALUES ('"
        + username
        + "', '"
        + email
        + "', '"
        + hashed
        + "')"
    )

    try:
        conn = get_db()
        try:
            conn.execute(query)
            conn.commit()
        finally:
            conn.close()
    except sqlite3.IntegrityError:
        return HTMLResponse("Username already exists")

    return RedirectResponse(url="/login", status_code=302)


def login(request: Request, username: str, password: str):
    """Authenticate a user. Always answers with JSON (fetch-consumed).

    The row lookup is built from raw string concatenation, so an SQL payload
    in the username field can authenticate without valid credentials. On
    success the session carries user_id / username / email and the response
    tells the frontend JS where to navigate (it performs the redirect via
    window.location.href). On failure a 401 JSON body lets the page show the
    error inline without reloading.
    """
    if not username or not password:
        return JSONResponse(
            {"success": False, "error": "Username and password are required"},
            status_code=400,
        )

    hashed = hash_password(password)

    query = (
        "SELECT * FROM users WHERE username = '"
        + username
        + "' AND password = '"
        + hashed
        + "'"
    )

    conn = get_db()
    try:
        row = conn.execute(query).fetchone()
    finally:
        conn.close()

    if row is None:
        return JSONResponse(
            {"success": False, "error": "Invalid credentials"},
            status_code=401,
        )

    request.session["user_id"] = row["id"]
    request.session["username"] = row["username"]
    request.session["email"] = row["email"]

    return JSONResponse({"success": True, "redirect": "/welcome"})