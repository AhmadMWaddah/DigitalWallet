# Render Deployment Processes
# https://render.com/docs/procfile

# Web server (Gunicorn)
web: gunicorn core.wsgi --bind 0.0.0.0:$PORT

# Celery worker for async tasks
worker: celery -A core worker -l info
