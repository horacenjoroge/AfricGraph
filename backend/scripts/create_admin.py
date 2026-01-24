#!/usr/bin/env python3
"""Script to create or promote a user to admin role."""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from src.infrastructure.database.postgres_client import postgres_client
from src.auth.password import hash_password

USERS_TABLE = "users"


def create_admin_user(email: str, password: str) -> None:
    """Create a new admin user or promote existing user to admin."""
    email = email.lower()
    
    with postgres_client.get_session() as s:
        # Check if user exists
        r = s.execute(
            text(f"SELECT id, role FROM {USERS_TABLE} WHERE email = :email"),
            {"email": email},
        )
        existing = r.fetchone()
        
        if existing:
            user_id, current_role = existing
            if current_role == "admin":
                print(f"User {email} is already an admin.")
                return
            
            # Promote to admin
            s.execute(
                text(f"UPDATE {USERS_TABLE} SET role = 'admin' WHERE id = :id"),
                {"id": user_id},
            )
            s.commit()
            print(f"✓ Promoted {email} to admin role.")
        else:
            # Create new admin user
            password_hash = hash_password(password)
            s.execute(
                text(f"""
                INSERT INTO {USERS_TABLE} (email, password_hash, role, is_active, created_at, updated_at)
                VALUES (:email, :password_hash, 'admin', true, now(), now())
                """),
                {
                    "email": email,
                    "password_hash": password_hash,
                },
            )
            s.commit()
            print(f"✓ Created admin user: {email}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python create_admin.py <email> <password>")
        print("Example: python create_admin.py admin@example.com mypassword123")
        sys.exit(1)
    
    email = sys.argv[1]
    password = sys.argv[2]
    
    try:
        create_admin_user(email, password)
        print("\n✓ Admin user ready! You can now login and access /admin")
    except Exception as e:
        print(f"✗ Error: {e}")
        sys.exit(1)
