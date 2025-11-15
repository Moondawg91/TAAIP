# TAAIP Deployment Guide

## Overview

This guide covers deploying the TAAIP system in development, staging, and production environments.

---

## Local Development Setup

### Prerequisites
- Python 3.8+
- Node.js 14+ (for API gateway)
- SQLite3
- Docker (optional, for containerized deployment)

### Installation

1. **Clone and setup**:
   ```bash
   cd /Users/ambermooney/Desktop/TAAIP
   ```

2. **Create Python virtual environment** (optional but recommended):
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Install Node dependencies** (for API gateway):
   ```bash
   npm install  # In project root or api-gateway directory
   ```

### Running Locally

#### Option 1: Direct Python (All-in-One)
```bash
python taaip_service.py
```
- FastAPI runs at `http://localhost:8000`
- Database initializes automatically at `data/taaip.sqlite3`

#### Option 2: With API Gateway
Terminal 1 - Start FastAPI backend:
```bash
python taaip_service.py
```

Terminal 2 - Start Express gateway:
```bash
node api-gateway.js
```
- Gateway runs at `http://localhost:3001`
- Proxies `/api/targeting/*` to backend

#### Option 3: With Docker Compose
```bash
docker-compose up -d
```
- FastAPI: `http://localhost:8000`
- Gateway: `http://localhost:3001`
- Frontend: `http://localhost:3000`

### Testing

Run the API test suite:
```bash
python test_taaip_api.py
```

Or with authentication:
```bash
export TAAIP_API_TOKEN=your_secret_token
python test_taaip_api.py --token $TAAIP_API_TOKEN
```

---

## Environment Configuration

### FastAPI Backend (`taaip_service.py`)

Set environment variables:

```bash
# Database location
export TAAIP_DB_PATH=data/taaip.sqlite3

# Optional: Machine learning model path
export TAAIP_MODEL_PATH=data/model.joblib

# Optional: API authentication token
export TAAIP_API_TOKEN=your_secret_api_token

# Optional: CORS allowed origins (comma-separated)
export TAAIP_CORS_ORIGINS=http://localhost:3000,http://localhost:3001

# Optional: Log level
export TAAIP_LOG_LEVEL=INFO

# Start service
python taaip_service.py
```

### Express Gateway (`api-gateway.js`)

```bash
# API Gateway port
export API_GATEWAY_PORT=3001

# Backend URL
export BACKEND_URL=http://localhost:8000

# Optional: API token (must match backend)
export TAAIP_API_TOKEN=your_secret_api_token

# Start gateway
node api-gateway.js
```

### Static Frontend

```bash
# Frontend server port
export FRONTEND_PORT=3000

# Start static server (Python)
python -m http.server 3000 --directory frontend

# Or with Node (if http-server installed)
http-server frontend -p 3000
```

---

## Docker Deployment

### Build Images

```bash
# Build FastAPI backend
docker build -f Dockerfile.backend -t taaip-backend:latest .

# Build Express gateway
docker build -f Dockerfile.gateway -t taaip-gateway:latest .
```

### Run with Docker Compose

**File: `docker-compose.yml`**:
```yaml
version: '3.8'

services:
  backend:
    build:
      context: .
      dockerfile: Dockerfile.backend
    ports:
      - "8000:8000"
    environment:
      TAAIP_DB_PATH: /app/data/taaip.sqlite3
      TAAIP_API_TOKEN: ${TAAIP_API_TOKEN}
    volumes:
      - ./data:/app/data
    command: uvicorn taaip_service:app --host 0.0.0.0 --port 8000

  gateway:
    build:
      context: .
      dockerfile: Dockerfile.gateway
    ports:
      - "3001:3001"
    environment:
      BACKEND_URL: http://backend:8000
      TAAIP_API_TOKEN: ${TAAIP_API_TOKEN}
    depends_on:
      - backend

  frontend:
    image: nginx:latest
    ports:
      - "3000:80"
    volumes:
      - ./frontend:/usr/share/nginx/html
```

**Start services**:
```bash
export TAAIP_API_TOKEN=your_secret_token
docker-compose up -d
```

**Monitor logs**:
```bash
docker-compose logs -f backend
docker-compose logs -f gateway
```

---

## Production Deployment

### 1. Database Migration to PostgreSQL

**Install PostgreSQL locally** (or use managed service like AWS RDS):
```bash
# macOS
brew install postgresql
brew services start postgresql

# Create database
createdb taaip_prod
```

**Update connection string** in `taaip_service.py`:
```python
import os
from sqlalchemy import create_engine

# PostgreSQL connection
db_url = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/taaip_prod")
engine = create_engine(db_url)
```

### 2. API Security Hardening

**Enable HTTPS/TLS**:
```bash
# Generate self-signed certificate (testing only)
openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365

# In taaip_service.py, use uvicorn with SSL:
# uvicorn taaip_service:app --host 0.0.0.0 --port 8000 --ssl-keyfile=key.pem --ssl-certfile=cert.pem
```

**Implement OAuth/OIDC** (replace Bearer token):
```python
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@app.post("/token")
def login(username: str, password: str):
    # Validate credentials
    token = jwt.encode({"sub": username}, SECRET_KEY, algorithm="HS256")
    return {"access_token": token, "token_type": "bearer"}

@app.get("/api/v2/events")
def get_events(token: str = Depends(oauth2_scheme)):
    # Verify JWT token
    payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    return {"events": []}
```

### 3. API Rate Limiting

```bash
pip install slowapi
```

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.get("/api/v2/events")
@limiter.limit("100/minute")
def get_events(request: Request):
    return {}
```

### 4. Logging & Monitoring

**Setup structured logging**:
```bash
pip install python-json-logger
```

```python
import logging
from pythonjsonlogger import jsonlogger

logger = logging.getLogger()
logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter()
logHandler.setFormatter(formatter)
logger.addHandler(logHandler)

logger.info("Event created", extra={"event_id": "evt_123", "user_id": "usr_001"})
```

**Monitor with CloudWatch / ELK**:
```bash
# Send logs to CloudWatch
pip install watchtower

import watchtower
handler = watchtower.CloudWatchLogHandler()
logger.addHandler(handler)
```

### 5. CI/CD Pipeline

**GitHub Actions** (`.github/workflows/deploy.yml`):
```yaml
name: Deploy TAAIP

on:
  push:
    branches: [main, staging]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.9
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest
      - name: Run tests
        run: pytest tests/

  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v2
      - name: Deploy to AWS
        run: |
          aws deploy --service taaip --version ${{ github.sha }}
```

### 6. Kubernetes Deployment

**Create deployment manifest** (`k8s-deployment.yaml`):
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: taaip-backend
  namespace: recruiting

spec:
  replicas: 3
  selector:
    matchLabels:
      app: taaip-backend

  template:
    metadata:
      labels:
        app: taaip-backend
    spec:
      containers:
      - name: backend
        image: taaip-backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: taaip-secrets
              key: db-url
        - name: TAAIP_API_TOKEN
          valueFrom:
            secretKeyRef:
              name: taaip-secrets
              key: api-token
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10

---
apiVersion: v1
kind: Service
metadata:
  name: taaip-backend-service
  namespace: recruiting

spec:
  selector:
    app: taaip-backend
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer

---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: taaip-hpa
  namespace: recruiting

spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: taaip-backend
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

**Deploy**:
```bash
kubectl apply -f k8s-deployment.yaml

# Monitor
kubectl get pods -n recruiting
kubectl logs -n recruiting deployment/taaip-backend
```

### 7. Database Backup & Recovery

**Automated backups**:
```bash
# PostgreSQL backup script
#!/bin/bash
BACKUP_DIR="/backups/taaip"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

pg_dump -h localhost -U postgres taaip_prod > "$BACKUP_DIR/taaip_$TIMESTAMP.sql"

# Compress and upload to S3
gzip "$BACKUP_DIR/taaip_$TIMESTAMP.sql"
aws s3 cp "$BACKUP_DIR/taaip_$TIMESTAMP.sql.gz" s3://taaip-backups/
```

**Restore from backup**:
```bash
aws s3 cp s3://taaip-backups/taaip_YYYYMMDD_HHMMSS.sql.gz .
gunzip taaip_YYYYMMDD_HHMMSS.sql.gz
psql -h localhost -U postgres taaip_prod < taaip_YYYYMMDD_HHMMSS.sql
```

---

## Performance Optimization

### 1. Database Indexing

```sql
-- Add indexes for frequently queried fields
CREATE INDEX idx_events_created ON events(created_at DESC);
CREATE INDEX idx_funnel_transitions_lead ON funnel_transitions(lead_id);
CREATE INDEX idx_event_metrics_date ON event_metrics(event_id, date);
```

### 2. Caching Strategy

```bash
pip install redis
```

```python
import redis
from functools import wraps

cache = redis.Redis(host='localhost', port=6379, db=0)

def cached(expire=3600):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            key = f"{func.__name__}:{args}:{kwargs}"
            result = cache.get(key)
            if result:
                return json.loads(result)
            result = func(*args, **kwargs)
            cache.setex(key, expire, json.dumps(result))
            return result
        return wrapper
    return decorator

@app.get("/api/v2/analytics/dashboard")
@cached(expire=300)  # Cache for 5 minutes
def get_dashboard():
    return get_dashboard_snapshot()
```

### 3. Query Optimization

```python
# Use database connection pooling
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True
)
```

---

## Monitoring & Alerting

### Health Check Endpoint

```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "ok",
  "service": "TAAIP Targeting & AI Service",
  "model_status": "simulated",
  "database": "connected",
  "timestamp": "2025-01-20T14:30:00Z"
}
```

### Metrics Endpoint

```bash
curl http://localhost:8000/metrics
```

Returns Prometheus-compatible metrics.

### Setup Alerting

**PagerDuty Integration**:
```python
import requests

def alert(severity, message):
    payload = {
        "routing_key": os.getenv("PAGERDUTY_ROUTING_KEY"),
        "event_action": "trigger",
        "dedup_key": f"taaip-{severity}-{int(time.time())}",
        "payload": {
            "summary": message,
            "severity": severity,
            "source": "TAAIP Service"
        }
    }
    requests.post("https://events.pagerduty.com/v2/enqueue", json=payload)

# Alert on high error rate
if error_rate > 0.05:
    alert("critical", "TAAIP API error rate > 5%")
```

---

## Troubleshooting

### Common Issues

**Issue**: Database locked
```
Solution: Ensure only one instance is writing to SQLite
Use PostgreSQL for multi-process deployments
```

**Issue**: API timeouts
```
Solution: Increase uvicorn timeout
uvicorn taaip_service:app --timeout-keep-alive 30
```

**Issue**: Memory leak
```
Solution: Monitor with:
ps aux | grep taaip_service
Enable garbage collection profiling
```

### Debug Mode

```bash
export TAAIP_DEBUG=1
export PYTHONUNBUFFERED=1
python taaip_service.py
```

---

## Scaling Checklist

- [ ] Move from SQLite to PostgreSQL
- [ ] Implement connection pooling
- [ ] Add Redis caching layer
- [ ] Setup load balancer
- [ ] Configure autoscaling
- [ ] Implement health checks
- [ ] Setup monitoring/alerts
- [ ] Document incident response
- [ ] Backup strategy in place
- [ ] Disaster recovery plan tested
