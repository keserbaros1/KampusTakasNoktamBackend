from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from database import get_db
from models.user import User
from models.advertisement import Advertisement
from schemas.user import UserResponse, SellerProfileResponse, UserUpdate
from routers.auth import get_current_user

router = APIRouter(prefix="/users", tags=["Users"])

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
