from fastapi import APIRouter
from fastapi.responses import RedirectResponse
from backend.models.admin_log_model import log_admin_event

router = APIRouter()

@router.get("/logout")
def logout():

    response = RedirectResponse(url="/")
    response.delete_cookie("session")
    log_admin_event("user_logout", "Session ended")

    return response


@router.get("/switch-user")
def switch_user():

    response = RedirectResponse(url="/signin")
    response.delete_cookie("session")
    log_admin_event("user_switch", "Switched account session")

    return response
