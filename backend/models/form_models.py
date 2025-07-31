"""
Simple form models without pydantic dependencies
"""
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime

class GenerateResp:
    """Response model for form generation"""
    
    def __init__(self, form_id: str, html: str, embed: str):
        self.form_id = form_id
        self.html = html
        self.embed = embed
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON responses"""
        return {
            "form_id": self.form_id,
            "html": self.html,
            "embed": self.embed
        }

@dataclass
class Form:
    """User's saved form"""
    id: str
    title: str
    html: str
    prompt: str
    user_id: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    is_active: bool = True
    submission_count: int = 0
    language: str = "en"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "html": self.html,
            "prompt": self.prompt,
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat(),
            "is_active": self.is_active,
            "submission_count": self.submission_count,
            "language": self.language
        }

@dataclass
class FormSubmission:
    """Form submission from users"""
    id: str
    form_id: str
    form_title: str
    data: Dict[str, Any]  # The actual form field data
    submitted_at: datetime = field(default_factory=datetime.utcnow)
    user_agent: Optional[str] = None
    referrer: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "form_id": self.form_id,
            "form_title": self.form_title,
            "data": self.data,
            "submitted_at": self.submitted_at.isoformat(),
            "user_agent": self.user_agent,
            "referrer": self.referrer
        }