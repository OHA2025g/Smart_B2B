from typing import Annotated
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, APIKeyCookie
from jose import JWTError, jwt
from passlib.context import CryptContext
from bson import ObjectId

from app.config import settings
from app.database import get_db
from app.schemas.common import error_response

security = HTTPBearer(auto_error=False)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(user_id: str) -> str:
    from jose import jwt as jose_jwt
    import datetime
    # expires_in: "7d" -> timedelta
    unit = settings.jwt_expires_in[-1]
    val = int(settings.jwt_expires_in[:-1] or "7")
    if unit == "d":
        delta = datetime.timedelta(days=val)
    elif unit == "h":
        delta = datetime.timedelta(hours=val)
    else:
        delta = datetime.timedelta(days=7)
    expire = datetime.datetime.utcnow() + delta
    to_encode = {"id": user_id, "exp": expire}
    return jose_jwt.encode(to_encode, settings.jwt_secret, algorithm="HS256")


async def get_current_user(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
):
    token = None
    if credentials:
        token = credentials.credentials
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error_response("Not authorized. No token.", "UNAUTHORIZED", path=str(request.url.path)),
        )
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
        user_id = payload.get("id")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=error_response("Invalid token.", "INVALID_TOKEN", path=request.url.path),
            )
    except JWTError as e:
        msg = "Token expired." if "expired" in str(e).lower() else "Not authorized. Invalid token."
        code = "TOKEN_EXPIRED" if "expired" in str(e).lower() else "INVALID_TOKEN"
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error_response(msg, code, path=request.url.path),
        )
    db = get_db()
    user = await db.users.find_one({"_id": ObjectId(user_id)}, projection={"password": 0})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error_response("User not found.", "UNAUTHORIZED", path=request.url.path),
        )
    if user.get("isBanned"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=error_response("Account is suspended.", "FORBIDDEN", path=request.url.path),
        )
    user["id"] = str(user["_id"])
    return user


def require_roles(*roles: str):
    async def role_check(request: Request, user: dict = Depends(get_current_user)):
        if user.get("role") not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=error_response("Access denied for this role.", "FORBIDDEN", path=request.url.path),
            )
        return user
    return role_check
