"""Authentication service: register, login, refresh, user table setup."""
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import text

from src.infrastructure.database.postgres_client import postgres_client
from src.infrastructure.logging import get_logger

from .jwt_handler import (
    create_access_token,
    create_refresh_token,
    validate_refresh_token,
)
from .models import Role, UserCreate, UserResponse
from .password import hash_password, verify_password

logger = get_logger(__name__)

USERS_TABLE = "users"


def ensure_users_table() -> None:
    """Create users table if it does not exist (matches 001_create_users.sql)."""
    sql = f"""
    CREATE TABLE IF NOT EXISTS {USERS_TABLE} (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        email VARCHAR(255) NOT NULL,
        password_hash VARCHAR(255) NOT NULL,
        role VARCHAR(50) NOT NULL DEFAULT 'user',
        is_active BOOLEAN NOT NULL DEFAULT true,
        created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email ON {USERS_TABLE}(email);
    """
    with postgres_client.get_session() as s:
        for stmt in (x.strip() for x in sql.split(";") if x.strip()):
            s.execute(text(stmt))
        # Context manager will commit automatically


def get_user_by_email(email: str) -> Optional[dict]:
    with postgres_client.get_session() as s:
        r = s.execute(
            text(f"SELECT id, email, password_hash, role, is_active, created_at FROM {USERS_TABLE} WHERE email = :email"),
            {"email": email.lower()},
        )
        row = r.fetchone()
    if not row:
        return None
    return {
        "id": str(row[0]),
        "email": row[1],
        "password_hash": row[2],
        "role": row[3],
        "is_active": row[4],
        "created_at": row[5],
    }


def register(data: UserCreate) -> UserResponse:
    email = data.email.lower()
    
    # Validate password BEFORE database operations
    try:
        password_hash = hash_password(data.password)
    except ValueError as e:
        # Re-raise ValueError with our custom message
        raise
    except Exception as e:
        # Catch any other password hashing errors
        raise ValueError(f"Password validation failed: {str(e)}")
    
    with postgres_client.get_session() as s:
        r = s.execute(
            text(f"SELECT 1 FROM {USERS_TABLE} WHERE email = :email"),
            {"email": email},
        )
        if r.fetchone():
            raise ValueError("Email already registered")
        r = s.execute(
            text(f"""
            INSERT INTO {USERS_TABLE} (email, password_hash, role, is_active, updated_at)
            VALUES (:email, :password_hash, :role, :is_active, :updated_at)
            RETURNING id, email, role, is_active, created_at
            """),
            {
                "email": email,
                "password_hash": password_hash,
                "role": Role.USER.value,
                "is_active": True,
                "updated_at": datetime.now(timezone.utc),
            },
        )
        row = r.fetchone()
        if not row:
            raise ValueError("Failed to create user - no data returned")
    return UserResponse(id=str(row[0]), email=row[1], role=row[2], is_active=row[3], created_at=row[4])


def login(email: str, password: str) -> tuple[UserResponse, str, str, int]:
    user = get_user_by_email(email)
    if not user:
        raise ValueError("Invalid email or password")
    if not user["is_active"]:
        raise ValueError("Account is disabled")
    if not verify_password(password, user["password_hash"]):
        raise ValueError("Invalid email or password")
    access, expires_in = create_access_token(str(user["id"]), user["role"])
    refresh = create_refresh_token(str(user["id"]))
    u = UserResponse(id=user["id"], email=user["email"], role=user["role"], is_active=user["is_active"], created_at=user["created_at"])
    return u, access, refresh, expires_in


def refresh(refresh_token: str) -> tuple[str, str, int]:
    sub = validate_refresh_token(refresh_token)
    if not sub:
        raise ValueError("Invalid or expired refresh token")
    with postgres_client.get_session() as s:
        r = s.execute(text(f"SELECT id, role FROM {USERS_TABLE} WHERE id = :id"), {"id": sub})
        row = r.fetchone()
    if not row:
        raise ValueError("User not found")
    access, expires_in = create_access_token(str(row[0]), row[1])
    new_refresh = create_refresh_token(str(row[0]))
    return access, new_refresh, expires_in


def get_user_by_id(user_id: str) -> Optional[UserResponse]:
    """Get user by ID."""
    with postgres_client.get_session() as s:
        r = s.execute(
            text(f"SELECT id, email, role, is_active, created_at FROM {USERS_TABLE} WHERE id = :id"),
            {"id": user_id},
        )
        row = r.fetchone()
    if not row:
        return None
    return UserResponse(id=str(row[0]), email=row[1], role=row[2], is_active=row[3], created_at=row[4])


def update_user_password(user_id: str, old_password: str, new_password: str) -> bool:
    """Update user password. Returns True if successful."""
    user = get_user_by_id(user_id)
    if not user:
        raise ValueError("User not found")
    
    # Get user with password hash
    user_dict = get_user_by_email(user.email)
    if not user_dict:
        raise ValueError("User not found")
    
    if not verify_password(old_password, user_dict["password_hash"]):
        raise ValueError("Current password is incorrect")
    
    with postgres_client.get_session() as s:
        s.execute(
            text(f"UPDATE {USERS_TABLE} SET password_hash = :password_hash, updated_at = :updated_at WHERE id = :id"),
            {
                "id": user_id,
                "password_hash": hash_password(new_password),
                "updated_at": datetime.now(timezone.utc),
            },
        )
        s.commit()
    logger.info("Password updated", user_id=user_id)
    return True
