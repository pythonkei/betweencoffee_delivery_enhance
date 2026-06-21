FROM python:3.11-slim

WORKDIR /app

# 安裝系統依賴
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libpq-dev \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# 複製專案檔案
COPY . /app/

# 安裝 Python 依賴
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 收集靜態檔案
RUN python manage.py collectstatic --noinput

# 複製 media 檔案到 staticfiles
RUN mkdir -p /app/staticfiles/media && \
    cp -r /app/media/* /app/staticfiles/media/ 2>/dev/null || echo "No media files to copy"

# 暴露端口
EXPOSE 8000

# 啟動命令
# 🔧 修復：使用 daphne 替代 gunicorn 以支援 WebSocket
# gunicorn 只能處理 WSGI（HTTP），無法處理 WebSocket 請求
# daphne 是 Django Channels 的 ASGI 伺服器，支援 HTTP + WebSocket
CMD python manage.py migrate --noinput && \
    python manage.py setup_social_apps && \
    python manage.py cleanup_duplicate_user && \
    daphne -b 0.0.0.0 -p $PORT betweencoffee_delivery.asgi:application
