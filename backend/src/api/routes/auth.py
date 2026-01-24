"""Login, register, refresh endpoints."""
from fastapi import APIRouter, HTTPException, Depends, Header
from typing import Optional
from pydantic import BaseModel, Field

from src.auth.models import LoginRequest, RefreshRequest, TokenResponse, UserCreate, UserResponse
from src.auth.service import login, refresh, register, get_user_by_id, update_user_password
from src.auth.jwt_handler import validate_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


def get_current_user_id(authorization: Optional[str] = Header(None)) -> Optional[str]:
    """Extract user ID from JWT token in Authorization header."""
    if not authorization:
        return None
    try:
        # Extract token from "Bearer <token>"
        token = authorization.replace("Bearer ", "").strip()
        payload = validate_access_token(token)
        if payload:
            return payload.get("sub")
    except Exception:
        pass
    return None


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=8, max_length=128, description="New password must be 8-128 characters")


@router.post("/register", response_model=UserResponse, status_code=201)
def register_endpoint(data: UserCreate):
    """Register a new user. Role is set to user."""
    try:
        return register(data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Log unexpected errors for debugging
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Registration error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")


@router.post("/login", response_model=TokenResponse)
def login_endpoint(body: LoginRequest):
    """Login with email and password. Returns access and refresh tokens."""
    try:
        user, access, ref, expires = login(body.email, body.password)
        return TokenResponse(access_token=access, refresh_token=ref, token_type="bearer", expires_in=expires)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.post("/refresh", response_model=TokenResponse)
def refresh_endpoint(body: RefreshRequest):
    """Exchange a valid refresh token for new access and refresh tokens."""
    try:
        access, new_refresh, expires = refresh(body.refresh_token)
        return TokenResponse(access_token=access, refresh_token=new_refresh, token_type="bearer", expires_in=expires)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.get("/me", response_model=UserResponse)
def get_current_user(user_id: Optional[str] = Depends(get_current_user_id)):
    """Get current user profile."""
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user = get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.post("/change-password")
def change_password(
    body: ChangePasswordRequest,
    user_id: Optional[str] = Depends(get_current_user_id),
):
    """Change user password."""
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        update_user_password(user_id, body.old_password, body.new_password)
        return {"status": "success", "message": "Password updated successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
