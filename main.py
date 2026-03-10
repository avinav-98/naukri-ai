from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from backend.auth.auth_middleware import AuthMiddleware
from backend.auth.google_signin import router as google_signin_router
from backend.auth.logout import router as logout_router
from backend.auth.password_reset import router as password_reset_router
from backend.auth.signin import router as signin_router
from backend.auth.signup import router as signup_router

from backend.api.dashboard_api import router as dashboard_router
from backend.api.jobs_api import router as jobs_router
from backend.api.settings_api import router as settings_router
from backend.api.activity_api import router as activity_router
from backend.api.admin_api import router as admin_api_router
from backend.api.automation_api import router as automation_router
from backend.api.ui_api import router as ui_router
from backend.models.settings_model import get_settings
from backend.models.ui_preferences_model import get_ui_preferences
from backend.models.user_model import get_user_by_id
from backend.services.automation_pipeline_service import has_user_resume


app = FastAPI(title="Naukri Auto Apply AI")

app.add_middleware(AuthMiddleware)

templates = Jinja2Templates(directory="frontend/templates")

app.mount("/static", StaticFiles(directory="frontend/static"), name="static")

# Register Routers
app.include_router(signin_router)
app.include_router(signup_router)
app.include_router(logout_router)
app.include_router(google_signin_router)
app.include_router(password_reset_router)

app.include_router(dashboard_router)
app.include_router(jobs_router)
app.include_router(settings_router)
app.include_router(activity_router)
app.include_router(admin_api_router)
app.include_router(automation_router)
app.include_router(ui_router)


def _ctx(request: Request, extra: dict | None = None):
    ctx = {"request": request}
    user_id = getattr(request.state, "user_id", None)
    if user_id:
        ctx["ui_prefs"] = get_ui_preferences(user_id=user_id)
        ctx["role"] = getattr(request.state, "role", "user")
        row = get_user_by_id(user_id)
        if row:
            ctx["current_user"] = {
                "id": row[0],
                "full_name": row[1] or "",
                "email": row[2] or "",
            }
        else:
            ctx["current_user"] = {"id": user_id, "full_name": "", "email": ""}
    else:
        ctx["ui_prefs"] = {"theme_mode": "system", "layout_mode": "standard", "accent_color": "#0b57d0"}
        ctx["role"] = "user"
        ctx["current_user"] = {"id": "", "full_name": "", "email": ""}
    if extra:
        ctx.update(extra)
    return ctx


# ------------------------
# AUTH PAGES
# ------------------------

@app.get("/", response_class=HTMLResponse)
def signin_page(request: Request):
    return templates.TemplateResponse("auth/signin.html", _ctx(request))


@app.get("/signin", response_class=HTMLResponse)
def signin_page_alias(request: Request):
    return templates.TemplateResponse("auth/signin.html", _ctx(request))


@app.get("/signup", response_class=HTMLResponse)
def signup_page(request: Request):
    return templates.TemplateResponse("auth/signup.html", _ctx(request))


# ------------------------
# DASHBOARD
# ------------------------

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard_page(request: Request):
    return templates.TemplateResponse("dashboard/dashboard.html", _ctx(request))


@app.get("/resume-analyzer", response_class=HTMLResponse)
def resume_analyzer_page(request: Request):
    return templates.TemplateResponse("dashboard/resume_analyzer.html", _ctx(request))


@app.get("/keywords", response_class=HTMLResponse)
def keywords_page(request: Request):
    return templates.TemplateResponse("dashboard/keywords.html", _ctx(request))


# ------------------------
# JOB PAGES
# ------------------------

@app.get("/fetch-jobs", response_class=HTMLResponse)
def fetch_jobs_page(request: Request):
    user_id = getattr(request.state, "user_id", None)
    settings = get_settings(user_id=user_id) if user_id else {}
    return templates.TemplateResponse("jobs/fetch_jobs.html", _ctx(request, {"settings": settings}))


@app.get("/jobs-directory", response_class=HTMLResponse)
def jobs_directory_page(request: Request):
    return templates.TemplateResponse("jobs/jobs_directory.html", _ctx(request))


@app.get("/relevant-jobs", response_class=HTMLResponse)
def relevant_jobs_page(request: Request):
    return templates.TemplateResponse("jobs/relevant_jobs.html", _ctx(request))


@app.get("/applied-jobs", response_class=HTMLResponse)
def applied_jobs_page(request: Request):
    return templates.TemplateResponse("jobs/applied_jobs.html", _ctx(request))


@app.get("/ext-jobs", response_class=HTMLResponse)
def ext_jobs_page(request: Request):
    return templates.TemplateResponse("jobs/ext_jobs.html", _ctx(request))


# ------------------------
# SETTINGS
# ------------------------

@app.get("/settings", response_class=HTMLResponse)
def settings_page(request: Request):
    user_id = getattr(request.state, "user_id", None)
    settings = get_settings(user_id=user_id) if user_id else {}
    settings["has_resume"] = has_user_resume(user_id) if user_id else False
    return templates.TemplateResponse("settings/control_panel.html", _ctx(request, {"settings": settings}))


# ------------------------
# PROFILE
# ------------------------

@app.get("/profile", response_class=HTMLResponse)
def profile_page(request: Request):
    return templates.TemplateResponse("profile/profile.html", _ctx(request))


@app.get("/forgot-password", response_class=HTMLResponse)
def forgot_password_page(request: Request):
    return templates.TemplateResponse("auth/forgot_password.html", _ctx(request))


@app.get("/reset-password/{token}", response_class=HTMLResponse)
def reset_password_page(token: str, request: Request):
    return templates.TemplateResponse("auth/reset_password.html", _ctx(request, {"reset_token": token}))


@app.get("/admin", response_class=HTMLResponse)
def admin_page(request: Request):
    return templates.TemplateResponse("admin/dashboard.html", _ctx(request))


@app.get("/admin/users", response_class=HTMLResponse)
def admin_users_page(request: Request):
    return templates.TemplateResponse("admin/users.html", _ctx(request))


@app.get("/admin/settings", response_class=HTMLResponse)
def admin_settings_page(request: Request):
    if getattr(request.state, "role", "user") != "admin":
        return templates.TemplateResponse("admin/forbidden.html", _ctx(request))
    return templates.TemplateResponse("admin/settings.html", _ctx(request))


@app.get("/admin/logs", response_class=HTMLResponse)
def admin_logs_page(request: Request):
    return templates.TemplateResponse("admin/logs.html", _ctx(request))
