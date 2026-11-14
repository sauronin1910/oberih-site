"""Налаштування Django-проєкту для сайту КЗ «НРЦ «Оберіг»»."""
from pathlib import Path
from decouple import Csv, config

BASE_DIR = Path(__file__).resolve().parent.parent

# --- Безпека та основні параметри ---
SECRET_KEY = config("SECRET_KEY")
DEBUG = config("DEBUG", default=False, cast=bool)
ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="127.0.0.1,localhost", cast=Csv())
CSRF_TRUSTED_ORIGINS = config("CSRF_TRUSTED_ORIGINS", default="", cast=Csv())
SITE_URL = config("SITE_URL", default="").strip().rstrip("/")

# --- Застосунки ---
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Сторонні пакети
    "simple_history",
    # Власні застосунки
    "core.apps.CoreConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "core.middleware.AdminLoginRateLimitMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "core.middleware.ContentSecurityPolicyMiddleware",
    "simple_history.middleware.HistoryRequestMiddleware",
]

ROOT_URLCONF = "config.urls"
CSRF_FAILURE_VIEW = "core.views.csrf_failure"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "core.context_processors.site_context",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# --- База даних (PostgreSQL) ---
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": config("DB_NAME", default="oberih_db"),
        "USER": config("DB_USER", default="oberih_user"),
        "PASSWORD": config("DB_PASSWORD", default=""),
        "HOST": config("DB_HOST", default="127.0.0.1"),
        "PORT": config("DB_PORT", default="5432"),
        "CONN_MAX_AGE": config("DB_CONN_MAX_AGE", default=60, cast=int),
        "OPTIONS": {
            "connect_timeout": 5,
        },
    }
}

# --- Перевірка паролів (мінімальна довжина — 12 символів) ---
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 12},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# --- Локалізація та часовий пояс ---
LANGUAGE_CODE = "uk"
TIME_ZONE = "Europe/Kyiv"
USE_I18N = True
USE_TZ = True

# --- Статика та медіафайли (шляхи керуються через .env для легкого переїзду) ---
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = Path(config("STATIC_ROOT", default=str(BASE_DIR / "staticfiles")))

MEDIA_URL = "/media/"
MEDIA_ROOT = Path(config("MEDIA_ROOT", default=str(BASE_DIR / "media")))

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "core.storage.NonStrictCompressedManifestStaticFilesStorage",
    },
}

# --- Обмеження розміру завантажень і зображень ---
DATA_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024  # 5 МБ
FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024  # 5 МБ
DATA_UPLOAD_MAX_NUMBER_FIELDS = 1000
IMAGE_MAX_PIXELS = config("IMAGE_MAX_PIXELS", default=50_000_000, cast=int)

# --- Кеш у базі даних PostgreSQL (спільний для всіх процесів Gunicorn) ---
# Таблиця створюється командою: python manage.py createcachetable
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.db.DatabaseCache",
        "LOCATION": "oberih_cache_table",
    }
}

# --- Захист форми звернень та входу в адмінку від спаму і перебору паролів ---
CONTACT_RATE_LIMIT_COUNT = config("CONTACT_RATE_LIMIT_COUNT", default=3, cast=int)
CONTACT_RATE_LIMIT_PERIOD = config("CONTACT_RATE_LIMIT_PERIOD", default=600, cast=int)

ADMIN_LOGIN_RATE_LIMIT_COUNT = config("ADMIN_LOGIN_RATE_LIMIT_COUNT", default=5, cast=int)
ADMIN_LOGIN_IP_RATE_LIMIT_COUNT = config("ADMIN_LOGIN_IP_RATE_LIMIT_COUNT", default=20, cast=int)
ADMIN_LOGIN_RATE_LIMIT_PERIOD = config("ADMIN_LOGIN_RATE_LIMIT_PERIOD", default=900, cast=int)

# На PaaS (наприклад Render) вкажіть CLIENT_IP_HEADER=HTTP_TRUE_CLIENT_IP і залиште TRUST_X_FORWARDED_FOR=False.
# На VPS за власним Nginx залиште CLIENT_IP_HEADER порожнім і увімкніть TRUST_X_FORWARDED_FOR=True.
CLIENT_IP_HEADER = config("CLIENT_IP_HEADER", default="").strip()
TRUST_X_FORWARDED_FOR = config("TRUST_X_FORWARDED_FOR", default=False, cast=bool)

# --- Електронна пошта ---
EMAIL_BACKEND = config(
    "EMAIL_BACKEND",
    default="django.core.mail.backends.smtp.EmailBackend",
)
EMAIL_HOST = config("EMAIL_HOST", default="localhost")
EMAIL_PORT = config("EMAIL_PORT", default=587, cast=int)
EMAIL_USE_TLS = config("EMAIL_USE_TLS", default=True, cast=bool)
EMAIL_USE_SSL = config("EMAIL_USE_SSL", default=False, cast=bool)
EMAIL_HOST_USER = config("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD", default="")
# Таймаут з'єднання з поштовим сервером (у секундах): потрібний, щоб зависання або
# недоступність зовнішнього SMTP-сервера не блокували робочий процес Gunicorn назавжди.
EMAIL_TIMEOUT = config("EMAIL_TIMEOUT", default=10, cast=int)
DEFAULT_FROM_EMAIL = config("DEFAULT_FROM_EMAIL", default="noreply@oberih.if.ua")
# Отримувач сповіщень із форми «Поставити запитання» (якщо порожньо — береться SiteSettings.email)
CONTACT_NOTIFY_EMAIL = config("CONTACT_NOTIFY_EMAIL", default="").strip()

# --- Налаштування безпеки для продакшену (активні за замовчуванням при DEBUG=False) ---
X_FRAME_OPTIONS = "DENY"
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
CSP_ENABLED = config("CSP_ENABLED", default=True, cast=bool)

SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_AGE = config("SESSION_COOKIE_AGE", default=28800, cast=int)  # 8 годин
SESSION_SAVE_EVERY_REQUEST = True
SESSION_COOKIE_SECURE = config("SESSION_COOKIE_SECURE", default=not DEBUG, cast=bool)
CSRF_COOKIE_SECURE = config("CSRF_COOKIE_SECURE", default=not DEBUG, cast=bool)

# УВАГА: на сервері за Nginx або на PaaS увімкніть USE_X_FORWARDED_PROTO=True у .env,
# інакше при SECURE_SSL_REDIRECT=True виникне нескінченний цикл перенаправлень!
USE_X_FORWARDED_PROTO = config("USE_X_FORWARDED_PROTO", default=False, cast=bool)
SECURE_PROXY_SSL_HEADER = (
    ("HTTP_X_FORWARDED_PROTO", "https") if USE_X_FORWARDED_PROTO else None
)

SECURE_SSL_REDIRECT = config("SECURE_SSL_REDIRECT", default=not DEBUG, cast=bool)
SECURE_HSTS_SECONDS = config(
    "SECURE_HSTS_SECONDS", default=0 if DEBUG else 3600, cast=int
)
SECURE_HSTS_INCLUDE_SUBDOMAINS = config(
    "SECURE_HSTS_INCLUDE_SUBDOMAINS", default=False, cast=bool
)
SECURE_HSTS_PRELOAD = config("SECURE_HSTS_PRELOAD", default=False, cast=bool)

# --- Резервне копіювання (каталог має бути ПОЗА проєктом та ПОЗА MEDIA_ROOT) ---
BACKUP_DIR = Path(
    config("BACKUP_DIR", default=str(BASE_DIR.parent / "oberih_backups"))
)
BACKUP_KEEP_COUNT = config("BACKUP_KEEP_COUNT", default=7, cast=int)

# --- Журналювання (LOGGING) ---
LOG_FILE = config("LOG_FILE", default="").strip()
LOG_LEVEL = config("LOG_LEVEL", default="INFO").strip().upper()

_log_handlers: dict = {
    "console": {
        "class": "logging.StreamHandler",
        "formatter": "standard",
    },
}
_active_handlers = ["console"]

if LOG_FILE:
    _log_path = Path(LOG_FILE)
    if not _log_path.is_absolute():
        _log_path = BASE_DIR / _log_path
    try:
        _log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(_log_path, "a", encoding="utf-8"):
            pass
        _log_handlers["file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": str(_log_path),
            "maxBytes": 5 * 1024 * 1024,  # 5 МБ
            "backupCount": 5,
            "encoding": "utf-8",
            "formatter": "standard",
        }
        _active_handlers.append("file")
    except OSError:
        # Якщо каталог або файл журналу недоступний для запису, працюємо лише з консоллю без падіння
        pass

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "[{asctime}] {levelname} {name}: {message}",
            "style": "{",
        },
    },
    "handlers": _log_handlers,
    "root": {
        "handlers": _active_handlers,
        "level": LOG_LEVEL,
    },
    "loggers": {
        "django": {
            "handlers": _active_handlers,
            "level": LOG_LEVEL,
            "propagate": False,
        },
        "core": {
            "handlers": _active_handlers,
            "level": LOG_LEVEL,
            "propagate": False,
        },
    },
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
