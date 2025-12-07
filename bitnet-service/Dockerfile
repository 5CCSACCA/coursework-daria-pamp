# Use a lightweight Python base
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python libraries
# torch & transformers: for the AI model
# fastapi & uvicorn: for the API
RUN pip install --no-cache-dir torch transformers fastapi uvicorn python-multipart

# Copy the app code
COPY ./app /app/app

# Run the service on port 8001
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
