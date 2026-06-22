# Foundation Implementation Plan (Phase 1–2): Scaffold + Auth + Store

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stand up the full project scaffold with working OTP authentication, JWT tokens, and store management API — the foundation every subsequent phase builds on.

**Architecture:** Monorepo with `/backend` (Django DRF) and `/frontend` (Next.js 14). Backend is a pure JSON REST API. Multi-tenancy via row-level isolation: every tenant-scoped model has a `tenant_id` FK to `Store`, and a `TenantViewSetMixin` auto-filters all querysets. JWT payload carries `tenant_id` so the tenant is always resolved from the token.

**Tech Stack:** Django 5.1, DRF 3.15, djangorestframework-simplejwt, PostgreSQL 16 (ArrayField for pin codes), Redis 7 (rate limiting + Celery broker), bcrypt (OTP hashing), python-decouple (env vars), Next.js 14 App Router, TailwindCSS, Zustand

## Global Constraints

- No git commits — user has disabled git for this project
- Python 3.12+
- Node 20+
- All API routes prefixed `/api/v1/`
- OTP: mock provider in dev (log to console), abstracted behind `send_otp(phone, otp)` in `apps/authentication/services.py`
- JWT access token: 1 hour, refresh token: 30 days
- OTP: 6 digits, expires 5 min, max 3 requests/10 min per phone, max 5 failed verify attempts before 15-min lockout
- All secrets in `.env` only — never committed, documented in `.env.example`
- Test coverage target: 80%+
- `AUTH_USER_MODEL = 'authentication.User'` — must be set before first migration

---

## File Map

```
/                                        # repo root
├── docker-compose.yml
├── .env.example
├── CLAUDE.md
├── backend/
│   ├── manage.py
│   ├── pytest.ini
│   ├── Dockerfile.dev
│   ├── requirements/
│   │   ├── base.txt
│   │   ├── development.txt
│   │   └── production.txt
│   ├── config/
│   │   ├── __init__.py
│   │   ├── urls.py
│   │   ├── wsgi.py
│   │   ├── celery.py
│   │   └── settings/
│   │       ├── __init__.py
│   │       ├── base.py
│   │       ├── development.py
│   │       └── production.py
│   ├── apps/
│   │   ├── __init__.py
│   │   ├── tenants/
│   │   │   ├── __init__.py
│   │   │   ├── models.py        # Store, TenantModel (abstract)
│   │   │   ├── mixins.py        # TenantViewSetMixin
│   │   │   ├── serializers.py   # StoreSerializer
│   │   │   ├── views.py         # StoreView
│   │   │   ├── urls.py
│   │   │   └── admin.py
│   │   └── authentication/
│   │       ├── __init__.py
│   │       ├── models.py        # User, CustomerProfile, OTPVerification
│   │       ├── managers.py      # UserManager
│   │       ├── tokens.py        # TenantRefreshToken (custom JWT)
│   │       ├── services.py      # send_otp, OTPService, RateLimitService
│   │       ├── serializers.py   # OTPRequestSerializer, OTPVerifySerializer
│   │       ├── views.py         # OTPRequestView, OTPVerifyView, TokenRefreshView
│   │       ├── urls.py
│   │       └── admin.py
│   └── tests/
│       ├── conftest.py
│       ├── tenants/
│       │   ├── __init__.py
│       │   └── test_store.py
│       └── authentication/
│           ├── __init__.py
│           ├── test_otp_service.py
│           ├── test_otp_endpoints.py
│           └── test_jwt.py
└── frontend/
    ├── Dockerfile.dev
    ├── next.config.ts
    ├── tailwind.config.ts
    ├── tsconfig.json
    ├── package.json
    ├── app/
    │   ├── layout.tsx
    │   ├── (auth)/
    │   │   └── login/
    │   │       └── page.tsx     # OTP login flow
    │   └── (store)/
    │       └── page.tsx         # home placeholder
    ├── components/
    │   └── ui/
    │       ├── Button.tsx
    │       └── Input.tsx
    ├── lib/
    │   ├── api.ts               # typed fetch wrapper, auto token refresh
    │   └── auth.ts              # token storage helpers
    └── store/
        └── auth.ts              # Zustand auth state
```

---

### Task 1: Project Scaffold + Docker

**Files:**
- Create: `docker-compose.yml`
- Create: `.env.example`
- Create: `CLAUDE.md`
- Create: `backend/Dockerfile.dev`
- Create: `frontend/Dockerfile.dev`
- Create: `backend/requirements/base.txt`
- Create: `backend/requirements/development.txt`
- Create: `backend/requirements/production.txt`

**Interfaces:**
- Produces: running Docker Compose stack (db, redis, backend, celery, frontend)

- [ ] **Step 1: Create root directory structure**

```bash
mkdir -p backend/requirements backend/config/settings backend/apps frontend
touch backend/__init__.py backend/apps/__init__.py
```

- [ ] **Step 2: Write requirements files**

`backend/requirements/base.txt`:
```
Django==5.1
djangorestframework==3.15.2
djangorestframework-simplejwt==5.3.1
django-cors-headers==4.4.0
drf-spectacular==0.27.2
psycopg2-binary==2.9.9
redis==5.0.8
celery==5.4.0
django-redis==5.4.0
bcrypt==4.2.0
python-decouple==3.8
django-storages[s3]==1.14.4
Pillow==10.4.0
```

`backend/requirements/development.txt`:
```
-r base.txt
pytest==8.3.2
pytest-django==4.9.0
pytest-cov==5.0.0
factory-boy==3.3.1
Faker==30.3.0
```

`backend/requirements/production.txt`:
```
-r base.txt
gunicorn==23.0.0
```

- [ ] **Step 3: Write backend Dockerfile.dev**

`backend/Dockerfile.dev`:
```dockerfile
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y libpq-dev gcc && rm -rf /var/lib/apt/lists/*

COPY requirements/development.txt requirements/development.txt
RUN pip install --no-cache-dir -r requirements/development.txt

COPY . .
```

- [ ] **Step 4: Write frontend Dockerfile.dev**

`frontend/Dockerfile.dev`:
```dockerfile
FROM node:20-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

EXPOSE 3000
CMD ["npm", "run", "dev"]
```

- [ ] **Step 5: Write docker-compose.yml**

```yaml
version: '3.9'

services:
  db:
    image: postgres:16-alpine
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.dev
    volumes:
      - ./backend:/app
    ports:
      - "8000:8000"
    env_file: .env
    environment:
      - DJANGO_SETTINGS_MODULE=config.settings.development
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_started
    command: python manage.py runserver 0.0.0.0:8000

  celery:
    build:
      context: ./backend
      dockerfile: Dockerfile.dev
    volumes:
      - ./backend:/app
    env_file: .env
    environment:
      - DJANGO_SETTINGS_MODULE=config.settings.development
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_started
    command: celery -A config worker -l info

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.dev
    volumes:
      - ./frontend:/app
      - /app/node_modules
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000

volumes:
  postgres_data:
```

- [ ] **Step 6: Write .env.example**

```bash
# Django
SECRET_KEY=change-me-to-a-50-char-random-string
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
POSTGRES_DB=commerce_db
POSTGRES_USER=commerce_user
POSTGRES_PASSWORD=change-me
DB_HOST=db
DB_PORT=5432

# Redis
REDIS_URL=redis://redis:6379/0

# JWT
JWT_ACCESS_TOKEN_LIFETIME_HOURS=1
JWT_REFRESH_TOKEN_LIFETIME_DAYS=30

# OTP
OTP_EXPIRY_MINUTES=5
OTP_MAX_ATTEMPTS=5
OTP_RATE_LIMIT_COUNT=3
OTP_RATE_LIMIT_WINDOW_MINUTES=10
OTP_LOCKOUT_MINUTES=15

# OTP Provider (mock | msg91 | fast2sms)
OTP_PROVIDER=mock

# Storage - Cloudflare R2
R2_ACCESS_KEY_ID=
R2_SECRET_ACCESS_KEY=
R2_BUCKET_NAME=
R2_ENDPOINT_URL=
R2_CUSTOM_DOMAIN=

# Razorpay
RAZORPAY_KEY_ID=
RAZORPAY_KEY_SECRET=
RAZORPAY_MODE=test

# WhatsApp (set before Phase 9)
WHATSAPP_PROVIDER=mock
WHATSAPP_API_KEY=

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:3000
```

- [ ] **Step 7: Write CLAUDE.md**

```markdown
# Multi-Tenant Hardware & Sanitary Commerce Platform

## Progress

| Phase | Description | Status |
|-------|-------------|--------|
| 1 | Auth — OTP + JWT | 🚧 In Progress |
| 2 | Store setup | 🚧 In Progress |
| 3 | Category system | ⏳ Pending |
| 4 | Product catalog | ⏳ Pending |
| 5 | Inventory | ⏳ Pending |
| 6 | Product discovery | ⏳ Pending |
| 7 | Cart | ⏳ Pending |
| 8 | Checkout | ⏳ Pending |
| 9 | Order management | ⏳ Pending |
| 10 | Payments | ⏳ Pending |

## Current Plan
docs/superpowers/plans/2026-06-20-plan-1-foundation.md

## Spec
docs/superpowers/specs/2026-06-20-platform-design.md

## Key Decisions
- Multi-tenancy: row-level isolation via tenant_id FK on every model
- Auth: OTP (phone) + JWT; SMS provider abstracted behind send_otp()
- Delivery: pin code allowlist now, lat/lng haversine later
- Payments: COD + Razorpay (test mode → live on KYC)
- No git commits in this project

## Running the project
```bash
cp .env.example .env   # fill in values
docker-compose up
```

Backend API: http://localhost:8000/api/v1/
API docs: http://localhost:8000/api/schema/swagger-ui/
Frontend: http://localhost:3000
```

- [ ] **Step 8: Verify Docker Compose config is valid**

```bash
docker-compose config
```
Expected: prints the resolved config with no errors.

---

### Task 2: Django Base Configuration

**Files:**
- Create: `backend/manage.py`
- Create: `backend/config/__init__.py`
- Create: `backend/config/settings/__init__.py`
- Create: `backend/config/settings/base.py`
- Create: `backend/config/settings/development.py`
- Create: `backend/config/settings/production.py`
- Create: `backend/config/urls.py`
- Create: `backend/config/wsgi.py`
- Create: `backend/config/celery.py`
- Create: `backend/pytest.ini`

**Interfaces:**
- Produces: importable Django settings, runnable `manage.py`

- [ ] **Step 1: Write manage.py**

```python
#!/usr/bin/env python
import os
import sys

def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError("Couldn't import Django.") from exc
    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()
```

- [ ] **Step 2: Write base settings**

`backend/config/settings/base.py`:
```python
from datetime import timedelta
from pathlib import Path
from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost').split(',')

DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.postgres',
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'drf_spectacular',
]

LOCAL_APPS = [
    'apps.tenants',
    'apps.authentication',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('POSTGRES_DB'),
        'USER': config('POSTGRES_USER'),
        'PASSWORD': config('POSTGRES_PASSWORD'),
        'HOST': config('DB_HOST', default='db'),
        'PORT': config('DB_PORT', default='5432'),
    }
}

AUTH_USER_MODEL = 'authentication.User'

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': config('REDIS_URL', default='redis://redis:6379/0'),
        'OPTIONS': {'CLIENT_CLASS': 'django_redis.client.DefaultClient'},
    }
}

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(
        hours=config('JWT_ACCESS_TOKEN_LIFETIME_HOURS', default=1, cast=int)
    ),
    'REFRESH_TOKEN_LIFETIME': timedelta(
        days=config('JWT_REFRESH_TOKEN_LIFETIME_DAYS', default=30, cast=int)
    ),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': False,
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'Commerce Platform API',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
}

CELERY_BROKER_URL = config('REDIS_URL', default='redis://redis:6379/0')
CELERY_RESULT_BACKEND = config('REDIS_URL', default='redis://redis:6379/0')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

CORS_ALLOWED_ORIGINS = config('CORS_ALLOWED_ORIGINS', default='http://localhost:3000').split(',')

# OTP settings
OTP_EXPIRY_MINUTES = config('OTP_EXPIRY_MINUTES', default=5, cast=int)
OTP_MAX_ATTEMPTS = config('OTP_MAX_ATTEMPTS', default=5, cast=int)
OTP_RATE_LIMIT_COUNT = config('OTP_RATE_LIMIT_COUNT', default=3, cast=int)
OTP_RATE_LIMIT_WINDOW_MINUTES = config('OTP_RATE_LIMIT_WINDOW_MINUTES', default=10, cast=int)
OTP_LOCKOUT_MINUTES = config('OTP_LOCKOUT_MINUTES', default=15, cast=int)
OTP_PROVIDER = config('OTP_PROVIDER', default='mock')
```

- [ ] **Step 3: Write development settings**

`backend/config/settings/development.py`:
```python
from .base import *

DEBUG = True
CORS_ALLOW_ALL_ORIGINS = True
```

- [ ] **Step 4: Write production settings**

`backend/config/settings/production.py`:
```python
from .base import *

DEBUG = False
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
AWS_ACCESS_KEY_ID = config('R2_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = config('R2_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = config('R2_BUCKET_NAME')
AWS_S3_ENDPOINT_URL = config('R2_ENDPOINT_URL')
AWS_S3_CUSTOM_DOMAIN = config('R2_CUSTOM_DOMAIN', default='')
AWS_DEFAULT_ACL = 'public-read'
```

- [ ] **Step 5: Write config/urls.py**

```python
from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/auth/', include('apps.authentication.urls')),
    path('api/v1/', include('apps.tenants.urls')),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]
```

- [ ] **Step 6: Write wsgi.py and celery.py**

`backend/config/wsgi.py`:
```python
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
application = get_wsgi_application()
```

`backend/config/celery.py`:
```python
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

app = Celery('commerce')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
```

`backend/config/__init__.py`:
```python
from .celery import app as celery_app

__all__ = ('celery_app',)
```

- [ ] **Step 7: Write pytest.ini**

`backend/pytest.ini`:
```ini
[pytest]
DJANGO_SETTINGS_MODULE = config.settings.development
python_files = tests/*/test_*.py
python_classes = Test*
python_functions = test_*
addopts = --cov=apps --cov-report=term-missing --cov-fail-under=80
```

- [ ] **Step 8: Verify Django imports cleanly**

From inside the `backend/` directory:
```bash
DJANGO_SETTINGS_MODULE=config.settings.development python -c "import django; django.setup(); print('OK')"
```
Expected: `OK`

---

### Task 3: Tenants App — Store Model + TenantModel

**Files:**
- Create: `backend/apps/tenants/__init__.py`
- Create: `backend/apps/tenants/models.py`
- Create: `backend/apps/tenants/admin.py`
- Create: `backend/tests/tenants/__init__.py`
- Create: `backend/tests/tenants/test_store.py`
- Create: `backend/tests/conftest.py`

**Interfaces:**
- Produces:
  - `Store` model with fields: `id, name, slug, phone, address, logo, delivery_pin_codes, delivery_radius_km, is_active, created_at`
  - `TenantModel` abstract base with `tenant = ForeignKey(Store)`
  - `Store` importable as `from apps.tenants.models import Store, TenantModel`

- [ ] **Step 1: Write the failing test**

`backend/tests/conftest.py`:
```python
import pytest
from django.contrib.postgres.fields import ArrayField

@pytest.fixture
def store(db):
    from apps.tenants.models import Store
    return Store.objects.create(
        name='Test Hardware Store',
        slug='test-hardware-store',
        phone='9876543210',
        address='123 Main St, Mumbai',
        delivery_pin_codes=['400001', '400002'],
    )
```

`backend/tests/tenants/test_store.py`:
```python
import pytest

@pytest.mark.django_db
def test_store_creation(store):
    assert store.id is not None
    assert store.name == 'Test Hardware Store'
    assert store.is_active is True
    assert '400001' in store.delivery_pin_codes

@pytest.mark.django_db
def test_store_pin_code_check(store):
    assert store.is_pin_code_serviceable('400001') is True
    assert store.is_pin_code_serviceable('999999') is False
```

- [ ] **Step 2: Run test — verify it fails**

```bash
cd backend && pytest tests/tenants/test_store.py -v
```
Expected: `ImportError` or `ModuleNotFoundError` for `apps.tenants.models`

- [ ] **Step 3: Write Store model**

`backend/apps/tenants/models.py`:
```python
from django.contrib.postgres.fields import ArrayField
from django.db import models


class Store(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    phone = models.CharField(max_length=15)
    address = models.TextField()
    logo = models.URLField(blank=True)
    delivery_pin_codes = ArrayField(
        models.CharField(max_length=10), default=list, blank=True
    )
    delivery_radius_km = models.IntegerField(default=15)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    def is_pin_code_serviceable(self, pin_code: str) -> bool:
        return pin_code in self.delivery_pin_codes


class TenantModel(models.Model):
    tenant = models.ForeignKey(
        Store, on_delete=models.CASCADE, related_name='+'
    )

    class Meta:
        abstract = True
```

`backend/apps/tenants/admin.py`:
```python
from django.contrib import admin
from .models import Store

@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'phone', 'is_active')
    prepopulated_fields = {'slug': ('name',)}
```

- [ ] **Step 4: Create and run migration**

```bash
cd backend && python manage.py makemigrations tenants && python manage.py migrate
```
Expected: migration created and applied, no errors.

- [ ] **Step 5: Run tests — verify they pass**

```bash
cd backend && pytest tests/tenants/test_store.py -v
```
Expected: 2 tests PASS

---

### Task 4: TenantViewSetMixin

**Files:**
- Create: `backend/apps/tenants/mixins.py`
- Modify: `backend/tests/tenants/test_store.py` (add mixin tests)

**Interfaces:**
- Produces:
  - `TenantViewSetMixin` class importable from `apps.tenants.mixins`
  - Method: `get_tenant(request) -> Store`
  - Auto-filters querysets to `tenant_id = request.auth['tenant_id']`
  - Auto-injects `tenant_id` on `perform_create`

- [ ] **Step 1: Write the failing test**

Add to `backend/tests/tenants/test_store.py`:
```python
from unittest.mock import MagicMock
from apps.tenants.mixins import TenantViewSetMixin
from apps.tenants.models import Store, TenantModel

@pytest.mark.django_db
def test_tenant_mixin_filters_queryset(store):
    other_store = Store.objects.create(
        name='Other Store', slug='other-store', phone='1234567890', address='Other'
    )

    # TenantModel subclass for testing
    class MockModel(TenantModel):
        class Meta:
            app_label = 'tenants'

    mixin = TenantViewSetMixin()
    mixin.request = MagicMock()
    mixin.request.auth = {'tenant_id': store.id}

    assert mixin.get_tenant() == store

@pytest.mark.django_db
def test_get_tenant_raises_on_missing_id(store):
    mixin = TenantViewSetMixin()
    mixin.request = MagicMock()
    mixin.request.auth = {}

    with pytest.raises(Exception):
        mixin.get_tenant()
```

- [ ] **Step 2: Run test — verify it fails**

```bash
cd backend && pytest tests/tenants/test_store.py::test_tenant_mixin_filters_queryset -v
```
Expected: `ImportError` for `apps.tenants.mixins`

- [ ] **Step 3: Write TenantViewSetMixin**

`backend/apps/tenants/mixins.py`:
```python
from apps.tenants.models import Store


class TenantViewSetMixin:
    """
    Mixin for all tenant-scoped DRF ViewSets.
    Reads tenant_id from JWT payload, filters querysets, injects on create.
    """

    def get_tenant(self) -> Store:
        tenant_id = self.request.auth.get('tenant_id')
        if not tenant_id:
            raise ValueError("No tenant_id in token")
        return Store.objects.get(id=tenant_id)

    def get_queryset(self):
        tenant_id = self.request.auth.get('tenant_id')
        return super().get_queryset().filter(tenant_id=tenant_id)

    def perform_create(self, serializer):
        tenant = self.get_tenant()
        serializer.save(tenant=tenant)
```

- [ ] **Step 4: Run tests — verify they pass**

```bash
cd backend && pytest tests/tenants/ -v
```
Expected: all tests PASS

---

### Task 5: Authentication App — User + OTPVerification Models

**Files:**
- Create: `backend/apps/authentication/__init__.py`
- Create: `backend/apps/authentication/managers.py`
- Create: `backend/apps/authentication/models.py`
- Create: `backend/apps/authentication/admin.py`
- Create: `backend/tests/authentication/__init__.py`
- Create: `backend/tests/authentication/test_models.py`

**Interfaces:**
- Produces:
  - `User` model: `id, phone, email, full_name, is_store_owner, is_active, is_staff, date_joined`
  - `CustomerProfile` model: `user (FK), tenant (FK → Store), created_at`
  - `OTPVerification` model: `phone, otp_hash, expires_at, is_used, attempt_count, created_at`
  - All importable from `apps.authentication.models`

- [ ] **Step 1: Write the failing tests**

`backend/tests/authentication/test_models.py`:
```python
import pytest
from django.utils import timezone
from datetime import timedelta


@pytest.mark.django_db
def test_user_creation_with_phone():
    from apps.authentication.models import User
    user = User.objects.create_user(phone='9876543210')
    assert user.phone == '9876543210'
    assert user.is_active is True
    assert user.is_store_owner is False
    assert user.email is None


@pytest.mark.django_db
def test_user_phone_is_unique():
    from apps.authentication.models import User
    from django.db import IntegrityError
    User.objects.create_user(phone='9876543210')
    with pytest.raises(IntegrityError):
        User.objects.create_user(phone='9876543210')


@pytest.mark.django_db
def test_customer_profile_created(store):
    from apps.authentication.models import User, CustomerProfile
    user = User.objects.create_user(phone='9876543210')
    profile = CustomerProfile.objects.create(user=user, tenant=store)
    assert profile.user == user
    assert profile.tenant == store


@pytest.mark.django_db
def test_otp_verification_model():
    from apps.authentication.models import OTPVerification
    otp = OTPVerification.objects.create(
        phone='9876543210',
        otp_hash='hashed_value',
        expires_at=timezone.now() + timedelta(minutes=5),
    )
    assert otp.is_used is False
    assert otp.attempt_count == 0
```

- [ ] **Step 2: Run test — verify it fails**

```bash
cd backend && pytest tests/authentication/test_models.py -v
```
Expected: `ImportError` for `apps.authentication.models`

- [ ] **Step 3: Write UserManager**

`backend/apps/authentication/managers.py`:
```python
from django.contrib.auth.models import BaseUserManager


class UserManager(BaseUserManager):
    def create_user(self, phone, password=None, **extra_fields):
        if not phone:
            raise ValueError('Phone number is required')
        user = self.model(phone=phone, **extra_fields)
        user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, phone, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_store_owner', True)
        user = self.create_user(phone, password, **extra_fields)
        if password:
            user.set_password(password)
            user.save(using=self._db)
        return user
```

- [ ] **Step 4: Write authentication models**

`backend/apps/authentication/models.py`:
```python
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from .managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    phone = models.CharField(max_length=15, unique=True)
    email = models.EmailField(blank=True, null=True)
    full_name = models.CharField(max_length=255, blank=True)
    is_store_owner = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.phone


class CustomerProfile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='profiles')
    tenant = models.ForeignKey('tenants.Store', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'tenant')

    def __str__(self):
        return f"{self.user.phone} @ {self.tenant.name}"


class OTPVerification(models.Model):
    phone = models.CharField(max_length=15)
    otp_hash = models.CharField(max_length=255)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    attempt_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=['phone', 'created_at'])]

    def __str__(self):
        return f"OTP for {self.phone}"
```

`backend/apps/authentication/admin.py`:
```python
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, CustomerProfile, OTPVerification


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('phone', 'email', 'full_name', 'is_store_owner', 'is_active')
    fieldsets = (
        (None, {'fields': ('phone', 'password')}),
        ('Info', {'fields': ('email', 'full_name')}),
        ('Permissions', {'fields': ('is_store_owner', 'is_active', 'is_staff', 'is_superuser')}),
    )
    add_fieldsets = (
        (None, {'fields': ('phone',)}),
    )
    search_fields = ('phone', 'email')
    ordering = ('phone',)
    filter_horizontal = ()


@admin.register(CustomerProfile)
class CustomerProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'tenant', 'created_at')


@admin.register(OTPVerification)
class OTPVerificationAdmin(admin.ModelAdmin):
    list_display = ('phone', 'is_used', 'expires_at', 'attempt_count')
```

- [ ] **Step 5: Create and run migration**

```bash
cd backend && python manage.py makemigrations authentication && python manage.py migrate
```
Expected: migration applied, no errors.

- [ ] **Step 6: Run tests — verify they pass**

```bash
cd backend && pytest tests/authentication/test_models.py -v
```
Expected: 4 tests PASS

---

### Task 6: OTP Service (Generate, Hash, Verify, Rate Limit)

**Files:**
- Create: `backend/apps/authentication/services.py`
- Create: `backend/tests/authentication/test_otp_service.py`

**Interfaces:**
- Produces:
  - `generate_otp() -> str` — 6-digit string
  - `hash_otp(otp: str) -> str` — bcrypt hash
  - `verify_otp_hash(otp: str, otp_hash: str) -> bool`
  - `send_otp(phone: str, otp: str) -> None` — mock: logs to console
  - `OTPRateLimitService.check_rate_limit(phone: str) -> None` — raises `RateLimitExceeded` if over limit
  - `OTPRateLimitService.check_lockout(phone: str) -> None` — raises `AccountLocked` if locked out
  - `OTPRateLimitService.record_failed_attempt(phone: str) -> None`
  - All importable from `apps.authentication.services`

- [ ] **Step 1: Write the failing tests**

`backend/tests/authentication/test_otp_service.py`:
```python
import pytest
from unittest.mock import patch
from apps.authentication.services import (
    generate_otp, hash_otp, verify_otp_hash, send_otp,
    OTPRateLimitService, RateLimitExceeded, AccountLocked,
)


def test_generate_otp_is_6_digits():
    otp = generate_otp()
    assert len(otp) == 6
    assert otp.isdigit()


def test_otp_hash_and_verify():
    otp = '123456'
    hashed = hash_otp(otp)
    assert verify_otp_hash(otp, hashed) is True
    assert verify_otp_hash('999999', hashed) is False


def test_send_otp_mock_logs(capsys):
    send_otp('9876543210', '123456')
    captured = capsys.readouterr()
    assert '123456' in captured.out


@pytest.mark.django_db
def test_rate_limit_blocks_after_threshold(store):
    phone = '9876543210'
    service = OTPRateLimitService()
    # First 3 should pass
    for _ in range(3):
        service.check_rate_limit(phone)
        service.record_otp_request(phone)
    # 4th should raise
    with pytest.raises(RateLimitExceeded):
        service.check_rate_limit(phone)


@pytest.mark.django_db
def test_lockout_blocks_after_failed_attempts():
    phone = '9876543210'
    service = OTPRateLimitService()
    for _ in range(5):
        service.record_failed_attempt(phone)
    with pytest.raises(AccountLocked):
        service.check_lockout(phone)
```

- [ ] **Step 2: Run test — verify it fails**

```bash
cd backend && pytest tests/authentication/test_otp_service.py -v
```
Expected: `ImportError` for `apps.authentication.services`

- [ ] **Step 3: Write services.py**

`backend/apps/authentication/services.py`:
```python
import random
import string
import bcrypt
import logging
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


class RateLimitExceeded(Exception):
    pass


class AccountLocked(Exception):
    pass


def generate_otp() -> str:
    return ''.join(random.choices(string.digits, k=6))


def hash_otp(otp: str) -> str:
    return bcrypt.hashpw(otp.encode(), bcrypt.gensalt()).decode()


def verify_otp_hash(otp: str, otp_hash: str) -> bool:
    return bcrypt.checkpw(otp.encode(), otp_hash.encode())


def send_otp(phone: str, otp: str) -> None:
    provider = settings.OTP_PROVIDER
    if provider == 'mock':
        # ponytail: mock provider — swap body here for real SMS
        print(f"[OTP] Phone: {phone}, OTP: {otp}")
        logger.info(f"OTP for {phone}: {otp}")
        return
    raise NotImplementedError(f"OTP provider '{provider}' not implemented")


class OTPRateLimitService:
    def _rate_limit_key(self, phone: str) -> str:
        return f"otp:rate:{phone}"

    def _lockout_key(self, phone: str) -> str:
        return f"otp:lockout:{phone}"

    def _failed_key(self, phone: str) -> str:
        return f"otp:failed:{phone}"

    def check_rate_limit(self, phone: str) -> None:
        key = self._rate_limit_key(phone)
        count = cache.get(key, 0)
        if count >= settings.OTP_RATE_LIMIT_COUNT:
            raise RateLimitExceeded(
                f"Max {settings.OTP_RATE_LIMIT_COUNT} OTP requests per "
                f"{settings.OTP_RATE_LIMIT_WINDOW_MINUTES} minutes"
            )

    def record_otp_request(self, phone: str) -> None:
        key = self._rate_limit_key(phone)
        count = cache.get(key, 0)
        ttl = settings.OTP_RATE_LIMIT_WINDOW_MINUTES * 60
        cache.set(key, count + 1, timeout=ttl)

    def check_lockout(self, phone: str) -> None:
        if cache.get(self._lockout_key(phone)):
            raise AccountLocked("Account temporarily locked. Try again later.")

    def record_failed_attempt(self, phone: str) -> None:
        key = self._failed_key(phone)
        count = cache.get(key, 0) + 1
        cache.set(key, count, timeout=settings.OTP_MAX_ATTEMPTS * 60)
        if count >= settings.OTP_MAX_ATTEMPTS:
            lockout_ttl = settings.OTP_LOCKOUT_MINUTES * 60
            cache.set(self._lockout_key(phone), True, timeout=lockout_ttl)
            cache.delete(key)

    def clear_failed_attempts(self, phone: str) -> None:
        cache.delete(self._failed_key(phone))
        cache.delete(self._lockout_key(phone))
```

- [ ] **Step 4: Run tests — verify they pass**

```bash
cd backend && pytest tests/authentication/test_otp_service.py -v
```
Expected: 5 tests PASS

---

### Task 7: Custom JWT Token

**Files:**
- Create: `backend/apps/authentication/tokens.py`
- Create: `backend/tests/authentication/test_jwt.py`

**Interfaces:**
- Produces:
  - `TenantRefreshToken.for_user_and_store(user, store)` — returns refresh token with `tenant_id, phone, is_store_owner` in payload
  - Importable as `from apps.authentication.tokens import TenantRefreshToken`

- [ ] **Step 1: Write the failing test**

`backend/tests/authentication/test_jwt.py`:
```python
import pytest
from apps.authentication.tokens import TenantRefreshToken


@pytest.mark.django_db
def test_token_contains_tenant_id(store):
    from apps.authentication.models import User
    user = User.objects.create_user(phone='9876543210')

    refresh = TenantRefreshToken.for_user_and_store(user, store)
    access = refresh.access_token

    assert access['tenant_id'] == store.id
    assert access['phone'] == '9876543210'
    assert access['is_store_owner'] is False
    assert 'user_id' in access
```

- [ ] **Step 2: Run test — verify it fails**

```bash
cd backend && pytest tests/authentication/test_jwt.py -v
```
Expected: `ImportError`

- [ ] **Step 3: Write tokens.py**

`backend/apps/authentication/tokens.py`:
```python
from rest_framework_simplejwt.tokens import RefreshToken


class TenantRefreshToken(RefreshToken):
    @classmethod
    def for_user_and_store(cls, user, store):
        token = cls.for_user(user)
        token['tenant_id'] = store.id
        token['phone'] = user.phone
        token['is_store_owner'] = user.is_store_owner
        # propagate to access token
        token.access_token['tenant_id'] = store.id
        token.access_token['phone'] = user.phone
        token.access_token['is_store_owner'] = user.is_store_owner
        return token
```

- [ ] **Step 4: Run tests — verify they pass**

```bash
cd backend && pytest tests/authentication/test_jwt.py -v
```
Expected: 1 test PASS

---

### Task 8: OTP Request + Verify Endpoints

**Files:**
- Create: `backend/apps/authentication/serializers.py`
- Create: `backend/apps/authentication/views.py`
- Create: `backend/apps/authentication/urls.py`
- Create: `backend/tests/authentication/test_otp_endpoints.py`

**Interfaces:**
- Produces:
  - `POST /api/v1/auth/otp/request/` — `{ phone }` → `{ message }`
  - `POST /api/v1/auth/otp/verify/` — `{ phone, otp }` → `{ access_token, refresh_token, is_new_user }`
  - `POST /api/v1/auth/token/refresh/` — `{ refresh }` → `{ access }`

- [ ] **Step 1: Write the failing tests**

`backend/tests/authentication/test_otp_endpoints.py`:
```python
import pytest
from django.urls import reverse


@pytest.fixture
def api_client():
    from rest_framework.test import APIClient
    return APIClient()


@pytest.fixture
def active_store(db):
    from apps.tenants.models import Store
    return Store.objects.create(
        name='Test Store', slug='test-store',
        phone='9999999999', address='Test Address',
        delivery_pin_codes=['400001'],
    )


@pytest.mark.django_db
def test_otp_request_success(api_client, active_store):
    response = api_client.post('/api/v1/auth/otp/request/', {'phone': '9876543210'})
    assert response.status_code == 200
    assert 'message' in response.data


@pytest.mark.django_db
def test_otp_request_invalid_phone(api_client, active_store):
    response = api_client.post('/api/v1/auth/otp/request/', {'phone': '123'})
    assert response.status_code == 400


@pytest.mark.django_db
def test_otp_verify_creates_new_user(api_client, active_store):
    from apps.authentication.models import OTPVerification
    from apps.authentication.services import hash_otp
    from django.utils import timezone
    from datetime import timedelta

    OTPVerification.objects.create(
        phone='9876543210',
        otp_hash=hash_otp('123456'),
        expires_at=timezone.now() + timedelta(minutes=5),
    )
    response = api_client.post('/api/v1/auth/otp/verify/', {
        'phone': '9876543210', 'otp': '123456'
    })
    assert response.status_code == 200
    assert 'access_token' in response.data
    assert 'refresh_token' in response.data
    assert response.data['is_new_user'] is True


@pytest.mark.django_db
def test_otp_verify_wrong_otp(api_client, active_store):
    from apps.authentication.models import OTPVerification
    from apps.authentication.services import hash_otp
    from django.utils import timezone
    from datetime import timedelta

    OTPVerification.objects.create(
        phone='9876543210',
        otp_hash=hash_otp('123456'),
        expires_at=timezone.now() + timedelta(minutes=5),
    )
    response = api_client.post('/api/v1/auth/otp/verify/', {
        'phone': '9876543210', 'otp': '999999'
    })
    assert response.status_code == 400


@pytest.mark.django_db
def test_otp_verify_expired_otp(api_client, active_store):
    from apps.authentication.models import OTPVerification
    from apps.authentication.services import hash_otp
    from django.utils import timezone
    from datetime import timedelta

    OTPVerification.objects.create(
        phone='9876543210',
        otp_hash=hash_otp('123456'),
        expires_at=timezone.now() - timedelta(minutes=1),
    )
    response = api_client.post('/api/v1/auth/otp/verify/', {
        'phone': '9876543210', 'otp': '123456'
    })
    assert response.status_code == 400
```

- [ ] **Step 2: Run test — verify it fails**

```bash
cd backend && pytest tests/authentication/test_otp_endpoints.py -v
```
Expected: URL resolution errors or 404s

- [ ] **Step 3: Write serializers**

`backend/apps/authentication/serializers.py`:
```python
import re
from django.utils import timezone
from rest_framework import serializers
from .models import OTPVerification
from .services import verify_otp_hash


class OTPRequestSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=15)

    def validate_phone(self, value):
        # Indian mobile numbers: 10 digits, starting with 6-9
        cleaned = re.sub(r'[\s\-\+]', '', value)
        if not re.match(r'^[6-9]\d{9}$', cleaned):
            raise serializers.ValidationError("Enter a valid 10-digit Indian mobile number.")
        return cleaned


class OTPVerifySerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=15)
    otp = serializers.CharField(min_length=6, max_length=6)

    def validate_phone(self, value):
        cleaned = re.sub(r'[\s\-\+]', '', value)
        if not re.match(r'^[6-9]\d{9}$', cleaned):
            raise serializers.ValidationError("Enter a valid 10-digit Indian mobile number.")
        return cleaned

    def validate(self, data):
        phone = data['phone']
        otp = data['otp']

        record = (
            OTPVerification.objects
            .filter(phone=phone, is_used=False)
            .order_by('-created_at')
            .first()
        )

        if not record:
            raise serializers.ValidationError("No OTP found for this number. Request a new one.")

        if record.expires_at < timezone.now():
            raise serializers.ValidationError("OTP has expired. Request a new one.")

        if not verify_otp_hash(otp, record.otp_hash):
            record.attempt_count += 1
            record.save(update_fields=['attempt_count'])
            raise serializers.ValidationError("Invalid OTP.")

        data['otp_record'] = record
        return data
```

- [ ] **Step 4: Write views**

`backend/apps/authentication/views.py`:
```python
from django.utils import timezone
from django.conf import settings
from datetime import timedelta
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from rest_framework_simplejwt.tokens import RefreshToken

from apps.tenants.models import Store
from .models import User, CustomerProfile, OTPVerification
from .serializers import OTPRequestSerializer, OTPVerifySerializer
from .services import generate_otp, hash_otp, send_otp, OTPRateLimitService, RateLimitExceeded, AccountLocked
from .tokens import TenantRefreshToken


class OTPRequestView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = OTPRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone = serializer.validated_data['phone']

        rate_service = OTPRateLimitService()
        try:
            rate_service.check_rate_limit(phone)
            rate_service.check_lockout(phone)
        except RateLimitExceeded as e:
            return Response({'error': str(e)}, status=status.HTTP_429_TOO_MANY_REQUESTS)
        except AccountLocked as e:
            return Response({'error': str(e)}, status=status.HTTP_429_TOO_MANY_REQUESTS)

        otp = generate_otp()
        otp_hash = hash_otp(otp)
        expires_at = timezone.now() + timedelta(minutes=settings.OTP_EXPIRY_MINUTES)

        OTPVerification.objects.create(phone=phone, otp_hash=otp_hash, expires_at=expires_at)
        rate_service.record_otp_request(phone)
        send_otp(phone, otp)

        return Response({'message': 'OTP sent successfully.'})


class OTPVerifyView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = OTPVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone = serializer.validated_data['phone']
        otp_record = serializer.validated_data['otp_record']

        rate_service = OTPRateLimitService()
        try:
            rate_service.check_lockout(phone)
        except AccountLocked as e:
            return Response({'error': str(e)}, status=status.HTTP_429_TOO_MANY_REQUESTS)

        otp_record.is_used = True
        otp_record.save(update_fields=['is_used'])
        rate_service.clear_failed_attempts(phone)

        # Get or create user
        user, is_new = User.objects.get_or_create(phone=phone)

        # Resolve store — single store for now
        store = Store.objects.filter(is_active=True).first()
        if not store:
            return Response({'error': 'No active store found.'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        # Create profile if new
        if is_new:
            CustomerProfile.objects.get_or_create(user=user, tenant=store)

        refresh = TenantRefreshToken.for_user_and_store(user, store)

        return Response({
            'access_token': str(refresh.access_token),
            'refresh_token': str(refresh),
            'is_new_user': is_new,
        })


class TokenRefreshView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response({'error': 'refresh token required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            refresh = RefreshToken(refresh_token)
            return Response({'access': str(refresh.access_token)})
        except (TokenError, InvalidToken) as e:
            return Response({'error': str(e)}, status=status.HTTP_401_UNAUTHORIZED)
```

- [ ] **Step 5: Write auth URLs**

`backend/apps/authentication/urls.py`:
```python
from django.urls import path
from .views import OTPRequestView, OTPVerifyView, TokenRefreshView

urlpatterns = [
    path('otp/request/', OTPRequestView.as_view(), name='otp-request'),
    path('otp/verify/', OTPVerifyView.as_view(), name='otp-verify'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
]
```

- [ ] **Step 6: Run tests — verify they pass**

```bash
cd backend && pytest tests/authentication/test_otp_endpoints.py -v
```
Expected: 5 tests PASS

- [ ] **Step 7: Run full test suite**

```bash
cd backend && pytest --cov=apps --cov-report=term-missing
```
Expected: all tests pass, coverage ≥ 80%

---

### Task 9: Store API Endpoints

**Files:**
- Create: `backend/apps/tenants/serializers.py`
- Create: `backend/apps/tenants/views.py`
- Create: `backend/apps/tenants/urls.py`
- Create: `backend/tests/tenants/test_store_api.py`

**Interfaces:**
- Produces:
  - `GET /api/v1/store/` — public, returns active store info
  - `PATCH /api/v1/store/` — owner only, updates store settings

- [ ] **Step 1: Write the failing tests**

`backend/tests/tenants/test_store_api.py`:
```python
import pytest


@pytest.fixture
def api_client():
    from rest_framework.test import APIClient
    return APIClient()


@pytest.fixture
def store_with_owner(db):
    from apps.tenants.models import Store
    from apps.authentication.models import User, CustomerProfile
    from apps.authentication.tokens import TenantRefreshToken

    store = Store.objects.create(
        name='Test Store', slug='test-store',
        phone='9999999999', address='Test Address',
        delivery_pin_codes=['400001'],
    )
    owner = User.objects.create_user(phone='9000000000', is_store_owner=True)
    CustomerProfile.objects.create(user=owner, tenant=store)
    refresh = TenantRefreshToken.for_user_and_store(owner, store)
    return store, owner, str(refresh.access_token)


@pytest.mark.django_db
def test_get_store_public(api_client, store_with_owner):
    store, _, _ = store_with_owner
    response = api_client.get('/api/v1/store/')
    assert response.status_code == 200
    assert response.data['name'] == 'Test Store'
    assert 'delivery_pin_codes' in response.data


@pytest.mark.django_db
def test_patch_store_requires_owner(api_client, store_with_owner):
    _, _, token = store_with_owner
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    response = api_client.patch('/api/v1/store/', {'name': 'Updated Store'}, format='json')
    assert response.status_code == 200
    assert response.data['name'] == 'Updated Store'


@pytest.mark.django_db
def test_patch_store_rejects_non_owner(api_client, store_with_owner):
    store, _, _ = store_with_owner
    from apps.authentication.models import User, CustomerProfile
    from apps.authentication.tokens import TenantRefreshToken

    customer = User.objects.create_user(phone='8000000000')
    CustomerProfile.objects.create(user=customer, tenant=store)
    refresh = TenantRefreshToken.for_user_and_store(customer, store)
    token = str(refresh.access_token)

    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    response = api_client.patch('/api/v1/store/', {'name': 'Hacked'}, format='json')
    assert response.status_code == 403
```

- [ ] **Step 2: Run test — verify it fails**

```bash
cd backend && pytest tests/tenants/test_store_api.py -v
```
Expected: URL resolution errors

- [ ] **Step 3: Write serializers and views**

`backend/apps/tenants/serializers.py`:
```python
from rest_framework import serializers
from .models import Store


class StoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Store
        fields = [
            'id', 'name', 'slug', 'phone', 'address', 'logo',
            'delivery_pin_codes', 'delivery_radius_km', 'is_active',
        ]
        read_only_fields = ['id', 'slug', 'is_active']
```

`backend/apps/tenants/views.py`:
```python
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated

from .models import Store
from .serializers import StoreSerializer


class IsStoreOwner(IsAuthenticated):
    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        return request.auth and request.auth.get('is_store_owner', False)


class StoreView(APIView):
    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsStoreOwner()]

    def get(self, request):
        store = Store.objects.filter(is_active=True).first()
        if not store:
            return Response({'error': 'Store not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(StoreSerializer(store).data)

    def patch(self, request):
        store = Store.objects.get(id=request.auth['tenant_id'])
        serializer = StoreSerializer(store, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
```

`backend/apps/tenants/urls.py`:
```python
from django.urls import path
from .views import StoreView

urlpatterns = [
    path('store/', StoreView.as_view(), name='store'),
]
```

- [ ] **Step 4: Run tests — verify they pass**

```bash
cd backend && pytest tests/tenants/test_store_api.py -v
```
Expected: 3 tests PASS

- [ ] **Step 5: Run full test suite**

```bash
cd backend && pytest --cov=apps --cov-report=term-missing
```
Expected: all tests pass, coverage ≥ 80%

---

### Task 10: Next.js Frontend Scaffold

**Files:**
- Create: `frontend/` (via create-next-app)
- Create: `frontend/lib/api.ts`
- Create: `frontend/lib/auth.ts`
- Create: `frontend/store/auth.ts`
- Create: `frontend/components/ui/Button.tsx`
- Create: `frontend/components/ui/Input.tsx`

**Interfaces:**
- Produces:
  - `apiFetch(path, options)` — typed fetch wrapper with auto token refresh
  - `getAccessToken() / setTokens() / clearTokens()` — token storage helpers
  - `useAuthStore` — Zustand store with `{ user, isAuthenticated, setAuth, logout }`

- [ ] **Step 1: Scaffold Next.js app**

Run from the repo root:
```bash
npx create-next-app@latest frontend \
  --typescript \
  --tailwind \
  --app \
  --src-dir=no \
  --import-alias="@/*" \
  --no-git
```
When prompted, select: TypeScript ✓, ESLint ✓, Tailwind ✓, App Router ✓

- [ ] **Step 2: Install Zustand**

```bash
cd frontend && npm install zustand
```

- [ ] **Step 3: Write lib/auth.ts — token storage**

`frontend/lib/auth.ts`:
```typescript
const ACCESS_TOKEN_KEY = 'access_token';
const REFRESH_TOKEN_KEY = 'refresh_token';

export function getAccessToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(ACCESS_TOKEN_KEY);
}

export function getRefreshToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(REFRESH_TOKEN_KEY);
}

export function setTokens(access: string, refresh: string): void {
  localStorage.setItem(ACCESS_TOKEN_KEY, access);
  localStorage.setItem(REFRESH_TOKEN_KEY, refresh);
}

export function clearTokens(): void {
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
}
```

- [ ] **Step 4: Write lib/api.ts — typed fetch wrapper**

`frontend/lib/api.ts`:
```typescript
import { getAccessToken, getRefreshToken, setTokens, clearTokens } from './auth';

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

async function refreshAccessToken(): Promise<string | null> {
  const refresh = getRefreshToken();
  if (!refresh) return null;
  const res = await fetch(`${BASE_URL}/api/v1/auth/token/refresh/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh }),
  });
  if (!res.ok) {
    clearTokens();
    return null;
  }
  const data = await res.json();
  setTokens(data.access, refresh);
  return data.access;
}

export async function apiFetch<T = unknown>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${BASE_URL}${path}`;
  const token = getAccessToken();

  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...(options.headers ?? {}),
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };

  let res = await fetch(url, { ...options, headers });

  if (res.status === 401 && token) {
    const newToken = await refreshAccessToken();
    if (newToken) {
      res = await fetch(url, {
        ...options,
        headers: { ...headers, Authorization: `Bearer ${newToken}` },
      });
    }
  }

  if (!res.ok) {
    const error = await res.json().catch(() => ({ error: res.statusText }));
    throw error;
  }

  return res.json() as Promise<T>;
}
```

- [ ] **Step 5: Write store/auth.ts — Zustand auth store**

`frontend/store/auth.ts`:
```typescript
'use client';
import { create } from 'zustand';
import { setTokens, clearTokens } from '@/lib/auth';

interface AuthUser {
  phone: string;
  isStoreOwner: boolean;
}

interface AuthState {
  user: AuthUser | null;
  isAuthenticated: boolean;
  setAuth: (user: AuthUser, accessToken: string, refreshToken: string) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: false,
  setAuth: (user, accessToken, refreshToken) => {
    setTokens(accessToken, refreshToken);
    set({ user, isAuthenticated: true });
  },
  logout: () => {
    clearTokens();
    set({ user: null, isAuthenticated: false });
  },
}));
```

- [ ] **Step 6: Write UI primitives**

`frontend/components/ui/Button.tsx`:
```typescript
import { ButtonHTMLAttributes } from 'react';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost';
  loading?: boolean;
}

export function Button({ variant = 'primary', loading, children, className = '', disabled, ...props }: ButtonProps) {
  const base = 'inline-flex items-center justify-center rounded-xl font-semibold text-base transition-colors min-h-[48px] px-6 disabled:opacity-50 disabled:cursor-not-allowed';
  const variants = {
    primary: 'bg-orange-500 text-white hover:bg-orange-600 active:bg-orange-700',
    secondary: 'bg-gray-100 text-gray-900 hover:bg-gray-200',
    ghost: 'bg-transparent text-orange-500 hover:bg-orange-50',
  };
  return (
    <button
      className={`${base} ${variants[variant]} ${className}`}
      disabled={disabled || loading}
      {...props}
    >
      {loading ? <span className="animate-spin mr-2">⏳</span> : null}
      {children}
    </button>
  );
}
```

`frontend/components/ui/Input.tsx`:
```typescript
import { InputHTMLAttributes } from 'react';

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
}

export function Input({ label, error, className = '', ...props }: InputProps) {
  return (
    <div className="flex flex-col gap-1">
      {label && <label className="text-sm font-medium text-gray-700">{label}</label>}
      <input
        className={`
          w-full rounded-xl border border-gray-200 bg-gray-50 px-4 py-3
          text-base text-gray-900 placeholder-gray-400
          focus:border-orange-500 focus:outline-none focus:ring-2 focus:ring-orange-200
          disabled:opacity-50 min-h-[48px]
          ${error ? 'border-red-400 focus:border-red-400 focus:ring-red-200' : ''}
          ${className}
        `}
        {...props}
      />
      {error && <p className="text-sm text-red-500">{error}</p>}
    </div>
  );
}
```

- [ ] **Step 7: Verify TypeScript compiles**

```bash
cd frontend && npx tsc --noEmit
```
Expected: no errors

---

### Task 11: Login Page — OTP Flow UI

**Files:**
- Create: `frontend/app/(auth)/login/page.tsx`
- Modify: `frontend/app/layout.tsx`
- Create: `frontend/app/(store)/page.tsx`

**Interfaces:**
- Consumes: `apiFetch` from `@/lib/api`, `useAuthStore` from `@/store/auth`, `Button` and `Input` from `@/components/ui/`
- Produces: Working OTP login flow — enter phone → receive OTP → enter OTP → redirect to home

- [ ] **Step 1: Write login page**

`frontend/app/(auth)/login/page.tsx`:
```typescript
'use client';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { apiFetch } from '@/lib/api';
import { useAuthStore } from '@/store/auth';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';

type Step = 'phone' | 'otp';

interface OTPVerifyResponse {
  access_token: string;
  refresh_token: string;
  is_new_user: boolean;
}

export default function LoginPage() {
  const router = useRouter();
  const { setAuth } = useAuthStore();

  const [step, setStep] = useState<Step>('phone');
  const [phone, setPhone] = useState('');
  const [otp, setOtp] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  async function handlePhoneSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await apiFetch('/api/v1/auth/otp/request/', {
        method: 'POST',
        body: JSON.stringify({ phone }),
      });
      setStep('otp');
    } catch (err: unknown) {
      const msg = err && typeof err === 'object' && 'phone' in err
        ? (err as { phone: string[] }).phone[0]
        : 'Failed to send OTP. Try again.';
      setError(msg);
    } finally {
      setLoading(false);
    }
  }

  async function handleOtpSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const data = await apiFetch<OTPVerifyResponse>('/api/v1/auth/otp/verify/', {
        method: 'POST',
        body: JSON.stringify({ phone, otp }),
      });
      // Decode phone from token payload (base64 middle segment)
      const payload = JSON.parse(atob(data.access_token.split('.')[1]));
      setAuth(
        { phone: payload.phone, isStoreOwner: payload.is_store_owner },
        data.access_token,
        data.refresh_token,
      );
      router.push('/');
    } catch (err: unknown) {
      const msg = err && typeof err === 'object' && 'non_field_errors' in err
        ? (err as { non_field_errors: string[] }).non_field_errors[0]
        : 'Invalid OTP. Try again.';
      setError(msg);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
      <div className="w-full max-w-sm bg-white rounded-2xl shadow-sm border border-gray-100 p-8">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">Welcome</h1>
        <p className="text-gray-500 text-sm mb-8">
          {step === 'phone' ? 'Enter your mobile number to continue' : `Enter the OTP sent to ${phone}`}
        </p>

        {step === 'phone' ? (
          <form onSubmit={handlePhoneSubmit} className="flex flex-col gap-4">
            <Input
              label="Mobile Number"
              type="tel"
              placeholder="9876543210"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              maxLength={10}
              inputMode="numeric"
              error={error}
              required
            />
            <Button type="submit" loading={loading} className="w-full">
              Send OTP
            </Button>
          </form>
        ) : (
          <form onSubmit={handleOtpSubmit} className="flex flex-col gap-4">
            <Input
              label="OTP"
              type="text"
              placeholder="123456"
              value={otp}
              onChange={(e) => setOtp(e.target.value)}
              maxLength={6}
              inputMode="numeric"
              error={error}
              required
            />
            <Button type="submit" loading={loading} className="w-full">
              Verify OTP
            </Button>
            <Button
              type="button"
              variant="ghost"
              className="w-full"
              onClick={() => { setStep('phone'); setError(''); setOtp(''); }}
            >
              Change number
            </Button>
          </form>
        )}
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Write root layout**

`frontend/app/layout.tsx`:
```typescript
import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'Hardware & Sanitary Store',
  description: 'Quality hardware, sanitary, and construction materials delivered to your door.',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={inter.className}>{children}</body>
    </html>
  );
}
```

- [ ] **Step 3: Write home placeholder**

`frontend/app/(store)/page.tsx`:
```typescript
export default function HomePage() {
  return (
    <main className="min-h-screen flex items-center justify-center">
      <p className="text-gray-500">Store coming soon — Phase 3+</p>
    </main>
  );
}
```

- [ ] **Step 4: Verify TypeScript compiles**

```bash
cd frontend && npx tsc --noEmit
```
Expected: no errors

- [ ] **Step 5: Start the dev server and verify login page loads**

```bash
# Ensure .env is populated and Docker Compose is running, then:
cd frontend && npm run dev
```
Open http://localhost:3000/login — confirm the phone entry form renders.
Open http://localhost:8000/api/schema/swagger-ui/ — confirm API docs render.

---

### Task 12: Create Initial Store via Management Command

**Files:**
- Create: `backend/apps/tenants/management/__init__.py`
- Create: `backend/apps/tenants/management/commands/__init__.py`
- Create: `backend/apps/tenants/management/commands/create_store.py`

**Interfaces:**
- Produces: `python manage.py create_store` — creates the first store and a superuser/owner

- [ ] **Step 1: Write management command**

`backend/apps/tenants/management/commands/create_store.py`:
```python
from django.core.management.base import BaseCommand
from apps.tenants.models import Store
from apps.authentication.models import User, CustomerProfile


class Command(BaseCommand):
    help = 'Create the initial store and owner account'

    def add_arguments(self, parser):
        parser.add_argument('--name', default='My Hardware Store')
        parser.add_argument('--slug', default='my-hardware-store')
        parser.add_argument('--phone', default='9999999999')
        parser.add_argument('--address', default='Enter store address')
        parser.add_argument('--pin-codes', default='400001', help='Comma-separated')
        parser.add_argument('--owner-phone', required=True, help='Owner mobile number')

    def handle(self, *args, **options):
        pin_codes = [p.strip() for p in options['pin_codes'].split(',')]

        store, created = Store.objects.get_or_create(
            slug=options['slug'],
            defaults={
                'name': options['name'],
                'phone': options['phone'],
                'address': options['address'],
                'delivery_pin_codes': pin_codes,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Store created: {store.name}'))
        else:
            self.stdout.write(f'Store already exists: {store.name}')

        owner, created = User.objects.get_or_create(
            phone=options['owner_phone'],
            defaults={'is_store_owner': True, 'is_staff': True}
        )
        if created:
            owner.is_store_owner = True
            owner.is_staff = True
            owner.save()
            self.stdout.write(self.style.SUCCESS(f'Owner created: {owner.phone}'))

        CustomerProfile.objects.get_or_create(user=owner, tenant=store)
        self.stdout.write(self.style.SUCCESS('Done. Login with OTP using the owner phone number.'))
```

- [ ] **Step 2: Run the command**

```bash
cd backend && python manage.py create_store \
  --name "Sahil Hardware" \
  --slug "sahil-hardware" \
  --owner-phone "9876543210" \
  --pin-codes "400001,400002,400003"
```
Expected: `Store created: Sahil Hardware` + `Owner created: 9876543210`

---

## End-to-End Smoke Test

After all tasks complete, run this sequence to confirm the full auth + store flow works:

- [ ] Start Docker Compose: `docker-compose up -d`
- [ ] Run migrations: `docker-compose exec backend python manage.py migrate`
- [ ] Create store: `docker-compose exec backend python manage.py create_store --owner-phone 9876543210 --pin-codes 400001,400002`
- [ ] Request OTP (check backend logs for OTP value since mock): `curl -X POST http://localhost:8000/api/v1/auth/otp/request/ -H "Content-Type: application/json" -d '{"phone":"9876543210"}'`
- [ ] Verify OTP: `curl -X POST http://localhost:8000/api/v1/auth/otp/verify/ -H "Content-Type: application/json" -d '{"phone":"9876543210","otp":"<from-logs>"}'`
- [ ] Get store: `curl http://localhost:8000/api/v1/store/`
- [ ] Open http://localhost:3000/login and complete OTP login in browser

Expected: JWT tokens returned, store info returned, browser login succeeds and redirects to `/`
