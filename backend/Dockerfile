# ─────────────────────────────────────────────
# Multi-Cloud Analyzer — FastAPI Backend
# ─────────────────────────────────────────────
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY main.py .
COPY benchmark.py .

# Copy providers package (if present)
COPY providers/ ./providers/

# Copy data files (CSV seed data, Firebase key)
COPY benchmark_results.csv .
COPY firebase-admin-key.json .

# Copy environment file (if present — used by benchmark.py for cloud credentials)
COPY .env* ./

# Expose FastAPI port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD curl --fail http://localhost:8000/ || exit 1

# Run the FastAPI server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
