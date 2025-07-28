"""
Test configuration and fixtures
"""
import pytest
import asyncio
import os
from unittest.mock import AsyncMock, MagicMock
from httpx import AsyncClient
from fastapi.testclient import TestClient
from motor.motor_asyncio import AsyncIOMotorClient
import mongomock

# Set testing environment
os.environ["TESTING"] = "true"
os.environ["MONGODB_URL"] = "mongodb://localhost:27017/autoforms_test"
os.environ["OPENAI_API_KEY"] = "sk-test-key"
os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only"

from backend.main import app
from backend.db import get_db
from backend.config import get_settings


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for the test session"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def mock_db():
    """Mock database connection"""
    client = mongomock.MongoClient()
    db = client.autoforms_test
    yield db
    client.close()


@pytest.fixture
async def app_with_mock_db(mock_db):
    """FastAPI app with mocked database"""
    app.dependency_overrides[get_db] = lambda: mock_db
    yield app
    app.dependency_overrides.clear()


@pytest.fixture
async def client(app_with_mock_db):
    """Async test client"""
    async with AsyncClient(app=app_with_mock_db, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def sync_client(app_with_mock_db):
    """Synchronous test client"""
    return TestClient(app_with_mock_db)


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client"""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "<html><body><h1>Test Form</h1></body></html>"
    
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
    return mock_client


@pytest.fixture
def sample_user_data():
    """Sample user data for testing"""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpassword123"
    }


@pytest.fixture
def sample_form_data():
    """Sample form data for testing"""
    return {
        "title": "Test Form",
        "html": "<html><body><form><input type='text' name='name'/></form></body></html>",
        "prompt": "Create a contact form"
    }


@pytest.fixture
def hebrew_test_data():
    """Hebrew content test data"""
    return {
        "prompt": "כתוב שיר אהבה עליי ונחמה",
        "expected_type": "content",
        "expected_theme": "love",
        "expected_lang": "he"
    }


@pytest.fixture
def auth_headers():
    """Generate auth headers for testing"""
    def _create_headers(token="test-token"):
        return {"Authorization": f"Bearer {token}"}
    return _create_headers


@pytest.fixture
def mock_settings():
    """Mock application settings"""
    settings = get_settings()
    settings.openai_key = "sk-test-key"
    settings.mongodb_url = "mongodb://localhost:27017/autoforms_test"
    settings.secret_key = "test-secret-key"
    return settings