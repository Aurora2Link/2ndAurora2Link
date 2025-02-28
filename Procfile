web: gunicorn -w 4 -b 0.0.0.0:5000 app:app
worker: celery -A celery_worker.celery worker --loglevel=info
