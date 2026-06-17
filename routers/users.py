import uuid
import shutil
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, status
from sqlalchemy.orm import Session
from uuid import UUID
from database import get_db
from models.user import User
from models.advertisement import Advertisement
from schemas.user import UserResponse, SellerProfileResponse, UserUpdate
from routers.auth import get_current_user

router = APIRouter(prefix="/users", tags=["Users"])

AVATAR_ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}
AVATAR_MAX_SIZE = 5 * 1024 * 1024  # 5 MB

@router.get("/me", response_model=UserResponse)
def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.put("/me", response_model=UserResponse)
def update_users_me(
    update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    update_data = update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(current_user, key, value)
    db.commit()
    db.refresh(current_user)
    return current_user

@router.post("/me/avatar", response_model=UserResponse)
async def upload_avatar(
    avatar: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if avatar.content_type not in AVATAR_ALLOWED_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Desteklenmeyen dosya formatı. JPEG, PNG veya WebP yükleyin."
        )

    contents = await avatar.read()
    if len(contents) > AVATAR_MAX_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Dosya boyutu 5 MB'ı aşamaz."
        )

    ext = avatar.filename.rsplit('.', 1)[-1] if avatar.filename and '.' in avatar.filename else 'jpg'
    filename = f"{uuid.uuid4()}.{ext}"
    file_path = f"static/images/avatars/{filename}"

    with open(file_path, "wb") as f:
        f.write(contents)

    current_user.profile_image_url = f"/static/images/avatars/{filename}"
    db.commit()
    db.refresh(current_user)
    return current_user

@router.get("/{user_id}", response_model=SellerProfileResponse)
def read_seller_profile(user_id: UUID, db: Session = Depends(get_db)):
    seller = db.query(User).filter(User.id == user_id).first()
    if not seller:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Satıcı bulunamadı.")

    seller_ads = db.query(Advertisement).filter(
        Advertisement.seller_id == user_id,
        Advertisement.is_active == True
    ).all()

    return {
        "id": seller.id,
        "full_name": seller.full_name,
        "university": seller.university,
        "city": seller.city,
        "profile_image_url": seller.profile_image_url,
        "phone": seller.phone,
        "rating": seller.rating,
        "total_sales": seller.total_sales,
        "total_reviews": seller.total_reviews,
        "member_since": seller.member_since,
        "is_email_verified": seller.is_email_verified,
        "ads": seller_ads,
    }
