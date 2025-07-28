"""
Production-ready configuration with security validation
"""
import os
import sys
from typing import List
from pathlib import Path

# Load .env file manually if it exists
def load_env_file():
    """Manually load .env file without dependencies"""
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if env_path.exists():
        try:
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        # Remove quotes if present
                        value = value.strip('"\'')
                        os.environ[key.strip()] = value
        except Exception as e:
            print(f"Warning: Could not load .env file: {e}")

# Load environment variables
load_env_file()

class Settings:
    """Simple settings class without pydantic"""
    
    def __init__(self):
        # Application settings
        self.app_env = os.getenv("APP_ENV", "development")
        self.debug = os.getenv("DEBUG", "false").lower() == "true"
        self.host = os.getenv("HOST", "127.0.0.1")
        self.port = int(os.getenv("PORT", "8000"))
        
        # Load all environment variables
        self.openai_key = os.getenv("OPENAI_KEY", "sk-test-key")
        self.mongodb_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
        self.database_name = os.getenv("DATABASE_NAME", "autoforms")
        
        # CORS configuration
        allowed_origins_str = os.getenv("ALLOWED_ORIGINS", "*")
        if allowed_origins_str == "*":
            self.allowed_origins = ["*"]
        else:
            self.allowed_origins = [origin.strip() for origin in allowed_origins_str.split(",")]
        
        self.openai_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER", "test@test.com")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "test-password")
        self.email_from = os.getenv("EMAIL_FROM", "test@test.com")
        self.base_url = os.getenv("BASE_URL", "http://127.0.0.1:8000")
        self.jwt_secret = os.getenv("JWT_SECRET", "test-jwt-secret")
        self._admin_emails_raw = os.getenv("ADMIN_EMAILS", "")
        
        # Redis configuration
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.redis_enabled = os.getenv("REDIS_ENABLED", "true").lower() == "true"
        
        # Cache settings
        self.cache_ttl_form_generation = int(os.getenv("CACHE_TTL_FORM_GENERATION", "1800"))  # 30 minutes
        self.cache_ttl_user_session = int(os.getenv("CACHE_TTL_USER_SESSION", "86400"))  # 24 hours
        self.cache_ttl_api_response = int(os.getenv("CACHE_TTL_API_RESPONSE", "600"))  # 10 minutes
        
        # Rate limiting
        self.rate_limit_requests = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
        self.rate_limit_window = int(os.getenv("RATE_LIMIT_WINDOW", "3600"))
        
        # Logging
        self.log_level = os.getenv("LOG_LEVEL", "INFO").upper()
        self.sentry_dsn = os.getenv("SENTRY_DSN", "")
        
        # Validate critical settings
        self._validate_settings()
        
    def _validate_settings(self):
        """Validate critical environment variables"""
        warnings = []
        errors = []
        
        # Check OpenAI key
        if self.openai_key == "sk-test-key" or not self.openai_key.startswith("sk-"):
            warnings.append("OPENAI_KEY appears to be a test/invalid key")
        
        # Check JWT secret in production
        if self.jwt_secret == "test-jwt-secret":
            warnings.append("JWT_SECRET is using default test value - should be changed in production")
        elif len(self.jwt_secret) < 32:
            warnings.append("JWT_SECRET should be at least 32 characters long")
        
        # Check MongoDB URI format
        if not self.mongodb_uri.startswith(("mongodb://", "mongodb+srv://")):
            errors.append("MONGODB_URI must start with 'mongodb://' or 'mongodb+srv://'")
        
        # Check SMTP configuration if not using defaults
        if self.smtp_user != "test@test.com" and "@" not in self.smtp_user:
            warnings.append("SMTP_USER should be a valid email address")
        
        # Check base URL format
        if not self.base_url.startswith(("http://", "https://")):
            warnings.append("BASE_URL should start with 'http://' or 'https://'")
        
        # Print warnings
        if warnings:
            print("⚠️ Configuration warnings:")
            for warning in warnings:
                print(f"   - {warning}")
        
        # Handle errors
        if errors:
            print("❌ Configuration errors:")
            for error in errors:
                print(f"   - {error}")
            print("\nPlease fix these configuration issues before running the application.")
            sys.exit(1)

    @property
    def admin_emails(self) -> List[str]:
        """Parse admin emails from comma-separated string"""
        if not self._admin_emails_raw:
            return []
        return [email.strip() for email in self._admin_emails_raw.split(",") if email.strip()]

# Global settings instance
_settings = None

def get_settings() -> Settings:
    """Get settings singleton"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings