from motor.motor_asyncio import AsyncIOMotorClient
from .config import get_settings
import asyncio

_client: AsyncIOMotorClient | None = None

async def get_client() -> AsyncIOMotorClient:
    global _client
    if _client is None:
        settings = get_settings()
        try:
            _client = AsyncIOMotorClient(
                settings.mongodb_uri, 
                uuidRepresentation="standard",
                maxPoolSize=10,
                minPoolSize=1,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=10000,
                socketTimeoutMS=5000
            )
            # Test the connection
            await _client.admin.command('ping')
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            raise
    return _client

async def get_db():
    try:
        client = await get_client()
        settings = get_settings()
        return client[settings.database_name]
    except Exception as e:
        print(f"❌ Database access failed: {e}")
        raise

async def close_db_connection():
    global _client
    if _client:
        _client.close()
        _client = None
