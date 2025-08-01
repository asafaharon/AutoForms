"""
Input validation service to strengthen API endpoint security
"""
import re
import html
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from email.utils import parseaddr
from urllib.parse import urlparse

@dataclass
class ValidationRule:
    """Define validation rules for fields"""
    required: bool = False
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    pattern: Optional[str] = None
    allowed_values: Optional[List[str]] = None
    custom_validator: Optional[callable] = None

class InputValidator:
    """Comprehensive input validation for API endpoints"""
    
    # Common validation patterns
    PATTERNS = {
        'email': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
        'url': r'^https?://[^\s/$.?#].[^\s]*$',
        'alpha': r'^[a-zA-Z\s]+$',
        'alphanumeric': r'^[a-zA-Z0-9\s]+$',
        'slug': r'^[a-zA-Z0-9-_]+$',
        'phone': r'^\+?[\d\s\-\(\)]{10,20}$',
        'safe_html': r'^[^<>]*$',  # No HTML tags
        'mongodb_id': r'^[a-fA-F0-9]{24}$',
        'language_code': r'^[a-z]{2}(-[A-Z]{2})?$',
        'hex_color': r'^#[a-fA-F0-9]{6}$'
    }
    
    # Validation rules for different endpoints
    VALIDATION_RULES = {
        'form_generation': {
            'prompt': ValidationRule(
                required=True,
                min_length=10,
                max_length=2000,
                custom_validator=lambda x: len(x.strip()) > 0
            ),
            'title': ValidationRule(
                required=True,
                min_length=3,
                max_length=200,
                pattern='safe_html'
            ),
            'language': ValidationRule(
                required=False,
                pattern='language_code',
                allowed_values=['en', 'he', 'es', 'fr', 'de']
            )
        },
        
        'form_saving': {
            'title': ValidationRule(
                required=True,
                min_length=3,
                max_length=200,
                pattern='safe_html'
            ),
            'prompt': ValidationRule(
                required=False,
                min_length=0,
                max_length=2000
            ),
            'language': ValidationRule(
                required=False,
                pattern='language_code',
                allowed_values=['en', 'he', 'es', 'fr', 'de']
            )
        },
        
        'form_submission': {
            'form_id': ValidationRule(
                required=True,
                pattern='mongodb_id'
            ),
            'csrf_token': ValidationRule(
                required=True,
                min_length=20,
                max_length=200
            )
        },
        
        'email_operations': {
            'email': ValidationRule(
                required=True,
                pattern='email',
                max_length=254
            ),
            'title': ValidationRule(
                required=False,
                max_length=200,
                pattern='safe_html'
            )
        },
        
        'user_registration': {
            'email': ValidationRule(
                required=True,
                pattern='email',
                max_length=254
            ),
            'password': ValidationRule(
                required=True,
                min_length=8,
                max_length=128,
                custom_validator=lambda x: self._validate_password_strength(x)
            ),
            'name': ValidationRule(
                required=False,
                max_length=100,
                pattern='safe_html'
            )
        },
        
        'unsubscribe': {
            'email': ValidationRule(
                required=True,
                pattern='email',
                max_length=254
            ),
            'token': ValidationRule(
                required=True,
                min_length=20,
                max_length=200,
                pattern='alphanumeric'
            ),
            'reason': ValidationRule(
                required=False,
                max_length=500,
                pattern='safe_html'
            )
        }
    }
    
    @staticmethod
    def _validate_password_strength(password: str) -> bool:
        """Validate password strength"""
        if len(password) < 8:
            return False
        
        # Check for at least one letter and one number
        has_letter = bool(re.search(r'[a-zA-Z]', password))
        has_number = bool(re.search(r'\d', password))
        
        return has_letter and has_number
    
    @staticmethod
    def sanitize_string(value: str, max_length: int = None) -> str:
        """Sanitize string input"""
        if not isinstance(value, str):
            return str(value)
        
        # Strip whitespace
        value = value.strip()
        
        # HTML escape to prevent XSS
        value = html.escape(value)
        
        # Truncate if necessary
        if max_length and len(value) > max_length:
            value = value[:max_length]
        
        return value
    
    @staticmethod
    def sanitize_email(email: str) -> str:
        """Sanitize and validate email address"""
        if not isinstance(email, str):
            raise ValueError("Email must be a string")
        
        email = email.strip().lower()
        
        # Basic email validation
        if not re.match(InputValidator.PATTERNS['email'], email):
            raise ValueError("Invalid email format")
        
        # Additional checks
        name, addr = parseaddr(email)
        if not addr or '@' not in addr:
            raise ValueError("Invalid email format")
        
        return addr
    
    @staticmethod
    def sanitize_url(url: str) -> str:
        """Sanitize and validate URL"""
        if not isinstance(url, str):
            raise ValueError("URL must be a string")
        
        url = url.strip()
        
        # Parse URL to validate structure
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            raise ValueError("Invalid URL format")
        
        # Only allow HTTP/HTTPS
        if parsed.scheme not in ['http', 'https']:
            raise ValueError("Only HTTP/HTTPS URLs allowed")
        
        return url
    
    def validate_field(self, field_name: str, value: Any, rule: ValidationRule) -> tuple[bool, str]:
        """Validate a single field against its rule"""
        # Check required
        if rule.required and (value is None or value == ''):
            return False, f"{field_name} is required"
        
        # Skip other validations if not required and empty
        if not rule.required and (value is None or value == ''):
            return True, ""
        
        # Convert to string for validation
        str_value = str(value).strip() if value is not None else ''
        
        # Check length constraints
        if rule.min_length is not None and len(str_value) < rule.min_length:
            return False, f"{field_name} must be at least {rule.min_length} characters"
        
        if rule.max_length is not None and len(str_value) > rule.max_length:
            return False, f"{field_name} must not exceed {rule.max_length} characters"
        
        # Check pattern
        if rule.pattern and str_value:
            pattern = self.PATTERNS.get(rule.pattern, rule.pattern)
            if not re.match(pattern, str_value):
                return False, f"{field_name} format is invalid"
        
        # Check allowed values
        if rule.allowed_values and str_value not in rule.allowed_values:
            return False, f"{field_name} must be one of: {', '.join(rule.allowed_values)}"
        
        # Check custom validator
        if rule.custom_validator:
            try:
                if not rule.custom_validator(str_value):
                    return False, f"{field_name} validation failed"
            except Exception as e:
                return False, f"{field_name} validation error: {str(e)}"
        
        return True, ""
    
    def validate_data(self, data: Dict[str, Any], rule_set: str) -> tuple[bool, List[str], Dict[str, Any]]:
        """
        Validate data against a rule set
        Returns: (is_valid, errors, sanitized_data)
        """
        if rule_set not in self.VALIDATION_RULES:
            return False, [f"Unknown validation rule set: {rule_set}"], {}
        
        rules = self.VALIDATION_RULES[rule_set]
        errors = []
        sanitized_data = {}
        
        # Validate each field in rules
        for field_name, rule in rules.items():
            value = data.get(field_name)
            is_valid, error = self.validate_field(field_name, value, rule)
            
            if not is_valid:
                errors.append(error)
            else:
                # Sanitize the value
                if value is not None:
                    if field_name == 'email':
                        try:
                            sanitized_data[field_name] = self.sanitize_email(value)
                        except ValueError as e:
                            errors.append(str(e))
                    elif field_name in ['url', 'link']:
                        try:
                            sanitized_data[field_name] = self.sanitize_url(value)
                        except ValueError as e:
                            errors.append(str(e))
                    else:
                        sanitized_data[field_name] = self.sanitize_string(
                            str(value), 
                            rule.max_length
                        )
                else:
                    sanitized_data[field_name] = value
        
        # Check for unexpected fields (basic protection)
        expected_fields = set(rules.keys())
        provided_fields = set(data.keys())
        unexpected_fields = provided_fields - expected_fields
        
        if unexpected_fields:
            # Log unexpected fields but don't fail validation
            print(f"⚠️ Unexpected fields in {rule_set}: {unexpected_fields}")
        
        return len(errors) == 0, errors, sanitized_data
    
    def validate_form_data(self, form_data: Dict[str, Any]) -> tuple[bool, List[str], Dict[str, Any]]:
        """Validate form submission data with flexible field validation"""
        errors = []
        sanitized_data = {}
        
        # Basic validation for all form fields
        for field_name, value in form_data.items():
            if value is None:
                continue
            
            str_value = str(value).strip()
            
            # Check for excessively long values
            if len(str_value) > 10000:  # 10KB limit per field
                errors.append(f"Field '{field_name}' exceeds maximum length")
                continue
            
            # Sanitize the value
            sanitized_value = self.sanitize_string(str_value, 10000)
            sanitized_data[field_name] = sanitized_value
        
        return len(errors) == 0, errors, sanitized_data

# Global validator instance
input_validator = InputValidator()

# Validation decorators for FastAPI endpoints
def validate_input(rule_set: str):
    """Decorator to validate input data against rule set"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Extract request data (this is a simplified version)
            # In real implementation, you'd extract data from request
            data = kwargs.get('data', {})
            
            is_valid, errors, sanitized_data = input_validator.validate_data(data, rule_set)
            if not is_valid:
                from fastapi import HTTPException
                raise HTTPException(status_code=400, detail=f"Validation errors: {'; '.join(errors)}")
            
            # Replace original data with sanitized data
            kwargs['data'] = sanitized_data
            return await func(*args, **kwargs)
        return wrapper
    return decorator