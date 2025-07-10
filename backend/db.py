from motor.motor_asyncio import AsyncIOMotorClient
from .config import get_settings

_client: AsyncIOMotorClient | None = None

async def get_client() -> AsyncIOMotorClient:
    global _client
    if _client is None:
        settings = get_settings()
        _client = AsyncIOMotorClient(settings.mongodb_uri, uuidRepresentation="standard")
    return _client

async def get_db():
    client = await get_client()
    settings = get_settings()
    return client[settings.database_name]
