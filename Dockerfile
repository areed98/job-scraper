FROM python:3.12-slim

# Minimal system deps (reportlab is pure Python)
RUN apt-get update && apt-get install -y --no-install-recommends \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Ensure data dirs exist at build time (volumes will override at runtime)
RUN mkdir -p /data/resume

ENV DATA_DIR=/data
ENV RESUME_DIR=/data/resume
ENV FLASK_APP=run.py

# Run migrations then start gunicorn
CMD flask db upgrade && gunicorn --bind 0.0.0.0:8000 --workers 2 --timeout 120 run:app
