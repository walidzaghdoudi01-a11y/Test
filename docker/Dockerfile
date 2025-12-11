FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY audit-service /app/audit-service
COPY audit-client /app/audit-client
COPY database /app/database

# Install audit-client as package
RUN pip install -e /app/audit-client

ENV PYTHONPATH=/app

# Run migrations and start service
CMD cd /app/database && alembic upgrade head && \
    cd /app/audit-service && uvicorn app.main:app --host 0.0.0.0 --port 8000
