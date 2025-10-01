"""
Development settings for Shortify Link.

Uses SQLite database and DEBUG=True.
"""

from .settings import *

DEBUG = True

ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

# SQLite database for development
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# Simplified logging for development
LOGGING["root"]["level"] = "DEBUG"
