from pydantic import BaseModel, EmailStr, Field, field_validator
from uuid import UUID
from datetime import datetime

class UserCreate(BaseModel):
    full_name: str
    email: EmailStr
    password: str = Field(..., max_length=50)

    @field_validator('email')
    @classmethod
    def check_edu_tr(cls, v):
        if not v.endswith('.edu.tr'):
            raise ValueError('Sisteme yalnızca .edu.tr uzantılı e-posta adresleri ile kayıt olunabilir.')
        return v

class UserResponse(BaseModel):
    id: UUID
    full_name: str
    email: EmailStr
    university: str
    member_since: datetime
    is_email_verified: bool

    class Config:
        from_attributes = True