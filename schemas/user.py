import re
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from schemas.advertisement import AdvertisementResponse

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

class UserUpdate(BaseModel):
    # university kasıtlı olarak yok: kayıtta .edu.tr e-postasından türetiliyor,
    # kullanıcı tarafından serbestçe değiştirilememeli.
    phone: Optional[str] = None
    city: Optional[str] = None

    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v):
        if v is not None and not re.match(r'^\+905[0-9]{9}$', v):
            raise ValueError('Telefon numarası +905XXXXXXXXX formatında olmalıdır (örn: +905321234567).')
        return v

class UserResponse(BaseModel):
    id: UUID
    full_name: str
    email: EmailStr
    university: str
    phone: Optional[str] = None
    city: Optional[str] = None
    avatar_url: Optional[str] = None
    member_since: datetime
    is_email_verified: bool

    class Config:
        from_attributes = True

class SellerProfileResponse(BaseModel):
    id: UUID
    full_name: str
    university: str
    city: Optional[str] = None
    avatar_url: str | None = None
    phone: str | None = None
    rating: float
    total_sales: int
    total_reviews: int
    member_since: datetime
    is_email_verified: bool
    ads: List[AdvertisementResponse] = Field(default_factory=list)

    class Config:
        from_attributes = True
