import re
import html
from typing import Optional
from fastapi import HTTPException, status


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
    """Validate password strength."""
    if len(password) < 8:
        return False
    # At least one uppercase, one lowercase, one digit
    if not re.search(r'[A-Z]', password):
        return False
    if not re.search(r'[a-z]', password):
        return False
    if not re.search(r'\d', password):
        return False
    return True


def validate_username(username: str) -> bool:
    """Validate username format."""
    if not username or len(username) < 3 or len(username) > 50:
        return False
    # Allow alphanumeric, underscore, hyphen
    return re.match(r'^[a-zA-Z0-9_-]+$', username) is not None


def validate_form_title(title: str) -> bool:
    """Validate form title."""
    if not title or len(title.strip()) < 1 or len(title.strip()) > 200:
        return False
    return True


def validate_url(url: str) -> bool:
    """Validate URL format."""
    url_regex = r'^https?://[^\s/$.?#].[^\s]*$'
    return re.match(url_regex, url) is not None


class ValidationError(HTTPException):
    """Custom validation error."""
    def __init__(self, detail: str):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)