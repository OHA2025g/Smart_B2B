from fastapi import APIRouter, Depends, HTTPException, Request
from app.database import get_db
from app.dependencies import get_current_user, hash_password, verify_password, create_access_token
from app.schemas.common import success_response, error_response, serialize_doc
from app.schemas.auth import RegisterBody, LoginBody

router = APIRouter()


@router.post("/register")
async def register(request: Request, body: RegisterBody):
    db = get_db()
    existing = await db.users.find_one({"email": body.email.lower()})
    if existing:
        raise HTTPException(status_code=400, detail=error_response("Email already registered.", "VALIDATION_ERROR", path=str(request.url.path)))
    hashed = hash_password(body.password)
    doc = {
        "email": body.email.lower().strip(),
        "password": hashed,
        "role": body.role,
        "name": body.name.strip(),
        "isBanned": False,
        "isVerifiedSupplier": False,
    }
    r = await db.users.insert_one(doc)
    user_id = str(r.inserted_id)
    token = create_access_token(user_id)
    user_out = {"id": user_id, "email": doc["email"], "role": doc["role"], "name": doc["name"]}
    return success_response(data={"user": user_out, "token": token})


@router.post("/login")
async def login(request: Request, body: LoginBody):
    db = get_db()
    user = await db.users.find_one({"email": body.email.lower()}, projection={"password": 1, "email": 1, "role": 1, "name": 1})
    if not user or not verify_password(body.password, user.get("password", "")):
        raise HTTPException(status_code=401, detail=error_response("Invalid email or password.", "UNAUTHORIZED", path=str(request.url.path)))
    user_id = str(user["_id"])
    token = create_access_token(user_id)
    user_out = {"id": user_id, "email": user["email"], "role": user["role"], "name": user["name"]}
    return success_response(data={"user": user_out, "token": token})


@router.get("/me")
async def me(request: Request, user: dict = Depends(get_current_user)):
    return success_response(data={"user": serialize_doc(user)})
