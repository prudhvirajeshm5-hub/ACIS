"""
Runs the test suite against SQLite so `pytest` works with zero
infrastructure. Production and development still use PostgreSQL exclusively
(see base.py) — this file exists purely for CI/local test speed and must
never be pointed at by DJANGO_SETTINGS_MODULE outside of testing.
"""
from .base import *  # noqa

DEBUG = False

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        # Django's SQLite test-database creation logic reads
        # DATABASES["default"]["TEST"]["NAME"] specifically — NOT the plain
        # "NAME" above — and silently defaults that to ":memory:" if it
        # isn't set, no matter what "NAME" says. Both must be set to the
        # same file path, or the ":memory:" per-connection isolation bug
        # comes right back.
        "NAME": BASE_DIR / "test_db.sqlite3",
        "TEST": {"NAME": BASE_DIR / "test_db.sqlite3"},
    }
}

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]  # fast hashing in tests only
CELERY_TASK_ALWAYS_EAGER = True
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
