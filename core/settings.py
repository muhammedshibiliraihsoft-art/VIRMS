"""VIRMS backend settings. Business policy remains in the canonical documents."""

import os
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlsplit

from dotenv import load_dotenv

from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent
if not os.getenv("DJANGO_ENV"):
    load_dotenv(BASE_DIR / ".env")
DJANGO_ENV = os.getenv("DJANGO_ENV")
if DJANGO_ENV not in {"local", "staging", "production"}:
    raise ImproperlyConfigured("DJANGO_ENV must be local, staging or production")
if DJANGO_ENV == "local":
    load_dotenv(BASE_DIR / ".env")


def required(name):
    value = os.getenv(name)
    if not value:
        raise ImproperlyConfigured(f"{name} must be set")
    return value


def csv_setting(name):
    return [item.strip() for item in os.getenv(name, "").split(",") if item.strip()]


SECRET_KEY = required("DJANGO_SECRET_KEY")
if SECRET_KEY.startswith("<") or (DJANGO_ENV != "local" and len(SECRET_KEY) < 50):
    raise ImproperlyConfigured("DJANGO_SECRET_KEY is not suitable for this environment")
DEBUG = DJANGO_ENV == "local" and os.getenv("DJANGO_DEBUG", "False") == "True"
ALLOWED_HOSTS = csv_setting("DJANGO_ALLOWED_HOSTS")
if not ALLOWED_HOSTS or "*" in ALLOWED_HOSTS:
    raise ImproperlyConfigured("DJANGO_ALLOWED_HOSTS must list explicit hosts")
CSRF_TRUSTED_ORIGINS = csv_setting("DJANGO_CSRF_TRUSTED_ORIGINS")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "apps.accounts",
    "apps.tenants",
    "apps.common",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "apps.accounts.middleware.ActiveAccountMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
if DJANGO_ENV != "local":
    MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")

ROOT_URLCONF = "core.urls"
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]
WSGI_APPLICATION = "core.wsgi.application"
ASGI_APPLICATION = "core.asgi.application"

database_url = os.getenv("DATABASE_URL")
if database_url:
    parsed = urlsplit(database_url)
    if parsed.scheme not in {"postgres", "postgresql"} or not parsed.hostname:
        raise ImproperlyConfigured("DATABASE_URL must be a PostgreSQL URL")
    database_config = {
        "NAME": unquote(parsed.path.lstrip("/")),
        "USER": unquote(parsed.username or ""),
        "PASSWORD": unquote(parsed.password or ""),
        "HOST": parsed.hostname,
        "PORT": parsed.port or 5432,
    }
    if not all(database_config[key] for key in ("NAME", "USER", "PASSWORD")):
        raise ImproperlyConfigured("DATABASE_URL is incomplete")
    sslmode = parse_qs(parsed.query).get("sslmode")
    if sslmode:
        database_config["OPTIONS"] = {"sslmode": sslmode[0]}
else:
    database_config = {
        "NAME": required("DB_NAME"),
        "USER": required("DB_USER"),
        "PASSWORD": required("DB_PASSWORD"),
        "HOST": required("DB_HOST"),
        "PORT": os.getenv("DB_PORT", "5432"),
    }
if database_config["PASSWORD"].startswith("<"):
    raise ImproperlyConfigured("Database password placeholder cannot be used")
DATABASES = {"default": {"ENGINE": "django.db.backends.postgresql", **database_config}}

AUTH_USER_MODEL = "accounts.User"
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "core.authentication.BrowserSessionAuthentication"
    ],
    "DEFAULT_PERMISSION_CLASSES": ["core.permissions.DenyByDefault"],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
}

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "staticfiles": {
        "BACKEND": (
            "django.contrib.staticfiles.storage.StaticFilesStorage"
            if DJANGO_ENV == "local"
            else "whitenoise.storage.CompressedManifestStaticFilesStorage"
        )
    },
}
if DJANGO_ENV == "local":
    STORAGES["default"] = {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
        "OPTIONS": {"location": BASE_DIR / ".local-media"},
    }
else:
    for name in (
        "OBJECT_STORAGE_ENDPOINT",
        "OBJECT_STORAGE_BUCKET",
        "OBJECT_STORAGE_ACCESS_KEY",
        "OBJECT_STORAGE_SECRET_KEY",
    ):
        required(name)
    STORAGES["default"] = {"BACKEND": "core.storage.PrivateObjectStorage"}

SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = DJANGO_ENV != "local"
CSRF_COOKIE_SECURE = DJANGO_ENV != "local"
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
if DJANGO_ENV != "local":
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
