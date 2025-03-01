web: gunicorn main:app
worker: celery -A main worker --loglevel=info --autoscale=8,2