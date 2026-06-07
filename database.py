# database.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from dotenv import load_dotenv

# .env dosyasındaki değişkenleri yükle
load_dotenv()

SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

# Engine oluştur
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Veritabanı işlemleri için Session sınıfı
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Modellerimizin miras alacağı Base sınıfı
Base = declarative_base()

# Dependency (Endpoint'lerde her istekte yeni bir DB oturumu açıp kapatmak için)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()