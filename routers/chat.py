import jwt
from typing import List, Dict
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, status, Query
from sqlalchemy.orm import Session
from database import get_db, SessionLocal
from models.chat import Conversation, Message
from models.user import User
from schemas.chat import ConversationResponse, MessageResponse
from routers.auth import get_current_user, SECRET_KEY, ALGORITHM

router = APIRouter(prefix="/chat", tags=["Chat"])

# Aktif WebSocket bağlantılarını yönetecek sınıf
class ConnectionManager:
    def __init__(self):
        # Hangi user_id'nin hangi WebSocket hattına bağlı olduğunu tutuyoruz
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        self.active_connections[user_id] = websocket

    def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]

manager = ConnectionManager()

# 1. İki kişi arasında sohbet odası oluştur veya varsa getir (Normal REST)
@router.post("/conversations", response_model=ConversationResponse)
def create_or_get_conversation(target_user_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    conv = db.query(Conversation).filter(
        ((Conversation.user1_id == current_user.id) & (Conversation.user2_id == target_user_id)) |
        ((Conversation.user1_id == target_user_id) & (Conversation.user2_id == current_user.id))
    ).first()

    if conv:
        return conv

    new_conv = Conversation(user1_id=current_user.id, user2_id=target_user_id)
    db.add(new_conv)
    db.commit()
    db.refresh(new_conv)
    return new_conv

# 2. Eski mesajları listele (Normal REST)
@router.get("/conversations/{conversation_id}/messages", response_model=List[MessageResponse])
def get_messages(conversation_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    messages = db.query(Message).filter(Message.conversation_id == conversation_id).order_by(Message.timestamp.asc()).all()
    return messages

# 3. Anlık Mesajlaşma Tüneli (WebSocket)
@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = Query(...)):
    # WebSocket için manuel token doğrulaması
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
            # Kullanıcıdan gelen JSON formatındaki mesajı bekle
            data = await websocket.receive_json()
            target_user_id = data.get("target_user_id")
            text = data.get("text")
            conversation_id = data.get("conversation_id")
            
            # 1. Mesajı veritabanına kaydet
            new_msg = Message(
                conversation_id=conversation_id, 
                sender_id=user_id, 
                text=text
            )
            db.add(new_msg)
            db.commit()
            
            # 2. Gönderene "Mesajın iletildi" bilgisini dön
            await websocket.send_json({"status": "SENT", "text": text})
            
            # 3. Eğer karşı taraf o an uygulamadaysa (aktif bağlantısı varsa) mesajı anında ekranına düşür
            if target_user_id in manager.active_connections:
                await manager.active_connections[target_user_id].send_json({
                    "sender_id": user_id,
                    "text": text,
                    "conversation_id": conversation_id
                })
                
    except WebSocketDisconnect:
        manager.disconnect(user_id)
    finally:
        db.close()