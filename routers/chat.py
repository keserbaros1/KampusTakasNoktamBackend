import jwt
import uuid
from typing import List, Dict
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, status, Query, File, UploadFile
from sqlalchemy.orm import Session
from database import get_db, SessionLocal
from models.chat import Conversation, Message
from models.user import User
from schemas.chat import ConversationResponse, MessageResponse, AttachmentResponse
from routers.auth import get_current_user, SECRET_KEY, ALGORITHM

router = APIRouter(prefix="/chat", tags=["Chat"])

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        self.active_connections[user_id] = websocket

    def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]

manager = ConnectionManager()

@router.get("/conversations")
def get_user_conversations(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    conversations = db.query(Conversation).filter(
        (Conversation.user1_id == current_user.id) | (Conversation.user2_id == current_user.id)
    ).all()

    result = []
    for conv in conversations:
        target_user_id = conv.user2_id if conv.user1_id == current_user.id else conv.user1_id
        target_user = db.query(User).filter(User.id == target_user_id).first()
        last_msg = db.query(Message).filter(Message.conversation_id == conv.id).order_by(Message.timestamp.desc()).first()

        result.append({
            "id": conv.id,
            "user1_id": str(conv.user1_id),
            "user2_id": str(conv.user2_id),
            "participant_name": target_user.full_name if target_user else "Bilinmeyen Kullanıcı",
            "participant_image_url": None,
            "last_message": last_msg.text if last_msg else "Sohbet başlatıldı",
            "last_message_timestamp": last_msg.timestamp.strftime("%H:%M") if last_msg else "",
            "unread_count": 0,
            "is_online": str(target_user_id) in manager.active_connections
        })

    return result

@router.post("/conversations")
def create_or_get_conversation(target_user_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    conv = db.query(Conversation).filter(
        ((Conversation.user1_id == current_user.id) & (Conversation.user2_id == target_user_id)) |
        ((Conversation.user1_id == target_user_id) & (Conversation.user2_id == current_user.id))
    ).first()

    if not conv:
        conv = Conversation(user1_id=current_user.id, user2_id=target_user_id)
        db.add(conv)
        db.commit()
        db.refresh(conv)

    target_user = db.query(User).filter(User.id == target_user_id).first()
    return {
        "id": conv.id,
        "user1_id": str(conv.user1_id),
        "user2_id": str(conv.user2_id),
        "participant_name": target_user.full_name if target_user else "Bilinmeyen Kullanıcı",
        "participant_image_url": None,
        "last_message": "Sohbet başlatıldı",
        "last_message_timestamp": "",
        "unread_count": 0,
        "is_online": target_user_id in manager.active_connections
    }

@router.get("/conversations/{conversation_id}/messages", response_model=List[MessageResponse])
def get_messages(conversation_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    messages = db.query(Message).filter(Message.conversation_id == conversation_id).order_by(Message.timestamp.asc()).all()
    return messages

@router.post("/conversations/{conversation_id}/attachments", response_model=AttachmentResponse)
async def upload_attachment(
    conversation_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sohbet bulunamadı.")
    if conv.user1_id != current_user.id and conv.user2_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bu sohbete erişim yetkiniz yok.")

    MAX_SIZE = 10 * 1024 * 1024  # 10 MB
    contents = await file.read()
    if len(contents) > MAX_SIZE:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Dosya boyutu 10 MB'ı aşamaz.")

    ext = file.filename.rsplit('.', 1)[-1] if file.filename and '.' in file.filename else 'bin'
    filename = f"{uuid.uuid4()}.{ext}"
    file_path = f"static/chat/{filename}"

    with open(file_path, "wb") as f:
        f.write(contents)

    return AttachmentResponse(
        url=f"/static/chat/{filename}",
        mime_type=file.content_type or "application/octet-stream",
        file_name=file.filename or filename
    )

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = Query(...)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
    except Exception:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await manager.connect(websocket, user_id)
    db = SessionLocal()

    try:
        while True:
            data = await websocket.receive_json()
            target_user_id = data.get("target_user_id")
            text = data.get("text", "")
            conversation_id = data.get("conversation_id")
            attachment_url = data.get("attachment_url")
            attachment_type = data.get("attachment_type")

            new_msg = Message(
                conversation_id=conversation_id,
                sender_id=user_id,
                text=text,
                attachment_url=attachment_url,
                attachment_type=attachment_type
            )
            db.add(new_msg)
            db.commit()
            db.refresh(new_msg)

            message_data = {
                "id": new_msg.id,
                "conversation_id": new_msg.conversation_id,
                "sender_id": str(new_msg.sender_id),
                "text": new_msg.text,
                "timestamp": new_msg.timestamp.isoformat(),
                "status": new_msg.status,
                "attachment_url": new_msg.attachment_url,
                "attachment_type": new_msg.attachment_type
            }

            await websocket.send_json(message_data)

            if target_user_id in manager.active_connections:
                await manager.active_connections[target_user_id].send_json(message_data)

    except WebSocketDisconnect:
        manager.disconnect(user_id)
    finally:
        db.close()
