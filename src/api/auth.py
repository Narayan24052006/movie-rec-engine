from datetime import datetime, timedelta
import jwt
import re
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from typing import Optional
from src.api.database import get_user_by_username, is_username_taken

SECRET_KEY = "streamrec-super-secret-production-key" # In real app, put in ENV
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7 # 7 days for convenience

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

def validate_email(email: str) -> bool:
    """Return True if the email is a Gmail address (case‑insensitive)."""
    email = email.strip().lower()
    return email.endswith("@gmail.com")

PASSWORD_REGEX = re.compile(r"^(?=.*[A-Z])(?=.*[0-9])(?=.*[!@#$%^&*()_+\-={}\[\]|\\:;\"'<>,.?/]).{8,}$")

def validate_password(pwd: str) -> bool:
    """Enforce min 8 chars, at least one uppercase, one digit, one special char."""
    return bool(PASSWORD_REGEX.match(pwd))

class TokenData(BaseModel):
    username: Optional[str] = None

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str, skip_validation: bool = False):
    # Enforce password policy at hash time (defensive)
    if not skip_validation and not validate_password(password):
        raise ValueError("Password does not meet complexity requirements")
    return pwd_context.hash(password)



def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except jwt.PyJWTError:
        raise credentials_exception
        
    user = get_user_by_username(username=token_data.username)
    if user is None:
        raise credentials_exception
    return user
