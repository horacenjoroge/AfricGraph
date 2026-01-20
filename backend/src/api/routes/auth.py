"""Login, register, refresh endpoints."""
from fastapi import APIRouter, HTTPException

from src.auth.models import LoginRequest, RefreshRequest, TokenResponse, UserCreate, UserResponse
from src.auth.service import login, refresh, register

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=201)
def register_endpoint(data: UserCreate):
    """Register a new user. Role is set to user."""
    try:
        return register(data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


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
