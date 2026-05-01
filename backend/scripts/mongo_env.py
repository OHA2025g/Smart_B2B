"""Mongo URI + DB name for scripts (aligned with app settings: MONGO_URL, DB_NAME, etc.)."""
import os
from urllib.parse import urlparse


def resolve_mongodb_uri() -> str:
    return (
        os.getenv("MONGODB_URI")
        or os.getenv("MONGO_URL")
        or os.getenv("DATABASE_URL")
        or "mongodb://localhost:27017/smartb2b"
    )


def resolve_db_name(uri: str | None = None) -> str:
    uri = uri or resolve_mongodb_uri()
    path = urlparse(uri).path
    name = (path or "/").strip("/").split("/")[0].split("?")[0]
    if name:
        return name
    db = os.getenv("DB_NAME") or os.getenv("MONGO_DB_NAME")
    if db and str(db).strip():
        return str(db).strip()
    return "smartb2b"


def describe_connection(uri: str | None = None) -> str:
    uri = uri or resolve_mongodb_uri()
    dbn = resolve_db_name(uri)
    p = urlparse(uri)
    port = p.port or 27017
    return f"database={dbn!r} host={p.hostname!r} port={port}"
