import shutil
import uuid
import os
from typing import List, Optional
from fastapi import APIRouter, Depends, status, Query, File, UploadFile, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models.advertisement import Advertisement
from models.user import User
from schemas.advertisement import AdvertisementCreate, AdvertisementResponse, AdvertisementUpdate, ConditionEnum, CategoryEnum
from routers.auth import get_current_user

router = APIRouter(prefix="/ads", tags=["Advertisements"])

@router.post("/", response_model=AdvertisementResponse, status_code=status.HTTP_201_CREATED)
def create_ad(ad: AdvertisementCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Pydantic modelindeki verileri al ve seller_id'yi giriş yapan kullanıcıdan çek
    new_ad = Advertisement(
        **ad.model_dump(),
        seller_id=current_user.id
    )
    db.add(new_ad)
    db.commit()
    db.refresh(new_ad)
    return new_ad


# ─── Admin: tüm ilanlar (auth yok) ───────────────────────────────────────────
@router.get("/", response_model=List[AdvertisementResponse])
def get_ads(
    category: Optional[CategoryEnum] = Query(None),
    condition: Optional[ConditionEnum] = Query(None),
    min_price: Optional[float] = Query(None, description="Minimum fiyat"),
    max_price: Optional[float] = Query(None, description="Maksimum fiyat"),
    is_swap: Optional[bool] = Query(None, description="Sadece takasa açık olanlar (true/false)"),
    db: Session = Depends(get_db)
):
    query = db.query(Advertisement).filter(Advertisement.is_active == True)

    if category:
        query = query.filter(Advertisement.category == category.value)
    if condition:
        query = query.filter(Advertisement.condition == condition.value)
    if min_price is not None:
        query = query.filter(Advertisement.price >= min_price)
    if max_price is not None:
        query = query.filter(Advertisement.price <= max_price)
    if is_swap is not None:
        query = query.filter(Advertisement.is_swap == is_swap)
    return query.all()


# ─── Keşfet: kendi ilanları hariç aktif ilanlar ──────────────────────────────
@router.get("/discover", response_model=List[AdvertisementResponse])
def discover_ads(
    category: Optional[CategoryEnum] = Query(None),
    condition: Optional[ConditionEnum] = Query(None),
    min_price: Optional[float] = Query(None),
    max_price: Optional[float] = Query(None),
    is_swap: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Advertisement).filter(
        Advertisement.is_active == True,
        Advertisement.seller_id != current_user.id
    )
    if category:
        query = query.filter(Advertisement.category == category.value)
    if condition:
        query = query.filter(Advertisement.condition == condition.value)
    if min_price is not None:
        query = query.filter(Advertisement.price >= min_price)
    if max_price is not None:
        query = query.filter(Advertisement.price <= max_price)
    if is_swap is not None:
        query = query.filter(Advertisement.is_swap == is_swap)
    return query.all()


# ─── İlanlarım: sadece giriş yapan kullanıcının ilanları ─────────────────────
@router.get("/my-ads", response_model=List[AdvertisementResponse])
def get_my_ads(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(Advertisement).filter(
        Advertisement.seller_id == current_user.id
    ).order_by(Advertisement.created_at.desc()).all()



@router.get("/{ad_id}", response_model=AdvertisementResponse)
def get_ad(ad_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    ad = db.query(Advertisement).filter(Advertisement.id == ad_id).first()
    if not ad:
        raise HTTPException(status_code=404, detail="İlan bulunamadı.")
    return ad


@router.post("/{ad_id}/images", response_model=AdvertisementResponse)
def upload_ad_images(
    ad_id: int, 
    files: List[UploadFile] = File(...), 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    # İlanı veritabanında bul ve giriş yapan kişiye ait olup olmadığını kontrol et
    ad = db.query(Advertisement).filter(Advertisement.id == ad_id).first()
    
    if not ad:
        raise HTTPException(status_code=404, detail="İlan bulunamadı.")
    
    if ad.seller_id != current_user.id:
        raise HTTPException(status_code=403, detail="Sadece kendi ilanınıza fotoğraf yükleyebilirsiniz.")

    uploaded_urls = []
    
    # Gelen her bir fotoğraf için döngü
    for file in files:
        # Dosya uzantısını alıp, benzersiz (UUID) bir dosya ismi oluştur
        file_extension = file.filename.split('.')[-1]
        unique_filename = f"{uuid.uuid4()}.{file_extension}"
        file_path = f"static/images/{unique_filename}"

        # Dosyayı sunucuya (bilgisayara) kaydet
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Veritabanına kaydedilecek URL yolunu listeye ekle
        uploaded_urls.append(f"/static/images/{unique_filename}")

    # Mevcut fotoğrafların üzerine yenilerini ekle ve veritabanını güncelle
    # (SQLAlchemy'de listeyi güncellerken atama yapmamız gerekir)
    ad.image_urls = ad.image_urls + uploaded_urls
    db.commit()
    db.refresh(ad)
    
    return ad

@router.put("/{ad_id}", response_model=AdvertisementResponse)
def update_ad(
    ad_id: int, 
    ad_update: AdvertisementUpdate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    # İlanı bul
    ad = db.query(Advertisement).filter(Advertisement.id == ad_id).first()
    
    if not ad:
        raise HTTPException(status_code=404, detail="İlan bulunamadı.")
    
    # Güvenlik Kontrolü: İlan başkasınınsa işlem yaptırma
    if ad.seller_id != current_user.id:
        raise HTTPException(status_code=403, detail="Sadece kendi ilanınızı güncelleyebilirsiniz.")

    # Gönderilen verilerde 'None' olmayanları (yani güncellenmek istenenleri) al
    update_data = ad_update.model_dump(exclude_unset=True)
    
    # Modelin özelliklerini döngüyle güncelle
    for key, value in update_data.items():
        setattr(ad, key, value)

    db.commit()
    db.refresh(ad)
    return ad

@router.delete("/{ad_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ad(
    ad_id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    ad = db.query(Advertisement).filter(Advertisement.id == ad_id).first()
    
    if not ad:
        raise HTTPException(status_code=404, detail="İlan bulunamadı.")
        
    if ad.seller_id != current_user.id:
        raise HTTPException(status_code=403, detail="Sadece kendi ilanınızı silebilirsiniz.")

    db.delete(ad)
    db.commit()
    # 204 No Content döndüğümüz için return yazmamıza gerek yok
