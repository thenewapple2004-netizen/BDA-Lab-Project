# Backend Dockerfile (Python/FastAPI)
FROM python:3.11-slim

WORKDIR /app

# Install system deps (minimal)
RUN apt-get update && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application code
COPY . .

ENV DATA_DIR=/app/data
EXPOSE 5000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5000"]

