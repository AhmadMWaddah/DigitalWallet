# Use the official Python slim image for a smaller footprint
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory in the container
WORKDIR /app

# Install system dependencies needed for psycopg2 and Celery
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Collect static files for production
RUN python manage.py collectstatic --noinput --settings=core.settings.prod

# Expose the port the app runs on
EXPOSE 8000

# Set the default command (can be overridden)
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "core.wsgi:application"]
