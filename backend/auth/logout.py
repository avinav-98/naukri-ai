from fastapi import APIRouter
from fastapi.responses import RedirectResponse

router = APIRouter()

@router.get("/logout")
def logout():

    response = RedirectResponse(url="/")
    response.delete_cookie("session")

    return response