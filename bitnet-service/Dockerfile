# Lightweight Python base
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install minimal system deps (needed for transformers + tokenizers)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir \
    fastapi \
    uvicorn[standard] \
    pillow \
    transformers==4.36.2 \
    torch --index-url https://download.pytorch.org/whl/cpu \
    python-multipart

# Copy service code
COPY ./app /app/app

# Prevent stdout buffering (useful for logs)
ENV PYTHONUNBUFFERED=1

# Expose internal port
EXPOSE 8001

# Start LLM service
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
