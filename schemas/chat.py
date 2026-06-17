from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID

class MessageResponse(BaseModel):
    id: int
    conversation_id: int
    sender_id: UUID
    text: str
    timestamp: datetime
    status: str
    attachment_url: Optional[str] = None
    attachment_type: Optional[str] = None

    class Config:
        from_attributes = True

class ConversationResponse(BaseModel):
    id: int
    user1_id: UUID
    user2_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True

class AttachmentResponse(BaseModel):
    url: str
    mime_type: str
    file_name: str
