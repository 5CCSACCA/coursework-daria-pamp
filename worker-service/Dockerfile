FROM python:3.10-slim

WORKDIR /app

# Install dependencies
# pika: for RabbitMQ
# firebase-admin, requests: for processing
RUN pip install --no-cache-dir pika requests firebase-admin

COPY ./app /app/app

# Run the worker script
CMD ["python", "-u", "app/main.py"]