from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List
from dotenv import load_dotenv
from pathlib import Path

# טוען את קובץ .env אם קיים
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

class Settings(BaseSettings):
    openai_key: str = Field(..., env="OPENAI_KEY")
    mongodb_uri: str = Field("mongodb://localhost:27017", env="MONGODB_URI")
    database_name: str = "autoforms"
    allowed_origins: List[str] = ["*"]
    openai_model: str = "gpt-4o-mini"
    smtp_host: str = Field("smtp.gmail.com", env="SMTP_HOST")
    smtp_port: int = Field(587, env="SMTP_PORT")
    smtp_user: str = Field(..., env="SMTP_USER")
    smtp_password: str = Field(..., env="SMTP_PASSWORD")
    email_from: str = Field(..., env="EMAIL_FROM")
    base_url: str = Field("http://127.0.0.1:8083", env="BASE_URL")
    jwt_secret: str = Field(..., env="JWT_SECRET")
    admin_emails: List[str] = Field(default_factory=list, env="ADMIN_EMAILS")
    port: int = Field(8000, env="PORT")
    environment: str = Field("development", env="ENVIRONMENT")

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8"
    }

@lru_cache()
def get_settings() -> Settings:
    return Settings()
