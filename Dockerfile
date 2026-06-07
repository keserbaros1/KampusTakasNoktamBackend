FROM python:3.11-slim

# Çalışma dizinini ayarla
WORKDIR /app

# Gerekli paketleri kopyala ve kur
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Proje dosyalarını kopyala
COPY . .

# FastAPI'yi başlat
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]