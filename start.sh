#!/bin/bash
set -e

# 等待数据库就绪（如果需要）
# 运行数据库迁移
echo "Running database migrations..."
python manage.py migrate --noinput

# 收集静态文件（确保在构建时已经完成）
echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

# 启动Gunicorn
echo "Starting Gunicorn..."
exec gunicorn betweencoffee_delivery.wsgi:application \
    --bind 0.0.0.0:$PORT \
    --workers 3 \
    --worker-class sync \
    --timeout 120 \
    --access-logfile -