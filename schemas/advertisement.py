from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from uuid import UUID

# Ortak alanları Base modelde topluyoruz
class AdvertisementBase(BaseModel):
    title: str
    description: str
    price: Optional[float] = 0.0
    is_swap: bool = False
    condition: str
    category: str
    location: str
    image_urls: List[str] = []

# Yeni ilan oluşturulurken kullanıcıdan istenecek veriler
class AdvertisementCreate(AdvertisementBase):
    pass

# İlan listelenirken dışarıya dönülecek veriler
class AdvertisementResponse(AdvertisementBase):
    id: int
    seller_id: UUID
    seller_full_name: str
    created_at: datetime
    is_active: bool

    class Config:
        from_attributes = True

class AdvertisementUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    is_swap: Optional[bool] = None
    condition: Optional[str] = None
    category: Optional[str] = None
    location: Optional[str] = None
    is_active: Optional[bool] = None