web: python manage.py migrate && gunicorn betweencoffee_delivery.wsgi:application --bind 0.0.0.0:$PORT
worker: python manage.py runworker