from fastapi import Depends, Cookie, HTTPException, status
from jose import JWTError
from backend.db import get_db
from backend.services.auth_service import decode_token
from bson import ObjectId
from bson.errors import InvalidId
from pymongo.errors import PyMongoError
import logging

logger = logging.getLogger(__name__)

# 1. ייבוא המודל الصحيح
from backend.models.user import UserPublic


# 2. עדכון הפונקציה כדי שתחזיר מודל Pydantic
async def get_current_user(token: str | None = Cookie(None), db=Depends(get_db)) -> UserPublic:
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated, token not provided",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = decode_token(token)
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except JWTError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")

    try:
        user_obj_id = ObjectId(user_id)
        user_doc = await db.users.find_one({"_id": user_obj_id})
    except InvalidId:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID format"
        )
    except PyMongoError as e:
        logger.error(f"Database error when fetching user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database connection error"
        )
    except Exception as e:
        logger.error(f"Unexpected error when fetching user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

    if user_doc is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    # המרת הנתונים ממסד הנתונים למודל UserPublic
    return UserPublic(
        id=str(user_doc["_id"]),
        username=user_doc["username"],
        email=user_doc["email"],
        created_at=user_doc["created_at"],
        is_admin=user_doc.get("is_admin", False)  # .get() בטוח יותר
    )


# 3. עדכון התלות של האדמין
async def get_current_admin_user(current_user: UserPublic = Depends(get_current_user)) -> UserPublic:
    """
    תלות שבודקת אם המשתמש המחובר הוא מנהל מערכת.
    אם לא, היא זורקת שגיאת 403 Forbidden.
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this resource",
        )
    return current_user


async def get_current_user_websocket(token: str) -> dict:
    """Get current user for WebSocket authentication"""
    try:
        payload = decode_token(token)
        user_id = payload.get("sub")
        if not user_id:
            return None
        
        # Get user from database
        db = await get_db()
        user_obj_id = ObjectId(user_id)
        user_doc = await db.users.find_one({"_id": user_obj_id})
        if not user_doc:
            return None
        
        return {
            "id": str(user_doc["_id"]),
            "username": user_doc["username"],
            "email": user_doc["email"],
            "is_admin": user_doc.get("is_admin", False)
        }
    
    except (JWTError, InvalidId, ValueError):
        logger.warning(f"Invalid token or user ID format for WebSocket authentication")
        return None
    except PyMongoError as e:
        logger.error(f"Database error in WebSocket authentication: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error in WebSocket authentication: {e}")
        return None