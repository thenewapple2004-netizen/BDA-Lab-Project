# Weather Analytics Backend - Multi-stage build
# Stage 1: Build React frontend
FROM node:18-alpine AS frontend-builder

WORKDIR /app/frontend

# Copy package files
COPY frontend/package*.json ./

# Install dependencies
RUN npm install

# Copy frontend source
COPY frontend/ ./

# Build React app
RUN npm run build

# Stage 2: Python backend
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY backend/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy main.py (all backend code in one file)
COPY backend/main.py .

# Copy built React app from frontend-builder
COPY --from=frontend-builder /app/frontend/build ./frontend

# Expose port
EXPOSE 5000

# Set environment variables
ENV DATA_DIR=/app/data

# Run the application
CMD ["python", "main.py"]
