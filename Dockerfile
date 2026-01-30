FROM python:3.11-slim

WORKDIR /app

# System-Dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Python-Dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application-Code
COPY . .

# Daten-Verzeichnisse
RUN mkdir -p /app/data /app/logs && \
    chmod 755 /app/data /app/logs

EXPOSE 5000

# Health-Check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

CMD ["python", "app.py"]
