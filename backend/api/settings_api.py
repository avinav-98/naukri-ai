from fastapi import APIRouter, Request
from backend.models.settings_model import get_settings, save_settings

router = APIRouter(prefix="/api")


@router.post("/settings")
def update_settings(data: dict, request: Request):
    user_id = request.state.user_id

    save_settings(data=data, user_id=user_id)

    return {"status":"saved"}


@router.get("/settings")
def read_settings(request: Request):
    user_id = request.state.user_id
    return get_settings(user_id=user_id)
