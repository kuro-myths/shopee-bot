FROM python:3.12-slim

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .

ENV CHECKER_ENABLED=true \
    DATABASE_URL=sqlite:////data/pricedrop.db \
    PYTHONUNBUFFERED=1
EXPOSE 8000

# Railway menyuntikkan $PORT; fallback ke 8000 untuk lokal/docker-compose
CMD ["sh", "-c", "mkdir -p /data && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
