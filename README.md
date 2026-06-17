# KampusTakasNoktam Backend API Dokümantasyonu

Temel URL: https://kampustakasnoktam.keserbaros.com/
Ortak Kural: `/auth/register`, `/auth/login` ve `GET /ads` hariç tüm isteklere Header olarak `Authorization: Bearer <TOKEN>` eklenmelidir. Hatalar her zaman `{"detail": "Hata mesajı"}` formatında döner.

> **Rate limit:** Tüm uçlar için varsayılan limit dakikada 60 istektir. Aşıldığında 429 döner.

---

## 1. Kimlik Doğrulama (Auth)

### Kayıt Ol
- `POST /auth/register`
- Not: Yalnızca `.edu.tr` uzantılı e-postalar kabul edilir. `university` alanı e-posta alan adından otomatik türetilir.
- Gövde (JSON):
  ```json
  {
    "full_name": "İsim",
    "email": "ornek@edu.tr",
    "password": "sifre"
  }
  ```
- Yanıt (201): `UserResponse`

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

### Profilimi Güncelle
- `PUT /users/me`
- Auth: Bearer token
- Gövde (JSON): sadece değişen alanlar. **`university` güncellenemez** (kayıtta e-postadan türetilir).
  ```json
  {
    "phone": "+905321234567",
    "city": "İstanbul"
  }
  ```
- Kurallar:
  - `phone` gönderilirse **`+905XXXXXXXXX`** formatında olmalıdır, aksi halde 422 döner.
- Yanıt (200): güncellenmiş `UserResponse`

### Profil Fotoğrafı (Avatar) Yükle
- `POST /users/me/avatar`
- Auth: Bearer token
- Gövde: `multipart/form-data`
  - `avatar`: tek görsel dosyası
- Kurallar:
  - İzinli formatlar: **JPEG, PNG, WebP** (aksi halde 415)
  - Maksimum boyut: **5 MB** (aşılırsa 413)
- Yanıt (200): güncellenmiş `UserResponse` (yeni `avatar_url` ile)

### Satıcı Profili Getir
- `GET /users/{user_id}`
- Parametre:
  - `user_id`: UUID
- Yanıt (200): `SellerProfileResponse`

> `SellerProfileResponse.ads`, satıcının **aktif** ilanlarını `AdvertisementResponse` formatında döner.
> İlanlar `Advertisement.seller_id == user_id` ile filtrelenir.

---

## 3. İlanlar (Advertisements)

> **Önemli:** `category` ve `condition` alanları artık serbest metin değil, sabit **enum kodu** kabul eder (büyük harf, İngilizce). Geçersiz değer 422 döndürür. Geçerli değerler için [Enum Değerleri](#enum-değerleri) bölümüne bakın.

### İlan Listele — Genel (Filtreli)
- `GET /ads`
- Auth: **gerekmez** (herkese açık)
- Sadece aktif ilanları döner.
- Opsiyonel URL parametreleri:
  - `category` — enum kodu (örn. `ELECTRONICS`)
  - `condition` — enum kodu (örn. `GOOD`)
  - `min_price`
  - `max_price`
  - `is_swap` — `true`/`false`
- Yanıt (200): `AdvertisementResponse[]`

### İlan Listele — Keşfet
- `GET /ads/discover`
- Auth: Bearer token
- Aktif ilanları döner, **kendi ilanlarınız hariç**.
- Filtre parametreleri `GET /ads` ile aynıdır.
- Yanıt (200): `AdvertisementResponse[]`

### İlanlarım
- `GET /ads/my-ads`
- Auth: Bearer token
- Sadece giriş yapan kullanıcının ilanlarını (oluşturma tarihine göre yeniden eskiye) döner.
- Yanıt (200): `AdvertisementResponse[]`

### Tek İlan Getir
- `GET /ads/{ad_id}`
- Auth: Bearer token
- Yanıt (200): `AdvertisementResponse`
- Bulunamazsa 404.

### Yeni İlan Oluştur
- `POST /ads`
- Auth: Bearer token
- Gövde (JSON):
  ```json
  {
    "title": "Hesap Makinesi",
    "description": "Az kullanılmış bilimsel hesap makinesi",
    "price": 150.0,
    "is_swap": false,
    "condition": "GOOD",
    "category": "STUDENT_ESSENTIALS",
    "location": "Merkez Kampüs"
  }
  ```
- Yanıt (201): `AdvertisementResponse`

### İlana Fotoğraf Yükle
- `POST /ads/{ad_id}/images`
- Auth: Bearer token (sadece ilan sahibi)
- Gövde: `multipart/form-data`
  - `files`: bir veya birden fazla görsel
- Yanıt (200): güncellenmiş `AdvertisementResponse`

### İlan Güncelle
- `PUT /ads/{ad_id}`
- Auth: Bearer token (sadece ilan sahibi)
- Gövde (JSON): sadece değişen alanlar (`condition`/`category` enum kodu olmalı)
  ```json
  {
    "price": 120.0,
    "condition": "FAIR"
  }
  ```
- Yanıt (200): güncellenmiş `AdvertisementResponse`

### İlan Sil
- `DELETE /ads/{ad_id}`
- Auth: Bearer token (sadece ilan sahibi)
- Yanıt (204): içerik yok

---

## 4. Mesajlaşma (Chat)

### Sohbetlerimi Listele
- `GET /chat/conversations`
- Auth: Bearer token
- Yanıt (200): zenginleştirilmiş sohbet dizisi
  ```json
  [
    {
      "id": 1,
      "user1_id": "uuid",
      "user2_id": "uuid",
      "participant_name": "Karşı Taraf",
      "participant_image_url": null,
      "last_message": "Son mesaj metni",
      "last_message_timestamp": "14:30",
      "unread_count": 0,
      "is_online": true
    }
  ]
  ```

### Sohbet Odası Başlat / Bul
- `POST /chat/conversations?target_user_id={uuid}`
- Auth: Bearer token
- Yanıt (200): yukarıdakiyle aynı yapıda tek sohbet objesi.

### Geçmiş Mesajları Çek
- `GET /chat/conversations/{conversation_id}/messages`
- Auth: Bearer token
- Yanıt (200): `MessageResponse[]`

### Sohbete Dosya/Ek Yükle
- `POST /chat/conversations/{conversation_id}/attachments`
- Auth: Bearer token (sadece sohbetin katılımcısı; değilse 403)
- Gövde: `multipart/form-data`
  - `file`: tek dosya
- Kurallar:
  - Maksimum boyut: **10 MB** (aşılırsa 413)
- Yanıt (200): `AttachmentResponse`
  ```json
  {
    "url": "/static/chat/<dosya>.png",
    "mime_type": "image/png",
    "file_name": "orijinal_ad.png"
  }
  ```
- Akış: Önce bu uçtan dosyayı yükleyin; dönen `url` ve `mime_type` değerlerini WebSocket mesajında `attachment_url` ve `attachment_type` olarak gönderin.

### Canlı Sohbet Bağlantısı
- `WS /chat/ws?token={token}`
- Giden mesaj (JSON):
  ```json
  {
    "target_user_id": "uuid",
    "conversation_id": 1,
    "text": "Selam",
    "attachment_url": "/static/chat/<dosya>.png",
    "attachment_type": "image/png"
  }
  ```
  - `text` opsiyoneldir (sadece ek dosyalı mesaj gönderilebilir).
  - `attachment_url` / `attachment_type` opsiyoneldir.
- Gelen mesajlar anında JSON formatında düşer (gönderene kendi mesajı da geri döner). Yapı `MessageResponse` ile aynıdır.

---

## 5. Model ve Yanıt Yapıları

### `UserResponse`
- `id`
- `full_name`
- `email`
- `university`
- `phone` *(nullable)*
- `city` *(nullable)*
- `avatar_url` *(nullable)*
- `member_since`
- `is_email_verified`

### `SellerProfileResponse`
- `id`
- `full_name`
- `university`
- `city` *(nullable)*
- `avatar_url` *(nullable)*
- `phone` *(nullable)*
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
- `condition` — enum kodu
- `category` — enum kodu
- `location`
- `image_urls`
- `seller_id`
- `seller_full_name`
- `created_at`
- `is_active`

### `MessageResponse`
- `id`
- `conversation_id`
- `sender_id`
- `text`
- `timestamp`
- `status` — `SENT` | `DELIVERED` | `READ`
- `attachment_url` *(nullable)*
- `attachment_type` *(nullable)*

### `AttachmentResponse`
- `url`
- `mime_type`
- `file_name`

### Enum Değerleri

`condition` (ürün durumu):

| Kod | Anlam (öneri) |
| --- | --- |
| `EXCELLENT` | Mükemmel |
| `GOOD` | İyi |
| `FAIR` | Orta |
| `POOR` | Kötü |
| `DAMAGED` | Hasarlı |

`category` (kategori):

| Kod | Anlam (öneri) |
| --- | --- |
| `HOUSEHOLD_GOODS` | Ev Eşyası |
| `TEXTBOOKS` | Ders Kitapları |
| `STUDENT_ESSENTIALS` | Öğrenci İhtiyaçları |
| `ELECTRONICS` | Elektronik |
| `CLOTHING` | Giyim |
| `SPORTS` | Spor |
| `OTHER` | Diğer |

> Görünen Türkçe etiketleri frontend tarafında eşleyin; API'ye her zaman kodu gönderin.

---

## 6. Frontend İçin Kullanım Önerisi

- Satıcı profili sayfası için `GET /users/{user_id}` çağrısını kullan; yanıttaki `ads` alanı sayesinde satıcının ilanlarını aynı çağrıda alırsın.
- Profil fotoğrafı için yanıtlardaki `avatar_url` alanını kullan (eski `profile_image_url` adı kaldırıldı).
- `category`/`condition` için kullanıcıya Türkçe etiket göster, API'ye enum kodunu gönder.
- Ana akışta `GET /ads/discover` (kendi ilanları hariç), profil sayfasında `GET /ads/my-ads` kullan.
- Dosya/foto yüklemelerinde boyut ve format limitlerini frontend'de de doğrula (avatar 5 MB & JPEG/PNG/WebP, chat eki 10 MB).
