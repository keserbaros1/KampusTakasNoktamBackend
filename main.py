import os
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from database import engine, Base
import models.user 
import models.advertisement
import models.chat
from routers import auth, users, advertisements, chat

# Veritabanı tablolarını oluştur (Eğer sunucuda yoksa sıfırdan çizer)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="CampusSwap API",
    description="Kampüs içi takas ve ikinci el platformu arka yüzü",
    version="1.0.0"
)

# RATE LIMITING
limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# HATA YAKALAMA
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # Pydantic'in karmaşık hata listesinden sadece ilk hatanın mesajını alıyoruz
    error_msg = exc.errors()[0].get("msg")
    
    # Özel "Value error, " takısını temizleyelim (Pydantic bazen başına ekler)
    if error_msg.startswith("Value error, "):
        error_msg = error_msg.replace("Value error, ", "")

    # Ön yüzün beklediği o standart formata çeviriyoruz
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": error_msg},
    )

# Fotoğrafların kaydedileceği klasörü otomatik oluştur
os.makedirs("static/images", exist_ok=True)

# /static URL'sine gelen istekleri static klasörüne yönlendir
app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(advertisements.router)
app.include_router(chat.router)

@app.get("/")
def root():
    return {"message": "CampusSwap API tıkır tıkır çalışıyor!"}