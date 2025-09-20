# 🚀 Deployment Guide

This guide covers various deployment options for the Automated Resume Relevance Check System.

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Local Development](#local-development)
3. [Docker Deployment](#docker-deployment)
4. [Cloud Deployment](#cloud-deployment)
   - [Heroku](#heroku)
   - [AWS](#aws)
   - [Google Cloud Platform](#google-cloud-platform)
   - [Azure](#azure)
   - [DigitalOcean](#digitalocean)
5. [Kubernetes](#kubernetes)
6. [Environment Configuration](#environment-configuration)
7. [Production Checklist](#production-checklist)
8. [Monitoring & Maintenance](#monitoring--maintenance)

## Prerequisites

- Git
- Docker and Docker Compose (for containerized deployment)
- Python 3.9+ (for local development)
- Cloud account (for cloud deployment)

## Local Development

### Quick Start
```bash
# Clone repository
git clone <your-repo-url>
cd automated-resume-relevance-check-system

# Set up environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
.\venv\Scripts\Activate.ps1  # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Initialize database
cd backend
python -c "from app.database.init_db import create_tables; create_tables()"

# Download models
python -m spacy download en_core_web_sm

# Start services
# Terminal 1: Backend
uvicorn app.main:app --reload --port 8000

# Terminal 2: Frontend
cd ../
streamlit run frontend/main.py --server.port 8501
```

## Docker Deployment

### Development
```bash
# Build and start services
docker-compose up --build

# Access application
# Frontend: http://localhost:8501
# Backend: http://localhost:8000
```

### Production
```bash
# Use production configuration
docker-compose -f docker-compose.prod.yml up -d

# View logs
docker-compose logs -f

# Scale services
docker-compose up --scale backend=2 --scale frontend=2
```

## Cloud Deployment

### Heroku

#### Automatic Deployment (Recommended)
1. **Fork the repository** on GitHub
2. **Create Heroku app**:
   ```bash
   heroku create your-app-name
   ```
3. **Configure environment variables**:
   ```bash
   heroku config:set SECRET_KEY=your_secret_key
   heroku config:set DATABASE_URL=your_database_url
   heroku config:set OPENAI_API_KEY=your_openai_key
   ```
4. **Deploy**:
   ```bash
   git push heroku main
   ```

#### Manual Deployment
```bash
# Install Heroku CLI
# Login to Heroku
heroku login

# Create app
heroku create your-resume-app

# Add PostgreSQL addon
heroku addons:create heroku-postgresql:hobby-dev

# Set environment variables
heroku config:set SECRET_KEY=$(openssl rand -base64 32)
heroku config:set ENVIRONMENT=production

# Deploy
git push heroku main

# Run database migrations
heroku run python backend/app/database/init_db.py

# Open app
heroku open
```

### AWS

#### Using AWS Elastic Beanstalk
1. **Install EB CLI**:
   ```bash
   pip install awsebcli
   ```

2. **Initialize EB application**:
   ```bash
   eb init resume-checker
   ```

3. **Create environment**:
   ```bash
   eb create production
   ```

4. **Deploy**:
   ```bash
   eb deploy
   ```

#### Using AWS ECS (Docker)
1. **Build and push to ECR**:
   ```bash
   # Create ECR repository
   aws ecr create-repository --repository-name resume-checker

   # Get login token
   aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

   # Build and tag
   docker build -t resume-checker .
   docker tag resume-checker:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/resume-checker:latest

   # Push
   docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/resume-checker:latest
   ```

2. **Create ECS service** using AWS Console or CLI

#### Using AWS Lambda (Serverless)
```bash
# Install Serverless Framework
npm install -g serverless

# Deploy serverless backend
serverless deploy
```

### Google Cloud Platform

#### Using Cloud Run
1. **Build and deploy**:
   ```bash
   # Set project
   gcloud config set project your-project-id

   # Build image
   gcloud builds submit --tag gcr.io/your-project-id/resume-checker

   # Deploy to Cloud Run
   gcloud run deploy resume-checker \
     --image gcr.io/your-project-id/resume-checker \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated
   ```

#### Using App Engine
1. **Create app.yaml**:
   ```yaml
   runtime: python39
   
   env_variables:
     SECRET_KEY: "your_secret_key"
     DATABASE_URL: "your_database_url"
   
   automatic_scaling:
     min_instances: 1
     max_instances: 10
   ```

2. **Deploy**:
   ```bash
   gcloud app deploy
   ```

### Azure

#### Using Container Instances
```bash
# Create resource group
az group create --name resume-checker --location eastus

# Create container instance
az container create \
  --resource-group resume-checker \
  --name resume-app \
  --image your-docker-image \
  --ports 8000 8501 \
  --environment-variables SECRET_KEY=your_key
```

#### Using App Service
```bash
# Create app service plan
az appservice plan create --name resume-plan --resource-group resume-checker --sku B1 --is-linux

# Create web app
az webapp create --resource-group resume-checker --plan resume-plan --name your-resume-app --runtime "PYTHON|3.9"

# Deploy code
az webapp deployment source config --name your-resume-app --resource-group resume-checker --repo-url https://github.com/your-username/your-repo --branch main
```

### DigitalOcean

#### Using App Platform
1. **Create app spec** (`app.yaml`):
   ```yaml
   name: resume-checker
   services:
   - name: backend
     source_dir: backend
     github:
       repo: your-username/your-repo
       branch: main
     run_command: uvicorn app.main:app --host 0.0.0.0 --port 8080
     environment_slug: python
     instance_count: 1
     instance_size_slug: basic-xxs
     envs:
     - key: SECRET_KEY
       value: your_secret_key
   - name: frontend
     source_dir: frontend
     run_command: streamlit run main.py --server.port 8080
     environment_slug: python
     instance_count: 1
     instance_size_slug: basic-xxs
   ```

2. **Deploy**:
   ```bash
   doctl apps create --spec app.yaml
   ```

## Kubernetes

### Prerequisites
- Kubernetes cluster
- kubectl configured
- Docker registry access

### Deployment Steps

1. **Create namespace**:
   ```bash
   kubectl create namespace resume-checker
   ```

2. **Deploy ConfigMap**:
   ```yaml
   apiVersion: v1
   kind: ConfigMap
   metadata:
     name: resume-config
     namespace: resume-checker
   data:
     DATABASE_URL: "postgresql://user:pass@db:5432/resume_db"
     ENVIRONMENT: "production"
   ```

3. **Deploy Secret**:
   ```yaml
   apiVersion: v1
   kind: Secret
   metadata:
     name: resume-secrets
     namespace: resume-checker
   type: Opaque
   data:
     SECRET_KEY: <base64-encoded-secret>
     OPENAI_API_KEY: <base64-encoded-key>
   ```

4. **Deploy Application**:
   ```yaml
   apiVersion: apps/v1
   kind: Deployment
   metadata:
     name: resume-backend
     namespace: resume-checker
   spec:
     replicas: 2
     selector:
       matchLabels:
         app: resume-backend
     template:
       metadata:
         labels:
           app: resume-backend
       spec:
         containers:
         - name: backend
           image: your-registry/resume-backend:latest
           ports:
           - containerPort: 8000
           envFrom:
           - configMapRef:
               name: resume-config
           - secretRef:
               name: resume-secrets
   ```

5. **Deploy Service**:
   ```yaml
   apiVersion: v1
   kind: Service
   metadata:
     name: resume-backend-service
     namespace: resume-checker
   spec:
     selector:
       app: resume-backend
     ports:
     - port: 8000
       targetPort: 8000
     type: LoadBalancer
   ```

## Environment Configuration

### Production Environment Variables
```bash
# Required
SECRET_KEY=your_very_secure_secret_key_here
DATABASE_URL=postgresql://user:password@host:port/database

# Optional but recommended
OPENAI_API_KEY=your_openai_api_key
HUGGINGFACE_API_KEY=your_huggingface_api_key

# Application settings
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

# Security
ALLOWED_ORIGINS=["https://yourdomain.com"]
CORS_ALLOW_CREDENTIALS=true

# File upload
MAX_FILE_SIZE=10485760
ALLOWED_EXTENSIONS=pdf,docx

# AI settings
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
HARD_MATCH_WEIGHT=0.4
SEMANTIC_MATCH_WEIGHT=0.6
```

### Database Configuration

#### PostgreSQL (Recommended for Production)
```bash
# Install PostgreSQL
# Create database
createdb resume_checker

# Set DATABASE_URL
DATABASE_URL=postgresql://username:password@localhost:5432/resume_checker
```

#### SQLite (Development Only)
```bash
DATABASE_URL=sqlite:///./resume_relevance.db
```

## Production Checklist

### Security
- [ ] Change default SECRET_KEY
- [ ] Use strong database passwords
- [ ] Enable HTTPS/SSL
- [ ] Configure CORS properly
- [ ] Implement rate limiting
- [ ] Add authentication if needed
- [ ] Validate file uploads strictly
- [ ] Regular security updates

### Performance
- [ ] Use PostgreSQL for database
- [ ] Enable database connection pooling
- [ ] Implement caching (Redis)
- [ ] Use CDN for static files
- [ ] Enable gzip compression
- [ ] Monitor resource usage

### Reliability
- [ ] Set up health checks
- [ ] Configure auto-scaling
- [ ] Implement backup strategy
- [ ] Set up monitoring alerts
- [ ] Plan disaster recovery
- [ ] Load testing

### Monitoring
- [ ] Application logging
- [ ] Error tracking (Sentry)
- [ ] Performance monitoring
- [ ] Uptime monitoring
- [ ] Database monitoring

## Monitoring & Maintenance

### Health Checks
The application provides health check endpoints:
- Backend: `GET /health`
- Database: `GET /health/db`

### Logging
Configure structured logging in production:
```python
import logging
import json

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
```

### Monitoring Tools
- **Application Performance**: New Relic, DataDog
- **Error Tracking**: Sentry
- **Uptime Monitoring**: Pingdom, UptimeRobot
- **Log Management**: ELK Stack, Splunk

### Backup Strategy
```bash
# Database backup
pg_dump resume_checker > backup_$(date +%Y%m%d).sql

# File backup
rsync -av uploads/ backup/uploads/

# Automated backups (cron job)
0 2 * * * /path/to/backup_script.sh
```

### Updates & Maintenance
```bash
# Regular updates
pip install --upgrade -r requirements.txt

# Security patches
docker pull python:3.9
docker build --no-cache .

# Database migrations
alembic upgrade head
```

## Troubleshooting

### Common Issues

1. **Port conflicts**:
   ```bash
   netstat -tulpn | grep :8000
   kill -9 <PID>
   ```

2. **Database connection issues**:
   ```bash
   # Check database status
   pg_isready -h localhost -p 5432
   
   # Reset database
   python -c "from backend.app.database.init_db import create_tables; create_tables()"
   ```

3. **Memory issues**:
   ```bash
   # Monitor memory usage
   free -h
   
   # Increase swap space
   sudo fallocate -l 1G /swapfile
   sudo mkswap /swapfile
   sudo swapon /swapfile
   ```

### Getting Help
- Check application logs
- Review error messages
- Test in development environment
- Create GitHub issue with details

---

**Happy Deploying! 🚀**

For specific deployment questions or issues, please create an issue in the GitHub repository.
