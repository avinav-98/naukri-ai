from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from backend.auth.auth_middleware import AuthMiddleware
from backend.auth.google_signin import router as google_signin_router
from backend.auth.logout import router as logout_router
from backend.auth.signin import router as signin_router
from backend.auth.signup import router as signup_router

from backend.api.dashboard_api import router as dashboard_router
from backend.api.jobs_api import router as jobs_router
from backend.api.settings_api import router as settings_router
from backend.api.activity_api import router as activity_router
from backend.api.automation_api import router as automation_router
from backend.api.ui_api import router as ui_router
from backend.models.settings_model import get_settings
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

app.include_router(dashboard_router)
app.include_router(jobs_router)
app.include_router(settings_router)
app.include_router(activity_router)
app.include_router(automation_router)
app.include_router(ui_router)


# ------------------------
# AUTH PAGES
# ------------------------

@app.get("/", response_class=HTMLResponse)
def signin_page(request: Request):
    return templates.TemplateResponse(
        "auth/signin.html",
        {"request": request}
    )


@app.get("/signin", response_class=HTMLResponse)
def signin_page_alias(request: Request):
    return templates.TemplateResponse(
        "auth/signin.html",
        {"request": request}
    )


@app.get("/signup", response_class=HTMLResponse)
def signup_page(request: Request):
    return templates.TemplateResponse(
        "auth/signup.html",
        {"request": request}
    )


# ------------------------
# DASHBOARD
# ------------------------

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard_page(request: Request):
    return templates.TemplateResponse(
        "dashboard/dashboard.html",
        {"request": request}
    )


@app.get("/resume-analyzer", response_class=HTMLResponse)
def resume_analyzer_page(request: Request):
    return templates.TemplateResponse(
        "dashboard/resume_analyzer.html",
        {"request": request}
    )


@app.get("/keywords", response_class=HTMLResponse)
def keywords_page(request: Request):
    return templates.TemplateResponse(
        "dashboard/keywords.html",
        {"request": request}
    )


# ------------------------
# JOB PAGES
# ------------------------

@app.get("/fetch-jobs", response_class=HTMLResponse)
def fetch_jobs_page(request: Request):
    user_id = getattr(request.state, "user_id", None)
    settings = get_settings(user_id=user_id) if user_id else {}
    return templates.TemplateResponse(
        "jobs/fetch_jobs.html",
        {"request": request, "settings": settings}
    )


@app.get("/jobs-directory", response_class=HTMLResponse)
def jobs_directory_page(request: Request):
    return templates.TemplateResponse(
        "jobs/jobs_directory.html",
        {"request": request}
    )


@app.get("/relevant-jobs", response_class=HTMLResponse)
def relevant_jobs_page(request: Request):
    return templates.TemplateResponse(
        "jobs/relevant_jobs.html",
        {"request": request}
    )


@app.get("/applied-jobs", response_class=HTMLResponse)
def applied_jobs_page(request: Request):
    return templates.TemplateResponse(
        "jobs/applied_jobs.html",
        {"request": request}
    )


@app.get("/ext-jobs", response_class=HTMLResponse)
def ext_jobs_page(request: Request):
    return templates.TemplateResponse(
        "jobs/ext_jobs.html",
        {"request": request}
    )


# ------------------------
# SETTINGS
# ------------------------

@app.get("/settings", response_class=HTMLResponse)
def settings_page(request: Request):
    user_id = getattr(request.state, "user_id", None)
    settings = get_settings(user_id=user_id) if user_id else {}
    settings["has_resume"] = has_user_resume(user_id) if user_id else False
    return templates.TemplateResponse(
        "settings/control_panel.html",
        {"request": request, "settings": settings}
    )


# ------------------------
# PROFILE
# ------------------------

@app.get("/profile", response_class=HTMLResponse)
def profile_page(request: Request):
    return templates.TemplateResponse(
        "profile/profile.html",
        {"request": request}
    )
