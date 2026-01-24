"""Password hashing utilities (bcrypt)."""
import bcrypt

# Bcrypt has a 72-byte limit
BCRYPT_MAX_BYTES = 72
BCRYPT_ROUNDS = 12


def hash_password(plain: str) -> str:
    """Hash a password using bcrypt. Raises ValueError if password exceeds 72 bytes."""
    if not plain:
        raise ValueError("Password cannot be empty")
    
    # Validate password length BEFORE attempting to hash
    password_bytes = plain.encode('utf-8')
    byte_length = len(password_bytes)
    char_length = len(plain)
    
    if byte_length > BCRYPT_MAX_BYTES:
        raise ValueError(
            f"Password cannot be longer than {BCRYPT_MAX_BYTES} bytes. "
            f"Your password is {byte_length} bytes ({char_length} characters). "
            "Please use a shorter password."
        )
    
    try:
        # Use bcrypt directly to avoid passlib compatibility issues
        salt = bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
        hashed = bcrypt.hashpw(password_bytes, salt)
        # Return as string (bcrypt returns bytes)
        return hashed.decode('utf-8')
    except Exception as e:
        error_msg = str(e)
        raise ValueError(f"Failed to hash password: {error_msg}") from e


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a password against a hash."""
    try:
        # Use bcrypt directly to avoid passlib compatibility issues
        password_bytes = plain.encode('utf-8')
        hash_bytes = hashed.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hash_bytes)
    except Exception:
        return False
