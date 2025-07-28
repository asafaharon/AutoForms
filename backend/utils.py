import re
import html
from typing import Optional
from fastapi import HTTPException, status
from bson import ObjectId
from bson.errors import InvalidId


def sanitize_filename(filename: str) -> str:
    """Sanitize a filename to prevent path traversal and invalid characters."""
    # Remove path separators and dangerous characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove leading/trailing whitespace and dots
    filename = filename.strip(' .')
    # Ensure it's not empty
    if not filename:
        filename = "untitled"
    return filename


def validate_email(email: str) -> bool:
    """Validate email format."""
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(email_regex, email) is not None


def escape_html(text: str) -> str:
    """Escape HTML to prevent XSS."""
    return html.escape(text)


def validate_password(password: str) -> bool:
    """Validate password - minimal requirements."""
    # Only require password to not be empty
    return password and len(password.strip()) > 0


def validate_username(username: str) -> bool:
    """Validate username format - minimal requirements."""
    # Only require username to not be empty and reasonable length
    return username and len(username.strip()) > 0 and len(username.strip()) <= 100


def validate_form_title(title: str) -> bool:
    """Validate form title."""
    if not title or len(title.strip()) < 1 or len(title.strip()) > 200:
        return False
    return True


def validate_url(url: str) -> bool:
    """Validate URL format."""
    url_regex = r'^https?://[^\s/$.?#].[^\s]*$'
    return re.match(url_regex, url) is not None


def validate_object_id(obj_id: str) -> ObjectId:
    """Validate and convert string to ObjectId."""
    try:
        return ObjectId(obj_id)
    except InvalidId:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid ID format"
        )


class ValidationError(HTTPException):
    """Custom validation error."""
    def __init__(self, detail: str):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)