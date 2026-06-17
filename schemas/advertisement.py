from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from uuid import UUID
from enum import Enum

class ConditionEnum(str, Enum):
    EXCELLENT = "EXCELLENT"
    GOOD = "GOOD"
    FAIR = "FAIR"
    POOR = "POOR"
    DAMAGED = "DAMAGED"

class CategoryEnum(str, Enum):
    HOUSEHOLD_GOODS = "HOUSEHOLD_GOODS"
    TEXTBOOKS = "TEXTBOOKS"
    STUDENT_ESSENTIALS = "STUDENT_ESSENTIALS"
    ELECTRONICS = "ELECTRONICS"
    CLOTHING = "CLOTHING"
    SPORTS = "SPORTS"
    OTHER = "OTHER"

class AdvertisementBase(BaseModel):
    title: str
    description: str
    price: Optional[float] = 0.0
    is_swap: bool = False
    condition: ConditionEnum
    category: CategoryEnum
    location: str
    image_urls: List[str] = []

class AdvertisementCreate(AdvertisementBase):
    pass

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
    condition: Optional[ConditionEnum] = None
    category: Optional[CategoryEnum] = None
    location: Optional[str] = None
    is_active: Optional[bool] = None
