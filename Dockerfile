FROM python:3.11-slim

WORKDIR /app

# 安裝系統依賴
# cargo（Rust 套件管理器）用於編譯 rpds-py 等需要 Rust 的套件
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libpq-dev \
    gcc \
    python3-dev \
    cargo \
    && rm -rf /var/lib/apt/lists/*

# 🔧 強制清除 Docker layer cache：每次部署都重新複製專案檔案
# 使用 build arg 確保 COPY 步驟不被 cache
ARG CACHEBUST=1

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
