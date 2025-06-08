from pathlib import Path
from decouple import config, Csv
import sys

from weatherapi.weather.constants import CACHE_TIMEOUT_CURRENT_WEATHER, API_NAME, API_VERSION

sys.path.append(str(Path(__file__).resolve().parent.parent))

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config("SECRET_KEY")
DEBUG = config("DEBUG", default=False, cast=bool)
ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="", cast=Csv())

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # DRF
    "rest_framework",
    "corsheaders",
    "drf_spectacular",
    # Apps
    "weather",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "weather.middleware.SecurityHeadersMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "weather.middleware.RequestLoggingMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "weather.middleware.ErrorHandlingMiddleware",
    "weather.middleware.APIVersionMiddleware",
]

ROOT_URLCONF = "settings.urls"

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

WSGI_APPLICATION = "settings.wsgi.application"

# --- DATABASES ---
# Для локальной разработки (по умолчанию SQLite)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}
# Для подключения к PostgreSQL раскомментируйте и настройте .env:
# DATABASES = {
#     "default": {
#         "ENGINE": "django.db.backends.postgresql",
#         "NAME": config('POSTGRES_DB'),
#         "USER": config('POSTGRES_USER'),
#         "PASSWORD": config('POSTGRES_PASSWORD'),
#         "HOST": config('POSTGRES_HOST', default='localhost'),
#         "PORT": config('POSTGRES_PORT', default='5432'),
#     }
# }

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = config("TIME_ZONE", default="UTC")
USE_I18N = True
USE_TZ = True

STATIC_URL = config("STATIC_URL", default="static/")
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [
    BASE_DIR / "static",
]
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.AllowAny",
    ],
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "100/hour",
        "user": "1000/hour",
        "burst": "10/min",
    },
    "EXCEPTION_HANDLER": "weather.exceptions.custom_exception_handler",
}

CORS_ALLOWED_ORIGINS = config("CORS_ALLOWED_ORIGINS", default="", cast=Csv())
CORS_ALLOW_ALL_ORIGINS = config("CORS_ALLOW_ALL_ORIGINS", default=True, cast=bool)

OPENWEATHER_API_KEY = config("OPENWEATHER_API_KEY", default="")
OPENWEATHER_BASE_URL = config(
    "OPENWEATHER_BASE_URL", default="https://api.openweathermap.org/data/2.5"
)

CACHES = {
    "default": {
        "BACKEND": config(
            "CACHE_BACKEND", default="django.core.cache.backends.locmem.LocMemCache"
        ),
        "LOCATION": config("CACHE_LOCATION", default="weather-api-cache"),
        "TIMEOUT": config(
            "CACHE_TIMEOUT", default=CACHE_TIMEOUT_CURRENT_WEATHER, cast=int
        ),
        "OPTIONS": {
            "MAX_ENTRIES": config("CACHE_MAX_ENTRIES", default=1000, cast=int),
        },
    }
}

SPECTACULAR_SETTINGS = {
    "TITLE": API_NAME,
    "DESCRIPTION": "REST API для получения данных о погоде с возможностью переопределения прогнозов",
    "VERSION": API_VERSION,
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
    "SCHEMA_PATH_PREFIX": "/api/",
}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": config(
                "LOG_FORMAT_VERBOSE",
                default="{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            ),
            "style": "{",
        },
        "simple": {
            "format": config("LOG_FORMAT_SIMPLE", default="{levelname} {message}"),
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "level": config("LOG_CONSOLE_LEVEL", default="INFO"),
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        "file": {
            "level": config("LOG_FILE_LEVEL", default="WARNING"),
            "class": "logging.FileHandler",
            "filename": config("LOG_FILE", default="weather_api.log"),
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": config("LOG_ROOT_LEVEL", default="INFO"),
    },
    "loggers": {
        "weather": {
            "handlers": ["console", "file"],
            "level": config("LOG_WEATHER_LEVEL", default="INFO"),
            "propagate": False,
        },
        "django.request": {
            "handlers": ["console", "file"],
            "level": config("LOG_DJANGO_REQUEST_LEVEL", default="WARNING"),
            "propagate": False,
        },
    },
}

if not DEBUG:
    CONN_MAX_AGE = config("CONN_MAX_AGE", default=60, cast=int)
    STATICFILES_STORAGE = config(
        "STATICFILES_STORAGE",
        default="django.contrib.staticfiles.storage.StaticFilesStorage",
    )
    SESSION_ENGINE = config(
        "SESSION_ENGINE", default="django.contrib.sessions.backends.cached_db"
    )
    SESSION_CACHE_ALIAS = config("SESSION_CACHE_ALIAS", default="default")
    TEMPLATES[0]["OPTIONS"]["loaders"] = [
        (
            "django.template.loaders.cached.Loader",
            [
                "django.template.loaders.filesystem.Loader",
                "django.template.loaders.app_directories.Loader",
            ],
        ),
    ]

DATABASES["default"]["OPTIONS"] = (
    {
        "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
        "charset": "utf8mb4",
    }
    if "mysql" in DATABASES["default"]["ENGINE"]
    else {}
)

if "redis" in CACHES["default"]["BACKEND"]:
    CACHES["default"]["OPTIONS"] = {
        "CONNECTION_POOL_KWARGS": {"max_connections": 50},
        "COMPRESSOR": "django_redis.compressors.zlib.ZlibCompressor",
        "IGNORE_EXCEPTIONS": True,
    }
