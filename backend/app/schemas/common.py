from typing import Any
from bson import ObjectId
from pydantic import BaseModel, ConfigDict

# Use same response shape as Node API: { success, data? | message?, ... }
def success_response(data: Any = None, message: str | None = None) -> dict:
    out: dict = {"success": True}
    if data is not None:
        out["data"] = data
    if message is not None:
        out["message"] = message
    return out


def error_response(message: str, error_code: str = "ERROR", details: list | None = None, path: str | None = None) -> dict:
    import datetime
    out: dict = {
        "success": False,
        "message": message,
        "errorCode": error_code,
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
    }
    if details is not None:
        out["details"] = details
    if path is not None:
        out["path"] = path
    return out


def serialize_doc(doc: dict | None) -> dict | None:
    """Convert MongoDB doc: _id -> id (str), datetime to ISO string."""
    if doc is None:
        return None
    out = dict(doc)
    if "_id" in out:
        sid = str(out.pop("_id"))
        out["id"] = sid
        out["_id"] = sid  # frontend compatibility
    for k, v in list(out.items()):
        if hasattr(v, "isoformat"):
            out[k] = v.isoformat() if v else None
        elif isinstance(v, ObjectId):
            out[k] = str(v)
        elif isinstance(v, list):
            out[k] = [_serialize_value(x) for x in v]
        elif isinstance(v, dict):
            out[k] = serialize_doc(v)
    return out


def _serialize_value(x: Any) -> Any:
    if isinstance(x, dict):
        return serialize_doc(x)
    if isinstance(x, ObjectId):
        return str(x)
    if hasattr(x, "isoformat"):
        return x.isoformat() if x else None
    if isinstance(x, list):
        return [_serialize_value(i) for i in x]
    return x


class PyObjectId(str):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if isinstance(v, ObjectId):
            return str(v)
        if isinstance(v, str) and len(v) == 24:
            try:
                ObjectId(v)
                return v
            except Exception:
                pass
        raise ValueError("Invalid ObjectId")
