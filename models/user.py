import uuid
from sqlalchemy import Column, String, Boolean, Float, Integer, DateTime
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    university = Column(String, nullable=False)
    member_since = Column(DateTime, default=datetime.utcnow)
    profile_image_url = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    city = Column(String(100), nullable=True)
    rating = Column(Float, default=0.0)
    total_sales = Column(Integer, default=0)
    total_reviews = Column(Integer, default=0)
    is_email_verified = Column(Boolean, default=False)