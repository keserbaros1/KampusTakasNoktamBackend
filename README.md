# KampusTakasNoktam Backend API Dokümantasyonu

Temel URL: https://kampustakasnoktam.keserbaros.com/
Ortak Kural: /auth/register ve /auth/login hariç tüm isteklere Header olarak Authorization: Bearer <TOKEN> eklenmelidir. Hatalar her zaman {"detail": "Hata mesajı"} formatında döner.

## 1. Kimlik Doğrulama (Auth)

### Kayıt Ol
- `POST /auth/register`
- Gövde (JSON):
  ```json
  {
    "full_name": "İsim",
    "email": "ornek@edu.tr",
    "password": "sifre"
  }
  ```
- Yanıt (201):
  ```json
  {
    "id": "uuid",
    "full_name": "İsim",
    "email": "ornek@edu.tr",
    "university": "Ornek",
    "member_since": "2026-06-11T...",
    "is_email_verified": false
  }
  ```

### Giriş Yap
- `POST /auth/login`
- Gövde (Form Data):
  - `username`: e-posta
  - `password`
- Yanıt (200):
  ```json
  {
    "access_token": "eyJhb...",
    "token_type": "bearer"
  }
  ```

---

## 2. Kullanıcı Profil (Users)

### Profilimi Getir
- `GET /users/me`
- Auth: Bearer token
- Yanıt (200): `UserResponse`
  - `id`
  - `full_name`
  - `email`
  - `university`
  - `member_since`
  - `is_email_verified`

### Satıcı Profili Getir
- `GET /users/{user_id}`
- Parametre:
  - `user_id`: UUID
- Yanıt (200): `SellerProfileResponse`
  - `id`
  - `full_name`
  - `university`
  - `profile_image_url`
  - `phone`
  - `rating`
  - `total_sales`
  - `total_reviews`
  - `member_since`
  - `is_email_verified`
  - `ads` — satıcının ilanları

> `SellerProfileResponse.ads`, aktif ilanları `AdvertisementResponse` formatında döner.
> Satıcının ilanları `Advertisement.seller_id == user_id` ile filtrelenir.

---

## 3. İlanlar (Advertisements)

### İlan Listele (Filtreli)
- `GET /ads`
- Opsiyonel URL parametreleri:
  - `category`
  - `condition`
  - `min_price`
  - `max_price`
  - `is_swap`
- Yanıt (200): `AdvertisementResponse[]`

### Yeni İlan Oluştur
- `POST /ads`
- Auth: Bearer token
- Gövde (JSON):
  ```json
  {
    "title": "Kalem",
    "description": "Uçlu",
    "price": 15.5,
    "is_swap": false,
    "condition": "Az Kullanılmış",
    "category": "Kırtasiye",
    "location": "Kantin"
  }
  ```
- Yanıt (201): `AdvertisementResponse`

### İlana Fotoğraf Yükle
- `POST /ads/{ad_id}/images`
- Auth: Bearer token
- Gövde: `multipart/form-data`
  - `files`: bir veya birden fazla görsel
- Yanıt (200): güncellenmiş `AdvertisementResponse`

### İlan Güncelle
- `PUT /ads/{ad_id}`
- Auth: Bearer token
- Gövde (JSON): sadece değişen alanlar
  ```json
  {
    "price": 20.0
  }
  ```
- Yanıt (200): güncellenmiş `AdvertisementResponse`

### İlan Sil
- `DELETE /ads/{ad_id}`
- Auth: Bearer token
- Yanıt (204): içerik yok

---

## 4. Mesajlaşma (Chat)

### Sohbet Odası Başlat / Bul
- `POST /chat/conversations?target_user_id={uuid}`
- Yanıt (200): sohbet odası objesi
  ```json
  {
    "id": 1,
    "user1_id": "uuid",
    "user2_id": "uuid"
  }
  ```

### Geçmiş Mesajları Çek
- `GET /chat/conversations/{conversation_id}/messages`
- Yanıt (200): mesaj dizisi

### Canlı Sohbet Bağlantısı
- `WS /chat/ws?token={token}`
- Giden mesaj (JSON):
  ```json
  {
    "target_user_id": "uuid",
    "text": "Selam",
    "conversation_id": 1
  }
  ```
- Gelen mesajlar anında JSON formatında düşer

---

## 5. Model ve Yanıt Yapıları

### `UserResponse`
- `id`
- `full_name`
- `email`
- `university`
- `member_since`
- `is_email_verified`

### `SellerProfileResponse`
- `id`
- `full_name`
- `university`
- `profile_image_url`
- `phone`
- `rating`
- `total_sales`
- `total_reviews`
- `member_since`
- `is_email_verified`
- `ads: AdvertisementResponse[]`

### `AdvertisementResponse`
- `id`
- `title`
- `description`
- `price`
- `is_swap`
- `condition`
- `category`
- `location`
- `image_urls`
- `seller_id`
- `created_at`
- `is_active`

---

## 6. Frontend İçin Kullanım Önerisi

- Satıcı profili sayfası için `GET /users/{user_id}` çağrısını kullan.
- Yanıttaki `ads` alanı sayesinde satıcının ilanlarını aynı çağrıda alabilirsin.
- Satıcı ilanlarını filtrelerken `seller_id` kullan: `Advertisement.seller_id == user_id`.
- Profil ve ürün listesi gösterimini tek endpoint üzerinden yaparak frontend performansını artırabilirsin.
