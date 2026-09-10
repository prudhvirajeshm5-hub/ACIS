from .base import *  # noqa

DEBUG = False

INSTALLED_APPS += ["axes"]  # noqa: F405
MIDDLEWARE = ["axes.middleware.AxesMiddleware"] + MIDDLEWARE  # noqa: F405
AUTHENTICATION_BACKENDS = ["axes.backends.AxesStandaloneBackend"] + AUTHENTICATION_BACKENDS  # noqa: F405

if not ALLOWED_HOSTS:  # noqa: F405
    raise RuntimeError("ALLOWED_HOSTS must be set explicitly in production (.env)")

# Security headers / HTTPS enforcement -----------------------------------
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Content Security Policy (requires django-csp; add to THIRD_PARTY_APPS/MIDDLEWARE if enabled)
CSP_DEFAULT_SRC = ("'self'",)
CSP_IMG_SRC = ("'self'", "data:")
CSP_SCRIPT_SRC = ("'self'",)
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'")

# In production, media should live in object storage, not local disk.
# Uncomment once django-storages + boto3 are configured via .env:
# DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
# AWS_STORAGE_BUCKET_NAME = env("AWS_STORAGE_BUCKET_NAME")
# AWS_S3_REGION_NAME = env("AWS_S3_REGION_NAME")
# AWS_DEFAULT_ACL = None
# AWS_S3_FILE_OVERWRITE = False

CELERY_TASK_ALWAYS_EAGER = False
