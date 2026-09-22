from fastapi import Header, HTTPException, Request

from .config import get_settings


def require_admin(x_admin_token: str | None = Header(default=None)):
    s = get_settings()
    if not s.require_auth:
        return True
    if not s.admin_token or x_admin_token != s.admin_token:
        raise HTTPException(status_code=401, detail="ADMIN_AUTH_REQUIRED")
    return True


def require_https(request: Request):
    s = get_settings()
    if s.environment == "production":
        proto = request.headers.get("x-forwarded-proto", request.url.scheme)
        if proto != "https":
            raise HTTPException(status_code=400, detail="HTTPS_REQUIRED")
    return True
