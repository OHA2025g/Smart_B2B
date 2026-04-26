from fastapi import APIRouter, Depends
from app.dependencies import get_current_user
from app.schemas.message import MessagePost
from app.services import message_thread

router = APIRouter()


@router.get("/{rfqId}")
async def get_thread(rfqId: str, user: dict = Depends(get_current_user)):
    return await message_thread.get_thread_response(rfqId, user)


@router.post("/{rfqId}", status_code=201)
async def post_message(rfqId: str, body: MessagePost, user: dict = Depends(get_current_user)):
    return await message_thread.post_message_response(
        rfqId,
        user,
        body.text,
        confirm_send=bool(body.confirm_send),
    )
