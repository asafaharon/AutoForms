"""
Simple user models without pydantic dependencies
"""
from datetime import datetime
from typing import Optional, Dict, Any

class UserCreate:
    """
    Model for creating a new user. Used for registration.
    """
    def __init__(self, username: str, email: str, password: str):
        self.username = username
        self.email = email
        self.password = password
    
    def validate(self) -> Optional[str]:
        """Basic validation - returns error message if invalid"""
        if not self.username or len(self.username.strip()) == 0:
            return "Username cannot be empty"
        if not self.email or "@" not in self.email:
            return "Invalid email address"
        if not self.password or len(self.password.strip()) == 0:
            return "Password cannot be empty"
        return None

class UserInDB:
    """
    Model representing a user as stored in the database.
    """
    def __init__(self, id: str, username: str, email: str, hashed_password: str, 
                 created_at: datetime, is_admin: bool = False):
        self.id = id
        self.username = username
        self.email = email
        self.hashed_password = hashed_password
        self.created_at = created_at
        self.is_admin = is_admin
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserInDB':
        """Create UserInDB from database document"""
        return cls(
            id=str(data.get("_id", "")),
            username=data.get("username", ""),
            email=data.get("email", ""),
            hashed_password=data.get("hashed_password", ""),
            created_at=data.get("created_at", datetime.utcnow()),
            is_admin=data.get("is_admin", False)
        )

class UserPublic:
    """
    Model for user data that is safe to expose publicly.
    """
    def __init__(self, id: str, username: str, email: str, created_at: datetime, is_admin: bool = False):
        self.id = id
        self.username = username
        self.email = email
        self.created_at = created_at
        self.is_admin = is_admin
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON responses"""
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "created_at": self.created_at.isoformat(),
            "is_admin": self.is_admin
        }