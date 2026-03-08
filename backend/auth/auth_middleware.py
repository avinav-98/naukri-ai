from fastapi.responses import RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware

from backend.auth.jwt_handler import decode_token
from backend.models.user_model import get_user_by_id


PUBLIC_EXACT_PATHS = {"/", "/signup", "/signin", "/signin-google", "/openapi.json", "/forgot-password"}
PUBLIC_PREFIX_PATHS = ("/static", "/docs", "/reset-password")


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        path = request.url.path

        if path in PUBLIC_EXACT_PATHS or path.startswith(PUBLIC_PREFIX_PATHS):
            return await call_next(request)

        token = request.cookies.get("session")
        if not token:
            return RedirectResponse("/")

        payload = decode_token(token)
        if not payload:
            return RedirectResponse("/")

        user_id = payload["user_id"]
        row = get_user_by_id(user_id)
        if not row:
            return RedirectResponse("/")
        role = (row[4] or payload.get("role") or "user").strip().lower()
        account_status = (row[5] or "active").strip().lower()
        if account_status != "active":
            response = RedirectResponse("/")
            response.delete_cookie("session")
            return response

        if path.startswith("/admin"):
            if role not in {"admin", "co_admin"}:
                return RedirectResponse("/dashboard")
        if path.startswith("/api/admin"):
            if role not in {"admin", "co_admin"}:
                return RedirectResponse("/dashboard")

        request.state.user_id = user_id
        request.state.role = role
        return await call_next(request)
