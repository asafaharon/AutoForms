from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional

class UserCreate(BaseModel):
    """
    Model for creating a new user. Used for registration.
    """
    username: str = Field(..., min_length=3, max_length=30)
    email: EmailStr
    password: str = Field(..., min_length=6)

class UserInDB(BaseModel):
    """
    Model representing a user as stored in the database. Includes sensitive data.
    """
    id: str
    username: str
    email: EmailStr
    hashed_password: str
    created_at: datetime
    is_admin: bool = False  # Field to determine admin privileges

class UserPublic(BaseModel):
    """
    Model for user data that is safe to expose publicly in API responses.
    """
    id: str
    username: str
    email: EmailStr
    created_at: datetime
    is_admin: bool  # Expose admin status for frontend/dependency checks