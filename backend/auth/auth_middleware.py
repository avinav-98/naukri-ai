from fastapi.responses import JSONResponse, RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware

from backend.auth.jwt_handler import decode_token
from backend.models.user_model import get_user_by_id


PUBLIC_EXACT_PATHS = {
    "/",
    "/signup",
    "/signin",
    "/signin-google",
    "/openapi.json",
    "/forgot-password",
    "/logout",
    "/switch-user",
}
PUBLIC_PREFIX_PATHS = ("/assets", "/docs", "/reset-password")
PUBLIC_API_PREFIXES = (
    "/api/session/login",
    "/api/session/signup",
    "/api/session/forgot-password",
    "/api/session/reset-password",
)


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        path = request.url.path

        if path in PUBLIC_EXACT_PATHS or path.startswith(PUBLIC_PREFIX_PATHS):
            return await call_next(request)

        token = request.cookies.get("session")
        payload = decode_token(token) if token else None
        row = get_user_by_id(payload["user_id"]) if payload else None

        if row:
            role = (row[4] or payload.get("role") or "user").strip().lower()
            account_status = (row[5] or "active").strip().lower()
            if account_status != "active":
                response = JSONResponse(status_code=401, content={"status": "error", "error": "Account disabled"})
                response.delete_cookie("session")
                return response if path.startswith("/api") else RedirectResponse("/")
            request.state.user_id = payload["user_id"]
            request.state.role = role

        if path.startswith(PUBLIC_API_PREFIXES):
            return await call_next(request)

        if not path.startswith("/api"):
            return await call_next(request)

        if not token:
            return JSONResponse(status_code=401, content={"status": "error", "error": "Authentication required"})

        if not payload or not row:
            response = JSONResponse(status_code=401, content={"status": "error", "error": "Invalid session"})
            response.delete_cookie("session")
            return response

        if path.startswith("/admin"):
            if request.state.role not in {"admin", "co_admin"}:
                return JSONResponse(status_code=403, content={"status": "error", "error": "Forbidden"})
        if path.startswith("/api/admin"):
            if request.state.role not in {"admin", "co_admin"}:
                return JSONResponse(status_code=403, content={"status": "error", "error": "Forbidden"})
        return await call_next(request)
