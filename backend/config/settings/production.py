from .base import *
import dj_database_url

DEBUG = False
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# ponytail: whitenoise must be right after SecurityMiddleware
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
] + [m for m in MIDDLEWARE if m != 'django.middleware.security.SecurityMiddleware']

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Railway/Render provide DATABASE_URL; fall back to individual vars from base.py
_db_url = config('DATABASE_URL', default='')
if _db_url:
    DATABASES['default'] = dj_database_url.parse(_db_url, conn_max_age=600, ssl_require=True)

# Only enable R2 storage if creds are present — skipping is fine for first deploy
_r2_key = config('R2_ACCESS_KEY_ID', default='')
if _r2_key:
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    AWS_ACCESS_KEY_ID = _r2_key
    AWS_SECRET_ACCESS_KEY = config('R2_SECRET_ACCESS_KEY')
    AWS_STORAGE_BUCKET_NAME = config('R2_BUCKET_NAME')
    AWS_S3_ENDPOINT_URL = config('R2_ENDPOINT_URL')
    AWS_S3_CUSTOM_DOMAIN = config('R2_CUSTOM_DOMAIN', default='')
    AWS_DEFAULT_ACL = 'public-read'
