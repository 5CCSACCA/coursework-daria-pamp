# Stage 2: container with YOLO + TinyLlama + DeepSymbol code
FROM python:3.11-slim

# Environment options: no .pyc files, unbuffered logs
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install system dependencies needed by OpenCV / Ultralytics / Torch
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Work directory inside the container
WORKDIR /app

# Install Python dependencies first (better layer caching)
COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu torch torchvision && \
    pip install --no-cache-dir -r requirements.txt
    
RUN python -c "from ultralytics import YOLO; YOLO('yolo11n.pt')"

# Copy project code and example data
COPY src ./src
COPY scripts ./scripts
COPY data ./data

# Make src importable as a package
ENV PYTHONPATH=/app/src

# Default command for Stage 2:
# run DeepSymbol pipeline on example image
CMD ["uvicorn", "deepsymbol.api:app", "--host", "0.0.0.0", "--port", "8000"]

