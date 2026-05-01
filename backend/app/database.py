from urllib.parse import urlparse

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ServerSelectionTimeoutError

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
    try:
        await client.admin.command("ping")
    except ServerSelectionTimeoutError as e:
        raise RuntimeError(
            "MongoDB is unreachable. In Docker/EasyPanel, set MONGODB_URI (or MONGO_URL) to your "
            "MongoDB service hostname on the same network — not localhost unless Mongo runs in "
            "the same container. Example: mongodb://mongo:27017/smartb2b"
        ) from e
    print("MongoDB connected")


async def close_db():
    global _client
    if _client:
        _client.close()
        _client = None
