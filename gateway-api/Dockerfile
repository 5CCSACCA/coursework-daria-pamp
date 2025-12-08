FROM python:3.10-slim

WORKDIR /app

RUN pip install --no-cache-dir fastapi uvicorn python-multipart requests firebase-admin pika prometheus-fastapi-instrumentator

COPY ./app /app/app

# Run on port 8080 (The main entry point)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]


