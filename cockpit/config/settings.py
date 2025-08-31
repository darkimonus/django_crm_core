import os
from pathlib import Path
from datetime import timedelta

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY")

DEBUG = os.getenv("DEBUG", "False").lower() == "true"

ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", '*').split(",")

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
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
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("POSTGRES_DB"),
        "USER": os.getenv("POSTGRES_USER"),
        "PASSWORD": os.getenv("POSTGRES_PASSWORD"),
        "HOST": os.getenv("POSTGRES_HOST"),
        "PORT": os.getenv("POSTGRES_PORT"),
        "TEST": {
            "MIRROR": "default",
        },
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

INSTALLED_APPS += [
    "rest_framework",
    "django_filters",
    "crm",
]

REST_FRAMEWORK = {
    "DEFAULT_FILTER_BACKENDS": ["django_filters.rest_framework.DjangoFilterBackend"],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.LimitOffsetPagination",
    "PAGE_SIZE": 50,
}

STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "static_root/")  # noqa F405

# swagger settings
INSTALLED_APPS += [
    "drf_spectacular",
    "drf_spectacular_sidecar",  # serves Swagger/Redoc assets without external CDNs
]

# --- DRF: use Spectacular's AutoSchema ---
REST_FRAMEWORK.update({
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
})

# DRF auth classes: add JWT. (Keep SessionAuthentication for browsable API if you like.)
REST_FRAMEWORK.update({
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",  # optional (for browsable API)
    ],
    # You can keep your DEFAULT_PERMISSION_CLASSES as you prefer; views can override.
})

# SimpleJWT tuning (example defaults; adjust to your policies)
INSTALLED_APPS += ["rest_framework_simplejwt.token_blacklist"]

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,        # rotate to reduce replay risk
    "BLACKLIST_AFTER_ROTATION": True,     # requires rest_framework_simplejwt.token_blacklist in INSTALLED_APPS
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "AUTH_HEADER_TYPES": ("Bearer",),
}


# --- Spectacular configuration (adjust to your needs) ---
SPECTACULAR_SETTINGS = {
    "TITLE": "Management Cockpit CRM API",
    "DESCRIPTION": (
        "SCD2-in-table CRM core with entities, details, history, as-of, and diff endpoints. "
        "Idempotent ingestion and audit trail included."
    ),
    "VERSION": "1.0.0",
    # Declare Bearer (JWT) security for the whole API (works with SimpleJWT or any Bearer token)
    "COMPONENTS": {
        "securitySchemes": {
            "BearerAuth": {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"}
        }
    },
    "SECURITY": [{"BearerAuth": []}],
    # Optional niceties:
    "SERVE_INCLUDE_SCHEMA": False,   # do not expose the raw schema on Swagger/Redoc page
    "SCHEMA_PATH_PREFIX": r"/api",   # only document endpoints under /api
}

SPECTACULAR_SETTINGS.update({
    "COMPONENT_SPLIT_REQUEST": True,
    "SORT_OPERATIONS": True,
    "SCHEMA_PATH_PREFIX": r"/api",
    "SWAGGER_UI_SETTINGS": {
        "deepLinking": True,
        "displayRequestDuration": True,
        "persistAuthorization": True,
        "tryItOutEnabled": True,
        "defaultModelsExpandDepth": -1,
        "defaultModelExpandDepth": 2,
        "filter": True,
    },
})

