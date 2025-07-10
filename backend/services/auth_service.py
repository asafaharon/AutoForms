from datetime import datetime, timedelta
from jose import jwt, JWTError
from passlib.context import CryptContext

from backend.config import get_settings
# קונטקסט להצפנת סיסמאות עם bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = "supersecret"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_minutes: int = 60):
    settings = get_settings()
    to_encode = data.copy()
    to_encode["exp"] = datetime.utcnow() + timedelta(minutes=expires_minutes)
    return jwt.encode(to_encode, settings.openai_key, algorithm=ALGORITHM)

def decode_token(token: str):
    settings = get_settings()                       # ← וגם כאן
    return jwt.decode(token, settings.openai_key, algorithms=[ALGORITHM])