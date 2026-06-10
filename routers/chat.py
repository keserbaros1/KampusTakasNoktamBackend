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

# --- 1. Kullanıcının TÜM sohbetlerini listele (Frontend'in GET isteği için) ---
@router.get("/conversations")
def get_user_conversations(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # İçinde bulunduğumuz sohbetleri getir
    conversations = db.query(Conversation).filter(
        (Conversation.user1_id == current_user.id) | (Conversation.user2_id == current_user.id)
    ).all()
    
    result = []
    for conv in conversations:
        # Karşı tarafı bul
        target_user_id = conv.user2_id if conv.user1_id == current_user.id else conv.user1_id
        target_user = db.query(User).filter(User.id == target_user_id).first()
        
        # Bu sohbetteki son mesajı bul
        last_msg = db.query(Message).filter(Message.conversation_id == conv.id).order_by(Message.timestamp.desc()).first()
        
        # Frontend'in 'ChatConversation' modelinde tam olarak beklediği anahtarlar:
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

# --- 2. Yeni sohbet başlat veya var olanı getir (Frontend'in POST isteği için) ---
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

    # Sohbet yeni bile olsa frontend aynı zengin JSON yapısını bekliyor
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
            db.refresh(new_msg) # ID ve Timestamp değerlerinin dolması için yenile
            
            # 2. Mesajı tam bir JSON objesi (Sözlük) haline getir
            message_data = {
                "id": new_msg.id,
                "conversation_id": new_msg.conversation_id,
                "sender_id": str(new_msg.sender_id),
                "text": new_msg.text,
                "timestamp": new_msg.timestamp.isoformat(),
                "status": new_msg.status
            }
            
            # 3. Gönderene kendi mesajını tam obje olarak geri dön (UI'da anında görünmesi için)
            await websocket.send_json(message_data)
            
            # 4. Karşı taraf aktifse ona da aynı tam objeyi ilet
            if target_user_id in manager.active_connections:
                await manager.active_connections[target_user_id].send_json(message_data)
                
    except WebSocketDisconnect:
        manager.disconnect(user_id)
    finally:
        db.close()