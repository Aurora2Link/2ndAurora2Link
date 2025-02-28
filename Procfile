web: gunicorn -k gevent -w 4 -b 0.0.0.0:8080 main:app
worker: celery -A celery_worker.celery worker --loglevel=info
