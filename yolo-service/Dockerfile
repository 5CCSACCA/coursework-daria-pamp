
FROM python:3.10-slim

# ---- System deps ----
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ---- Python deps ----
RUN pip install --no-cache-dir \
    fastapi \
    uvicorn[standard] \
    pillow \
    ultralytics \
    python-multipart

# Install CPU-only PyTorch separately
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# ---- Copy service code ----
COPY app /app/app

ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
