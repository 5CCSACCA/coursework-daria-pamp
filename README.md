# DeepSymbol – Cloud Computing for AI Coursework (5CCSACCA)

Repository: https://github.com/5CCSACCA/coursework-daria-pamp

DeepSymbol is a containerised AI service that detects objects in an uploaded image and returns a short “dream-style” symbolic interpretation. The system is built as a small distributed application with an API, an LLM inference service, background processing via a message queue, and full monitoring via Prometheus + Grafana.

## Architecture overview
The solution is composed of the following services (Docker Compose):
- api (FastAPI, HTTPS): main entrypoint. Handles image upload, object detection pipeline orchestration, Firebase authentication, and exposes /metrics for monitoring.
- bitnet (LLM inference): runs a local LLM endpoint compatible with chat completions. Used by the API to generate symbolic interpretations.
- rabbitmq (message queue): async pipeline for background post-processing.
- postprocess (worker): consumes messages from RabbitMQ and performs post-processing tasks.
- prometheus: scrapes metrics from the API.
- grafana: visualises Prometheus metrics with a provisioned dashboard and datasource.

High-level flow:
User calls API via Swagger UI or curl.
API authenticates request (Firebase ID token).
API sends prompt to bitnet to generate interpretation.
Any async work is queued via RabbitMQ and processed by postprocess worker.
API exports metrics; Prometheus scrapes them; Grafana shows dashboards.

## Repository structure

src/deepsymbol/ – FastAPI app + auth + BitNet client + prompt builder

bitnet/ – BitNet service container build and server

monitoring/ – Prometheus config + Grafana provisioning (datasource + dashboard)

tests/ – automated unit tests

run_tests.sh – convenience script to run tests

secrets/ – local secrets mount (excluded from Git)

certs/ – local self-signed TLS certs (excluded from Git)

## Security (Stage 11)

Firestore is not self-hosted → no open port
Access is via service account JSON mounted read-only
Only authenticated endpoints can write/read data

### Firebase authentication
Endpoints under /firebase/* are protected using Firebase ID tokens. Swagger UI supports an Authorize button (Bearer token).
Header expected:
Authorization: Bearer <FIREBASE_ID_TOKEN>

### HTTPS for API
The API runs over HTTPS using a self-signed certificate (local dev / coursework demo).
Because the certificate is self-signed, browsers may show a warning (“Potential Security Risk”). For verification and demo, use curl -k or accept the risk once in the browser.

Correct way to test the API
This will not work (API does not accept plain HTTP):
`curl http://localhost:8000/health`
Correct (ignore certificate verification, force HTTP/1.1):
`curl -k --http1.1 https://localhost:8000/health`
> Expected response: `{"status":"ok"}`

### Secrets handling
Secrets (Firebase key) are mounted read-only into the containers:
./secrets:/app/secrets:ro
TLS certs are mounted read-only:
./certs:/app/certs:ro
Both are excluded from Git via .gitignore.

## Monitoring (Stage 9)
### Prometheus
Prometheus scrapes the API metrics endpoint over HTTPS:
API metrics (Docker network): `https://api:8000/metrics`
From the host: `https://localhost:8000/metrics`
Config: monitoring/prometheus.yml:
```scheme: https
tls_config:
  insecure_skip_verify: true
```

Health checks:
Prometheus ready: `http://localhost:9090/-/ready`
Prometheus healthy: `http://localhost:9090/-/healthy`
Targets: `http://localhost:9090/targets`

### Grafana
Grafana is provisioned automatically:
Datasource: Prometheus (http://prometheus:9090)
Dashboard(s) loaded from: /var/lib/grafana/dashboards

UI:
Grafana dashboard: `http://localhost:3000`
Default login/password: admin / admin

## Testing (Stage 10)
Unit tests cover:
Prompt generation (deepsymbol.prompts)
LLM response cleaning (_clean_llm_text)
Auth helper behaviour

Run locally (recommended with venv):
```
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt

PYTHONPATH=src python -m pytest -q
```

Or use the helper script:
`./run_tests.sh`

All tests pass successfully.

## Setup

1) Place Firebase key
Put your Firebase service account json in:
./secrets/firebase_key.json

2) Ensure BitNet model exists
The BitNet model must exist at:
./bitnet/model/ggml-model-i2_s.gguf

3) Generate self-signed TLS cert (local demo)
```
mkdir -p certs
openssl req -x509 -newkey rsa:2048 -nodes \
  -keyout certs/key.pem -out certs/cert.pem \
  -days 365 -subj "/CN=localhost"
```

## Run with Docker Compose
Build and start everything:
```
sudo docker compose down -v #Clean reset, optional
sudo docker compose build
sudo docker compose up -d --build
sudo docker compose ps
```

Expected ports:
API (HTTPS): `https://localhost:8000`
BitNet: `http://localhost:8080`
RabbitMQ UI: `http://localhost:15672` (guest/guest)
Prometheus: `http://localhost:9090`
Grafana: `http://localhost:3000`

## Quick verification commands
API health:
```
curl -sk --http1.1 https://localhost:8000/health
```
Swagger UI HTML reachable:
```
curl -sk --http1.1 https://localhost:8000/docs | head
```
Metrics reachable:
```
curl -sk --http1.1 https://localhost:8000/metrics | head
```
Prometheus target shows API is UP:
```
curl -s http://localhost:9090/api/v1/targets | head -c 300; echo
```

## Using Swagger with Firebase auth
1)Open:
`https://localhost:8000/docs`
2)Click Authorize
3)Paste the raw token (without the word _Bearer_):
<YOUR_ID_TOKEN>

Example (getting token via Identity Toolkit API, if you have an email/password test user):
```
TOKEN=$(curl -s "https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=<API_KEY>" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"12345678","returnSecureToken":true}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin).get('idToken',''))")

curl -k -H "Authorization: Bearer $TOKEN" https://localhost:8000/firebase/outputs
```

All protected endpoints are secured using Firebase Authentication.
Requests without a token return 401 Unauthorized
Requests with a valid Firebase ID token are accepted
Example (unauthenticated request):
`curl -k --http1.1 https://localhost:8000/firebase/outputs`
Expected result:
`401 Unauthorized`

### Secrets management
Firebase service account credentials are mounted as read-only volumes
Secrets are excluded from version control via .gitignore
No database ports are exposed externally

Firestore is used as a managed backend service, accessed only via authenticated SDK calls

## Troubleshooting
### Browser warning on /docs
This is expected with self-signed TLS. For demo/verification use:
`curl -sk --http1.1 https://localhost:8000/health`

### BitNet unavailable / 503
Make sure BitNet container is running:
```
sudo docker compose ps
sudo docker compose up -d bitnet
```

### Worker shows “retrying”
This can happen briefly while RabbitMQ initialises. It should settle into:
`[postprocess] waiting for messages...`

## Service ports

| Service      | Port | Protocol | Description |
|--------------|------|----------|-------------|
| API          | 8000 | HTTPS    | FastAPI entrypoint (secured with TLS) |
| BitNet       | 8080 | HTTP     | Local LLM inference service |
| RabbitMQ     | 5672 | AMQP     | Message queue (internal communication) |
| RabbitMQ UI  | 15672| HTTP     | RabbitMQ management console |
| Prometheus   | 9090 | HTTP     | Metrics scraping and querying |
| Grafana      | 3000 | HTTP     | Metrics visualisation dashboard |

