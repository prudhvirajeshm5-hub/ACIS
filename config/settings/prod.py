from .base import *  # noqa

DEBUG = False

INSTALLED_APPS += ["axes"]  # noqa: F405
MIDDLEWARE = ["axes.middleware.AxesMiddleware"] + MIDDLEWARE  # noqa: F405
AUTHENTICATION_BACKENDS = ["axes.backends.AxesStandaloneBackend"] + AUTHENTICATION_BACKENDS  # noqa: F405

if not ALLOWED_HOSTS:  # noqa: F405
    raise RuntimeError("ALLOWED_HOSTS must be set explicitly in production (.env)")

# Render sets RENDER_EXTERNAL_HOSTNAME to the service's *.onrender.com
# domain automatically — trust it without requiring a manual .env edit
# for the default subdomain (a custom domain still needs ALLOWED_HOSTS).
_render_host = env("RENDER_EXTERNAL_HOSTNAME", default="")
if _render_host:
    ALLOWED_HOSTS.append(_render_host)  # noqa: F405
    CSRF_TRUSTED_ORIGINS = [f"https://{_render_host}"]

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

# In production, media should live in object storage, not local disk —
# a Render web service's local filesystem is wiped on every deploy
# unless you've attached a persistent Disk. Set AWS_STORAGE_BUCKET_NAME
# (and friends) in the environment to switch media over to S3 —
# leave it unset to keep using local disk (fine only with a mounted Disk).
if env("AWS_STORAGE_BUCKET_NAME", default=""):
    STORAGES["default"] = {"BACKEND": "storages.backends.s3boto3.S3Boto3Storage"}  # noqa: F405
    AWS_STORAGE_BUCKET_NAME = env("AWS_STORAGE_BUCKET_NAME")
    AWS_S3_REGION_NAME = env("AWS_S3_REGION_NAME", default="")
    AWS_S3_ENDPOINT_URL = env("AWS_S3_ENDPOINT_URL", default="")  # for non-AWS S3-compatible stores
    AWS_DEFAULT_ACL = None
    AWS_S3_FILE_OVERWRITE = False
    AWS_QUERYSTRING_AUTH = False

CELERY_TASK_ALWAYS_EAGER = False
