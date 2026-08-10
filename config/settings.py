"""Django settings for the Event Registration System.

All environment-specific values are read from environment variables,
optionally loaded from a `.env` file in the project root.
"""

from datetime import timedelta
from pathlib import Path
import os

from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")


def env(name, default=None, *, required=False):
    value = os.environ.get(name, default)
    if required and not value:
        raise ImproperlyConfigured(f"The {name} environment variable is required.")
    return value


def env_bool(name, default=False):
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


def env_int(name, default):
    value = os.environ.get(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError as exc:
        raise ImproperlyConfigured(f"The {name} environment variable must be an integer.") from exc


def env_list(name, default=""):
    value = os.environ.get(name, default)
    return [item.strip() for item in value.split(",") if item.strip()]


SECRET_KEY = env("SECRET_KEY", required=True)

DEBUG = env_bool("DEBUG", default=False)

ALLOWED_HOSTS = env_list("ALLOWED_HOSTS")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "rest_framework",
    "rest_framework_simplejwt.token_blacklist",
    "drf_spectacular",
    "common",
    "users",
    "authentication",
    "events",
    "registrations",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("DB_NAME", "event_registration"),
        "USER": env("DB_USER", "event_registration"),
        "PASSWORD": env("DB_PASSWORD", ""),
        "HOST": env("DB_HOST", "localhost"),
        "PORT": env("DB_PORT", "5432"),
    }
}

AUTH_USER_MODEL = "users.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_PAGINATION_CLASS": "common.pagination.DefaultPageNumberPagination",
    "PAGE_SIZE": 20,
    "EXCEPTION_HANDLER": "common.exceptions.api_exception_handler",
    "DEFAULT_THROTTLE_CLASSES": (
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ),
    "DEFAULT_THROTTLE_RATES": {
        "anon": env("THROTTLE_ANON", "100/minute"),
        "user": env("THROTTLE_USER", "1000/minute"),
        "auth": env("THROTTLE_AUTH", "10/minute"),
    },
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Event Registration System API",
    "DESCRIPTION": (
        "REST API for organizers to create and manage events and for "
        "authenticated users to register for them.\n\n"
        "All errors use one envelope: "
        '`{"error": {"code": "<machine-readable>", "message": "<human-readable>", '
        '"details": <extra or null>}}`. Status mapping: 400 validation, '
        "401 unauthenticated, 403 forbidden, 404 missing or not visible, "
        "409 business-rule/state conflict, 429 throttled."
    ),
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "ENUM_NAME_OVERRIDES": {
        "EventStatusEnum": "events.models.EventStatus",
        "RegistrationStatusEnum": "registrations.models.RegistrationStatus",
    },
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=env_int("JWT_ACCESS_TOKEN_LIFETIME_MINUTES", 15)),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=env_int("JWT_REFRESH_TOKEN_LIFETIME_DAYS", 7)),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
}

CORS_ALLOWED_ORIGINS = env_list("CORS_ALLOWED_ORIGINS")

if not DEBUG:
    SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", default=True)
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = env_int("SECURE_HSTS_SECONDS", 31536000)
    SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool("SECURE_HSTS_INCLUDE_SUBDOMAINS", default=True)
    SECURE_HSTS_PRELOAD = env_bool("SECURE_HSTS_PRELOAD", default=True)
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True

STATIC_URL = "static/"

STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "{asctime} {levelname} {name} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "standard",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": env("LOG_LEVEL", "INFO"),
    },
}
