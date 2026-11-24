FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (e.g. for psycopg2 if building from source, though we use binary)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir --default-timeout=100 --retries=10 -r requirements.txt

COPY . .

# Expose port
EXPOSE 8000

# Script to wait for DB and run migrations
COPY start.sh /start.sh
RUN chmod +x /start.sh

CMD ["/start.sh"]
