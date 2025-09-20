# Deployment Guide

## Overview

This guide covers various deployment options for the Resume Relevance Check System, from local development to production cloud deployments.

## Prerequisites

- Python 3.8+
- Docker and Docker Compose (for containerized deployment)
- Git
- OpenAI API key (optional but recommended)
- HuggingFace token (optional)

## Deployment Options

### 1. Local Development

#### Quick Setup
```bash
# Clone repository
git clone <repository-url>
cd resume-relevance-check-system

# Run setup script
chmod +x setup.sh
./setup.sh

# Edit environment variables
nano .env

# Start services
./start_backend.sh &
./start_frontend.sh
```

#### Manual Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
python -m spacy download en_core_web_sm

# Set up environment
cp .env.template .env
# Edit .env with your settings

# Start backend
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Start frontend (new terminal)
cd frontend
streamlit run main.py --server.port 8501
```

### 2. Docker Deployment

#### Using Docker Compose (Recommended)
```bash
# Clone and setup
git clone <repository-url>
cd resume-relevance-check-system

# Configure environment
cp .env.template .env
# Edit .env with your API keys

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

#### Individual Docker Containers
```bash
# Build backend image
docker build -t resume-backend -f Dockerfile.backend .

# Build frontend image  
docker build -t resume-frontend -f Dockerfile.frontend .

# Run backend
docker run -d -p 8000:8000 \
  -e OPENAI_API_KEY=your_key \
  -v $(pwd)/uploads:/app/uploads \
  resume-backend

# Run frontend
docker run -d -p 8501:8501 \
  -e API_BASE_URL=http://localhost:8000 \
  resume-frontend
```

### 3. Cloud Deployments

#### Streamlit Cloud

1. **Prepare Repository**
```bash
# Create requirements.txt for Streamlit Cloud
echo "streamlit==1.28.2
streamlit-option-menu==0.3.6
requests==2.31.0
pandas==2.1.4
plotly==5.17.0" > streamlit_requirements.txt
```

2. **Deploy Frontend**
- Push code to GitHub
- Visit [Streamlit Cloud](https://streamlit.io/cloud)
- Connect GitHub repository
- Set main file path: `frontend/main.py`
- Add secrets for API keys

3. **Deploy Backend Separately**
- Use Heroku, Railway, or Render for backend
- Update `API_BASE_URL` in Streamlit app

#### Heroku Deployment

1. **Backend Deployment**
```bash
# Install Heroku CLI
npm install -g heroku

# Login and create app
heroku login
heroku create resume-relevance-backend

# Configure buildpacks
heroku buildpacks:set heroku/python

# Set environment variables
heroku config:set OPENAI_API_KEY=your_key
heroku config:set HUGGINGFACE_API_TOKEN=your_token

# Create Procfile for backend
echo "web: uvicorn backend.app.main:app --host 0.0.0.0 --port \$PORT" > Procfile

# Deploy
git add .
git commit -m "Deploy to Heroku"
git push heroku main
```

2. **Frontend on Streamlit Cloud**
- Configure `API_BASE_URL` to point to Heroku backend
- Deploy frontend on Streamlit Cloud

#### AWS Deployment

1. **Using AWS ECS**
```bash
# Push images to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account>.dkr.ecr.us-east-1.amazonaws.com

# Tag and push backend
docker tag resume-backend:latest <account>.dkr.ecr.us-east-1.amazonaws.com/resume-backend:latest
docker push <account>.dkr.ecr.us-east-1.amazonaws.com/resume-backend:latest

# Tag and push frontend
docker tag resume-frontend:latest <account>.dkr.ecr.us-east-1.amazonaws.com/resume-frontend:latest
docker push <account>.dkr.ecr.us-east-1.amazonaws.com/resume-frontend:latest
```

2. **ECS Task Definition**
```json
{
  "family": "resume-relevance-system",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "containerDefinitions": [
    {
      "name": "backend",
      "image": "<account>.dkr.ecr.us-east-1.amazonaws.com/resume-backend:latest",
      "portMappings": [{"containerPort": 8000}],
      "environment": [
        {"name": "OPENAI_API_KEY", "value": "your_key"}
      ]
    },
    {
      "name": "frontend",
      "image": "<account>.dkr.ecr.us-east-1.amazonaws.com/resume-frontend:latest",
      "portMappings": [{"containerPort": 8501}]
    }
  ]
}
```

#### Google Cloud Run

1. **Deploy Backend**
```bash
# Build and push to Google Container Registry
gcloud builds submit --tag gcr.io/PROJECT_ID/resume-backend backend/

# Deploy to Cloud Run
gcloud run deploy resume-backend \
  --image gcr.io/PROJECT_ID/resume-backend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars OPENAI_API_KEY=your_key
```

2. **Deploy Frontend**
```bash
# Build and push frontend
gcloud builds submit --tag gcr.io/PROJECT_ID/resume-frontend frontend/

# Deploy frontend
gcloud run deploy resume-frontend \
  --image gcr.io/PROJECT_ID/resume-frontend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars API_BASE_URL=https://resume-backend-xxx.run.app
```

#### Azure Container Instances

1. **Create Resource Group**
```bash
az group create --name resume-rg --location eastus
```

2. **Deploy Backend**
```bash
az container create \
  --resource-group resume-rg \
  --name resume-backend \
  --image resume-backend:latest \
  --dns-name-label resume-backend-unique \
  --ports 8000 \
  --environment-variables OPENAI_API_KEY=your_key
```

3. **Deploy Frontend**
```bash
az container create \
  --resource-group resume-rg \
  --name resume-frontend \
  --image resume-frontend:latest \
  --dns-name-label resume-frontend-unique \
  --ports 8501 \
  --environment-variables API_BASE_URL=http://resume-backend-unique.eastus.azurecontainer.io:8000
```

### 4. Production Considerations

#### Database Setup
```bash
# For production, use PostgreSQL
pip install psycopg2-binary

# Update .env
DATABASE_URL=postgresql://user:password@localhost/resume_relevance
```

#### Security Configuration
```python
# backend/app/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Restrict origins
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Add authentication middleware
from fastapi.security import HTTPBearer
security = HTTPBearer()
```

#### Environment Variables
```env
# Production settings
DEBUG=False
SECRET_KEY=your_strong_secret_key
DATABASE_URL=postgresql://user:password@host:port/database
REDIS_URL=redis://localhost:6379/0

# API Keys
OPENAI_API_KEY=sk-...
HUGGINGFACE_API_TOKEN=hf_...

# File Storage
AWS_ACCESS_KEY_ID=your_aws_key
AWS_SECRET_ACCESS_KEY=your_aws_secret
AWS_STORAGE_BUCKET_NAME=your_bucket
```

#### Scaling Configuration
```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  backend:
    build: .
    scale: 3
    environment:
      - DATABASE_URL=postgresql://user:password@db:5432/resume_relevance
    depends_on:
      - db
      - redis

  frontend:
    build: ./frontend
    scale: 2

  db:
    image: postgres:13
    environment:
      POSTGRES_DB: resume_relevance
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:alpine

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.prod.conf:/etc/nginx/nginx.conf
```

#### Monitoring Setup
```bash
# Add health checks
docker-compose.yml:
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 30s
  timeout: 10s
  retries: 3

# Logging configuration
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
```

### 5. SSL/HTTPS Setup

#### Using Let's Encrypt with Nginx
```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d yourdomain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

#### Nginx SSL Configuration
```nginx
server {
    listen 443 ssl;
    server_name yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    location / {
        proxy_pass http://frontend:8501;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /api/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 6. Backup and Recovery

#### Database Backup
```bash
# PostgreSQL backup
pg_dump -h localhost -U user resume_relevance > backup.sql

# Restore
psql -h localhost -U user resume_relevance < backup.sql
```

#### File Storage Backup
```bash
# Backup uploads directory
tar -czf uploads_backup.tar.gz uploads/

# Backup vector store
tar -czf vector_store_backup.tar.gz vector_store/
```

### 7. Performance Optimization

#### Caching with Redis
```python
# backend/app/cache.py
import redis
from functools import wraps

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def cache_result(expiration=3600):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
            result = redis_client.get(cache_key)
            if result:
                return json.loads(result)
            
            result = func(*args, **kwargs)
            redis_client.setex(cache_key, expiration, json.dumps(result))
            return result
        return wrapper
    return decorator
```

#### Load Balancing
```nginx
upstream backend {
    server backend1:8000;
    server backend2:8000;
    server backend3:8000;
}

upstream frontend {
    server frontend1:8501;
    server frontend2:8501;
}
```

### 8. Troubleshooting

#### Common Issues
```bash
# Port conflicts
sudo lsof -i :8000
sudo kill -9 <PID>

# Memory issues
docker system prune -a
docker volume prune

# Database connection issues
docker-compose logs db
docker-compose restart db
```

#### Health Checks
```bash
# Check backend health
curl http://localhost:8000/health

# Check frontend
curl http://localhost:8501

# Check database
docker-compose exec db psql -U user -d resume_relevance -c "\dt"
```

This deployment guide provides comprehensive options for deploying the Resume Relevance Check System in various environments, from development to production-scale deployments.
