from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from backend.auth.auth_middleware import AuthMiddleware

from backend.api.session_api import router as session_router
from backend.api.dashboard_api import router as dashboard_router
from backend.api.jobs_api import router as jobs_router
from backend.api.settings_api import router as settings_router
from backend.api.activity_api import router as activity_router
from backend.api.admin_api import router as admin_api_router
from backend.api.automation_api import router as automation_router
from backend.database import initialize_database


initialize_database()
app = FastAPI(title="Naukri Auto Apply AI")

app.add_middleware(AuthMiddleware)
BASE_DIR = Path(__file__).resolve().parent
SPA_DIST_DIR = BASE_DIR / "frontend" / "dist"
SPA_ASSETS_DIR = SPA_DIST_DIR / "assets"

if SPA_ASSETS_DIR.exists():
    app.mount("/assets", StaticFiles(directory=str(SPA_ASSETS_DIR)), name="assets")

# Register Routers
app.include_router(session_router)
app.include_router(dashboard_router)
app.include_router(jobs_router)
app.include_router(settings_router)
app.include_router(activity_router)
app.include_router(admin_api_router)
app.include_router(automation_router)


def _spa_index_response():
    index_path = SPA_DIST_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return HTMLResponse(
        """
        <!doctype html>
        <html lang="en">
          <head>
            <meta charset="utf-8" />
            <meta name="viewport" content="width=device-width, initial-scale=1" />
            <title>Naukri Auto Apply AI</title>
          </head>
          <body>
            <main style="font-family: sans-serif; max-width: 720px; margin: 4rem auto; line-height: 1.5;">
              <h1>Frontend build not found</h1>
              <p>Build the React app before loading the UI.</p>
              <p>Expected output: <code>frontend/dist/index.html</code></p>
            </main>
          </body>
        </html>
        """.strip()
    )


@app.get("/", response_class=HTMLResponse)
def spa_root():
    return _spa_index_response()


@app.get("/{full_path:path}", response_class=HTMLResponse)
def spa_fallback(full_path: str):
    if full_path.startswith(("api/", "auth/")):
        return HTMLResponse("Not Found", status_code=404)
    return _spa_index_response()
