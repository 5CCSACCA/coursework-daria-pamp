FROM python:3.10-slim

WORKDIR /app

# Install curl for healthcheck inside the container
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir fastapi uvicorn python-multipart requests firebase-admin pika prometheus-fastapi-instrumentator

COPY ./app /app/app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]


