from .settings import *  # noqa

# Use SQLite for tests (fast, zero-setup)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",  # or BASE_DIR / "test.sqlite3"
    }
}

SECRET_KEY = "test-secret-key"
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
