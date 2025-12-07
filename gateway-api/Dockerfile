FROM python:3.10-slim

WORKDIR /app

# Install dependencies
# requests: to call yolo and bitnet services
# sqlalchemy: for the database
RUN pip install --no-cache-dir fastapi uvicorn python-multipart requests sqlalchemy

COPY ./app /app/app

# Run on port 8080 (The main entry point)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
