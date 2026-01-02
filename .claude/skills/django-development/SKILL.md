---
name: django-development
description: Django and Django REST Framework development patterns. Use when building models, views, serializers, URLs, or API endpoints for the backend.
allowed-tools: Read, Write, Edit, Bash, Grep, Glob
---

# Django Development Skill

## Project Setup

### Initialize Django Project
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install django djangorestframework motor python-dotenv httpx anthropic

# Create project
django-admin startproject config backend
cd backend

# Create apps
python manage.py startapp members
python manage.py startapp bills
python manage.py startapp votes
python manage.py startapp finance
python manage.py startapp agent
```

### Project Structure
```
backend/
├── config/
│   ├── settings.py
│   ├── urls.py
│   └── asgi.py
├── members/
│   ├── models.py
│   ├── views.py
│   ├── serializers.py
│   ├── services.py
│   └── urls.py
├── bills/
├── votes/
├── finance/
├── agent/
└── manage.py
```

## Settings Configuration

### config/settings.py
```python
from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('DJANGO_SECRET_KEY')
DEBUG = os.getenv('DEBUG', 'False') == 'True'
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost').split(',')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'members',
    'bills',
    'votes',
    'finance',
    'agent',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    # ... rest of middleware
]

REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
}

CORS_ALLOWED_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:5173').split(',')

# MongoDB (using Motor for async)
MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017')
MONGODB_DB = os.getenv('MONGODB_DB', 'gov_watchdog')
```

## Model Patterns (Pydantic for MongoDB)

### members/models.py
```python
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class Term(BaseModel):
    congress: int
    chamber: str
    state: str
    district: Optional[int] = None
    start_date: datetime
    end_date: Optional[datetime] = None

class Member(BaseModel):
    bioguide_id: str = Field(..., description="Unique identifier")
    name: str
    first_name: str
    last_name: str
    party: str  # D, R, I
    state: str
    district: Optional[int] = None
    chamber: str  # house, senate
    terms: List[Term] = []
    image_url: Optional[str] = None
    contact: Optional[dict] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
```

## View Patterns

### members/views.py
```python
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .services import MemberService

class MemberListView(APIView):
    async def get(self, request):
        state = request.query_params.get('state')
        chamber = request.query_params.get('chamber')
        query = request.query_params.get('q')

        service = MemberService()
        members = await service.search(
            state=state,
            chamber=chamber,
            query=query,
        )

        return Response({
            'count': len(members),
            'results': members,
        })

class MemberDetailView(APIView):
    async def get(self, request, bioguide_id):
        service = MemberService()
        member = await service.get_by_id(bioguide_id)

        if not member:
            return Response(
                {'error': 'Member not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        return Response(member)
```

## Service Layer Pattern

### members/services.py
```python
from motor.motor_asyncio import AsyncIOMotorClient
from django.conf import settings

class MemberService:
    def __init__(self):
        self.client = AsyncIOMotorClient(settings.MONGODB_URI)
        self.db = self.client[settings.MONGODB_DB]
        self.collection = self.db.members

    async def search(self, state=None, chamber=None, query=None):
        filters = {}
        if state:
            filters['state'] = state.upper()
        if chamber:
            filters['chamber'] = chamber.lower()

        if query:
            filters['$text'] = {'$search': query}

        cursor = self.collection.find(filters).limit(100)
        members = await cursor.to_list(length=100)

        # Convert ObjectId to string
        for m in members:
            m['_id'] = str(m['_id'])

        return members

    async def get_by_id(self, bioguide_id: str):
        member = await self.collection.find_one({'bioguide_id': bioguide_id})
        if member:
            member['_id'] = str(member['_id'])
        return member
```

## URL Configuration

### config/urls.py
```python
from django.urls import path, include

urlpatterns = [
    path('api/v1/members/', include('members.urls')),
    path('api/v1/bills/', include('bills.urls')),
    path('api/v1/votes/', include('votes.urls')),
    path('api/v1/finance/', include('finance.urls')),
    path('api/v1/agent/', include('agent.urls')),
]
```

### members/urls.py
```python
from django.urls import path
from .views import MemberListView, MemberDetailView

urlpatterns = [
    path('', MemberListView.as_view(), name='member-list'),
    path('<str:bioguide_id>/', MemberDetailView.as_view(), name='member-detail'),
]
```

## Testing Patterns

### members/tests.py
```python
import pytest
from rest_framework.test import APIClient

@pytest.fixture
def api_client():
    return APIClient()

@pytest.mark.asyncio
async def test_member_list(api_client):
    response = api_client.get('/api/v1/members/')
    assert response.status_code == 200
    assert 'results' in response.json()

@pytest.mark.asyncio
async def test_member_search_by_state(api_client):
    response = api_client.get('/api/v1/members/?state=CA')
    assert response.status_code == 200
    for member in response.json()['results']:
        assert member['state'] == 'CA'
```

## Common Commands
```bash
# Run development server
python manage.py runserver

# Run tests
pytest

# Create migrations (if using Django models)
python manage.py makemigrations

# Apply migrations
python manage.py migrate
```
