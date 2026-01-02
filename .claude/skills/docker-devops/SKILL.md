---
name: docker-devops
description: Docker and deployment configuration. Use when creating Dockerfiles, docker-compose, or configuring deployment infrastructure.
allowed-tools: Read, Write, Edit, Bash
---

# Docker DevOps Skill

## Project Dockerfiles

### Backend Dockerfile (Django)
```dockerfile
# backend/Dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create non-root user
RUN adduser --disabled-password --gecos '' appuser
USER appuser

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "config.asgi:application", "-k", "uvicorn.workers.UvicornWorker"]
```

### Frontend Dockerfile (React + Vite)
```dockerfile
# frontend/Dockerfile
# Build stage
FROM node:20-alpine as build

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

# Production stage
FROM nginx:alpine

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

### Frontend Nginx Config
```nginx
# frontend/nginx.conf
server {
    listen 80;
    server_name localhost;
    root /usr/share/nginx/html;
    index index.html;

    # Handle SPA routing
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Proxy API requests to backend
    location /api/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Cache static assets
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

## Docker Compose

### Development Configuration
```yaml
# docker-compose.yml
version: '3.8'

services:
  mongodb:
    image: mongo:7
    ports:
      - "27017:27017"
    volumes:
      - mongodb_data:/data/db
    environment:
      MONGO_INITDB_ROOT_USERNAME: admin
      MONGO_INITDB_ROOT_PASSWORD: ${MONGO_PASSWORD:-devpassword}
    healthcheck:
      test: echo 'db.runCommand("ping").ok' | mongosh localhost:27017/test --quiet
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DEBUG=True
      - MONGODB_URI=mongodb://admin:${MONGO_PASSWORD:-devpassword}@mongodb:27017
      - MONGODB_DB=gov_watchdog
      - DJANGO_SECRET_KEY=${DJANGO_SECRET_KEY:-dev-secret-key}
      - CONGRESS_API_KEY=${CONGRESS_API_KEY}
      - FEC_API_KEY=${FEC_API_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
    depends_on:
      mongodb:
        condition: service_healthy
    volumes:
      - ./backend:/app  # Hot reload in dev

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.dev
    ports:
      - "5173:5173"
    environment:
      - VITE_API_URL=http://localhost:8000
    volumes:
      - ./frontend:/app
      - /app/node_modules
    depends_on:
      - backend

volumes:
  mongodb_data:
```

### Production Configuration
```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  mongodb:
    image: mongo:7
    volumes:
      - mongodb_data:/data/db
    environment:
      MONGO_INITDB_ROOT_USERNAME: ${MONGO_USER}
      MONGO_INITDB_ROOT_PASSWORD: ${MONGO_PASSWORD}
    restart: always
    networks:
      - backend-network

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    environment:
      - DEBUG=False
      - MONGODB_URI=mongodb://${MONGO_USER}:${MONGO_PASSWORD}@mongodb:27017
      - MONGODB_DB=gov_watchdog
      - DJANGO_SECRET_KEY=${DJANGO_SECRET_KEY}
      - ALLOWED_HOSTS=${ALLOWED_HOSTS}
      - CONGRESS_API_KEY=${CONGRESS_API_KEY}
      - FEC_API_KEY=${FEC_API_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
    depends_on:
      - mongodb
    restart: always
    networks:
      - backend-network
      - frontend-network

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "80:80"
      - "443:443"
    depends_on:
      - backend
    restart: always
    networks:
      - frontend-network

networks:
  backend-network:
    driver: bridge
  frontend-network:
    driver: bridge

volumes:
  mongodb_data:
```

### Frontend Dev Dockerfile
```dockerfile
# frontend/Dockerfile.dev
FROM node:20-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
```

## Environment Files

### .env.example
```bash
# MongoDB
MONGO_USER=admin
MONGO_PASSWORD=your_secure_password

# Django
DJANGO_SECRET_KEY=your_secret_key
DEBUG=False
ALLOWED_HOSTS=localhost,yourdomain.com

# External APIs
CONGRESS_API_KEY=your_congress_api_key
FEC_API_KEY=your_fec_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key

# Frontend
VITE_API_URL=http://localhost:8000
```

## Common Docker Commands

```bash
# Development
docker-compose up -d              # Start all services
docker-compose logs -f backend    # Follow backend logs
docker-compose exec backend bash  # Shell into backend
docker-compose down               # Stop all services
docker-compose down -v            # Stop and remove volumes

# Production
docker-compose -f docker-compose.prod.yml up -d --build

# Maintenance
docker system prune -a            # Clean unused images
docker volume prune               # Clean unused volumes

# MongoDB backup
docker-compose exec mongodb mongodump --out /dump
docker cp $(docker-compose ps -q mongodb):/dump ./backup
```

## Health Checks

### Backend Health Endpoint
```python
# backend/config/views.py
from rest_framework.decorators import api_view
from rest_framework.response import Response
from config.database import mongodb

@api_view(['GET'])
async def health_check(request):
    try:
        await mongodb.client.admin.command('ping')
        db_status = 'healthy'
    except Exception:
        db_status = 'unhealthy'

    return Response({
        'status': 'healthy' if db_status == 'healthy' else 'unhealthy',
        'database': db_status,
    })
```

## CI/CD GitHub Actions
```yaml
# .github/workflows/deploy.yml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Build and push images
        run: |
          docker-compose -f docker-compose.prod.yml build
          # Push to registry...

      - name: Deploy to server
        run: |
          # SSH and deploy...
```
