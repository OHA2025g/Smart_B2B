from urllib.parse import urlparse
from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings

_client: AsyncIOMotorClient | None = None
_db = None


def _db_name() -> str:
    path = urlparse(settings.mongodb_uri).path
    name = (path or "/").strip("/").split("/")[0].split("?")[0]
    return name or "smartb2b"


def get_client() -> AsyncIOMotorClient:
    global _client
    if _client is None:
        _client = AsyncIOMotorClient(settings.mongodb_uri)
    return _client


def get_db():
    global _db
    if _db is None:
        _db = get_client()[_db_name()]
    return _db


async def connect_db():
    client = get_client()
    await client.admin.command("ping")
    print("MongoDB connected")


async def close_db():
    global _client
    if _client:
        _client.close()
        _client = None
