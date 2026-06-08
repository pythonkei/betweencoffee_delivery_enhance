web: python manage.py collectstatic --noinput && mkdir -p staticfiles/media && cp -r media/* staticfiles/media/ 2>/dev/null || true && gunicorn betweencoffee_delivery.wsgi:application --bind 0.0.0.0:$PORT --workers=3
celery_worker: celery -A betweencoffee_delivery.celery_app worker --loglevel=info --concurrency=2
celery_beat: celery -A betweencoffee_delivery.celery_app beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler
