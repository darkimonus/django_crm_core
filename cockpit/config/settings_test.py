import os
from .settings import *  # noqa

# Use Postgres in tests to support exclusion constraints and ranges
# Ensure we DO NOT mirror the default DB; run full migrations for tests.
test_db_name = os.getenv("POSTGRES_TEST_DB", f"test_{os.getenv('POSTGRES_DB', 'postgres')}")
DATABASES["default"].pop("TEST", None)
DATABASES["default"]["TEST"] = {"NAME": test_db_name}

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "test-secret-key")
DEBUG = False

# Faster password hashing for tests
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

# Keep emails in memory
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# Ensure timezone-aware datetimes
USE_TZ = True
TIME_ZONE = "UTC"

# If REST_FRAMEWORK is env-dependent in your base settings, make sure it’s present:
REST_FRAMEWORK = globals().get("REST_FRAMEWORK", {})
