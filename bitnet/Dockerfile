FROM ghcr.io/kth8/bitnet:latest

WORKDIR /app

RUN pip3 install --no-cache-dir fastapi uvicorn pydantic

COPY server.py /app/server.py

EXPOSE 8080
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8080"]

