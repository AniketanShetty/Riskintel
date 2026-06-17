FROM python:3.13-slim

WORKDIR /app

# Install system dependencies required for psycopg2 and building
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Ensure entrypoint is executable
RUN chmod +x entrypoint.sh

# Set PYTHONPATH so Alembic can import the local modules
ENV PYTHONPATH=/app

# Expose port
EXPOSE 8000

ENTRYPOINT ["./entrypoint.sh"]
