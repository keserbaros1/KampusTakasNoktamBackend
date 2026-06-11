from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class Advertisement(Base):
    __tablename__ = "advertisements"

    id = Column(Integer, primary_key=True, index=True)
    seller_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    price = Column(Float, default=0.0)
    is_swap = Column(Boolean, default=False)
    condition = Column(String, nullable=False)
    category = Column(String, nullable=False)
    location = Column(String, nullable=False)
    # PostgreSQL'in Array tipi sayesinde birden fazla linki tek sütunda tutabiliriz
    image_urls = Column(ARRAY(String), default=[]) 
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    # İlanı çekerken sahibinin bilgilerine de kolayca ulaşmak için ilişki kuruyoruz
    seller = relationship("User", backref="advertisements")

    @property
    def seller_full_name(self):
        return self.seller.full_name if self.seller else None