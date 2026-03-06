from fastapi.responses import RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware

from backend.auth.jwt_handler import decode_token


PUBLIC_EXACT_PATHS = {"/", "/signup", "/signin", "/signin-google", "/openapi.json"}
PUBLIC_PREFIX_PATHS = ("/static", "/docs")


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

        request.state.user_id = payload["user_id"]
        return await call_next(request)
