"""Local password login, logout, and current-user endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from backend.api.models import LoginRequest
from backend.auth.models import UserContext
from backend.auth.session import (
    authenticate_user,
    create_session,
    get_current_user,
    revoke_session,
    session_token_from_request,
)
from backend.config import settings
from backend.db.connection import transaction


router = APIRouter(prefix="/api", tags=["auth"])


def _user_response(user: UserContext) -> dict[str, str]:
    return {
        "id": user.id,
        "username": user.username,
        "name": user.name,
        "email": user.email,
        "role": user.role,
        "department": user.department,
        "status": "active",
    }


@router.post("/auth/login")
def login(payload: LoginRequest, response: Response) -> dict[str, object]:
    try:
        with transaction() as connection:
            user = authenticate_user(connection, payload.username, payload.password)
            token = create_session(connection, user.id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": str(exc), "code": "INVALID_CREDENTIALS"},
        ) from exc

    response.set_cookie(
        key=settings.session_cookie_name,
        value=token,
        max_age=settings.session_ttl_hours * 3600,
        httponly=True,
        secure=settings.session_cookie_secure,
        samesite="lax",
        path="/",
    )
    return {"user": _user_response(user)}


@router.post("/auth/logout")
def logout(request: Request, response: Response) -> dict[str, str]:
    token = session_token_from_request(request)
    if token:
        with transaction() as connection:
            revoke_session(connection, token)
    response.delete_cookie(settings.session_cookie_name, path="/")
    return {"status": "ok"}


@router.get("/me")
def me(user: UserContext = Depends(get_current_user)) -> dict[str, str]:
    return _user_response(user)
