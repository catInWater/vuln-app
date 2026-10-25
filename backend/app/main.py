"""Application entry point.

Run either way (both must work):
    cd backend && python app/main.py
    uv run backend/app/main.py        # from the project root

The sys.path bootstrap at the top makes the `app` package importable
regardless of which directory the script is launched from.
"""

import os
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parents[1]  # backend/
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.api.routes.auth import router as auth_router
from app.db.session import init_db

# INTENTIONAL VULNERABILITY #4: Session Hijacking.
# Hardcoded, publicly-known weak secret key for session signing. Do NOT move
# this to an env var or a strong value — session forgery is a learning target.
SECRET_KEY = "super-secret-key-12345"

app = FastAPI(title="Vulnerable Web Application - Security Lab")

app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

app.include_router(auth_router)

project_root = Path(__file__).resolve().parents[2]
frontend_dir = project_root / "frontend"

# Static assets are served straight from disk (spec RB-04).
app.mount(
    "/static/css",
    StaticFiles(directory=frontend_dir / "static" / "css"),
    name="css",
)
app.mount(
    "/static/images",
    StaticFiles(directory=frontend_dir / "static" / "images"),
    name="images",
)

# Create the database file + users table on startup (spec RB-01/RB-02).
init_db()

if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "3001"))
    uvicorn.run(app, host="0.0.0.0", port=port)