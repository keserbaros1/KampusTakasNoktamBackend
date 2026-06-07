from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models.user import User
from schemas.user import UserResponse
from routers.auth import get_current_user

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/me", response_model=UserResponse)
def read_users_me(current_user: User = Depends(get_current_user)):
    # get_current_user fonksiyonu arka planda token'ı kontrol etti 
    # ve başarılıysa bize doğrudan giriş yapan kullanıcıyı (current_user) getirdi.
    return current_user