from pathlib import Path
from datetime import timedelta
import os
from dotenv import load_dotenv
import pathlib
from django.core.exceptions import ImproperlyConfigured

try:
    import pymysql
    pymysql.install_as_MySQLdb()
except Exception:
    pass

_PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
for _env_file in (
    os.environ.get("ENV_FILE"),
    str(_PROJECT_ROOT / ".env"),
    "/var/www/www-root/data/www/anisphere.org/.env",
):
    if _env_file and os.path.exists(_env_file):
        load_dotenv(_env_file)
        break
else:
    load_dotenv()

from config.feature_flags import env_flag

IN_DOCKER = os.path.exists("/.dockerenv") or os.environ.get("RUNNING_IN_DOCKER") == "1"
if not IN_DOCKER:
    if os.environ.get("DB_HOST") == "mysql":
        os.environ["DB_HOST"] = "127.0.0.1"
        os.environ["DB_PORT"] = os.environ.get("DB_LOCAL_PORT", "3307")
    if os.environ.get("REDIS_HOST") == "redis":
        os.environ["REDIS_HOST"] = "127.0.0.1"

BASE_DIR = Path(__file__).resolve().parent.parent


def parse_env_list(name, default=None):
    val = os.environ.get(name)
    if val is None:
        val = default
    if not val:
        return []
    return [p.strip() for p in val.split(",") if p.strip()]


def _with_local(values, extras):
    return list(dict.fromkeys(list(values) + list(extras)))


_LOCAL_HOSTS = ["localhost", "127.0.0.1", "[::1]", "backend"]
_LOCAL_ORIGINS = [
    f"http://{host}{port}"
    for host in ("localhost", "127.0.0.1")
    for port in ("", ":5173", ":4173", ":3000", ":8000")
]



SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY") or os.environ.get("SECRET_KEY")

DEBUG = os.environ.get("DEBUG", "False").lower() in ("1", "true", "yes")

SUPPORT_ADMIN_USER_ID = os.environ.get("SUPPORT_ADMIN_USER_ID")

ALLOWED_HOSTS = _with_local(parse_env_list("ALLOWED_HOSTS"), _LOCAL_HOSTS)


INSTALLED_APPS = [
    "apps.seo",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django_celery_results",
    "django.contrib.staticfiles",
    "corsheaders",
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "channels",
    "core",
    "apps.users",
    "apps.anime",
    "apps.dubs",
    "apps.playlists",
    "apps.social",
    "apps.reactor",
    "apps.notifications",
    "apps.native_apps",
    "apps.studios",
    "apps.ideas",
    "imagekit",
]

MIDDLEWARE = [
    "apps.seo.middleware.SeoPrivacyHeadersMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "config.middleware.ReleaseFeatureGateMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "config.middleware.CSRFExemptMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "config.middleware.OnlineStatusMiddleware",
    "config.middleware.SecurityResponseHeadersMiddleware",
]

if DEBUG:
    MIDDLEWARE.append("config.middleware.AuthDebugMiddleware")

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        'DIRS': [
            BASE_DIR / 'templates',
        ],        
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

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_HEADER_NAME": "HTTP_AUTHORIZATION",
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
    "TOKEN_TYPE_CLAIM": "token_type",
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "VERIFYING_KEY": None,
    "AUDIENCE": None,
    "ISSUER": None,
    "JWK_URL": None,
    "LEEWAY": 0,
}


_DB_ENGINE = os.environ.get("DB_ENGINE", "django.db.backends.mysql")
if _DB_ENGINE == "django.db.backends.sqlite3":
    DATABASES = {"default": {"ENGINE": _DB_ENGINE, "NAME": os.environ.get("DB_NAME", str(BASE_DIR / "test.sqlite3"))}}
else:
    DATABASES = {
        "default": {
            "ENGINE": _DB_ENGINE,
            "NAME": os.environ.get("DB_NAME", "project_db"),
            "USER": os.environ.get("DB_USER", "project"),
            "PASSWORD": os.environ.get("DB_PASSWORD"),
            "HOST": os.environ.get("DB_HOST", "localhost"),
            "PORT": os.environ.get("DB_PORT", "3306"),
            "CONN_MAX_AGE": 600,
            "OPTIONS": {
                "charset": "utf8mb4",
                "use_unicode": True,
                "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
            },
        }
    }

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

CORS_ALLOW_ALL_ORIGINS = os.environ.get("CORS_ALLOW_ALL_ORIGINS", "False").lower() in ("1", "true", "yes")
CORS_ALLOW_CREDENTIALS = True

CORS_ALLOWED_ORIGINS = _with_local(
    parse_env_list("CORS_ALLOWED_ORIGINS"),
    parse_env_list("CSRF_TRUSTED_ORIGINS") + _LOCAL_ORIGINS,
)
CORS_ALLOWED_ORIGIN_REGEXES = parse_env_list("CORS_ALLOWED_ORIGIN_REGEXES")

CORS_ALLOW_HEADERS = [
    "accept",
    "accept-encoding",
    "authorization",
    "cache-control",
    "content-type",
    "dnt",
    "if-modified-since",
    "keep-alive",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
]

CORS_ALLOW_METHODS = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
CORS_PREFLIGHT_MAX_AGE = 86400

CORS_URLS_REGEX = r"^/api/.*$"

AUTH_USER_MODEL = "users.User"

LANGUAGE_CODE = "ru-ru"
TIME_ZONE = "Europe/Moscow"
USE_I18N = True
USE_TZ = True


DATA_DIR = pathlib.Path(os.environ.get("DATA_DIR") or (BASE_DIR / "data")).resolve()

STATIC_URL = "/static/"
STATIC_ROOT = DATA_DIR / "staticfiles"
STATICFILES_DIRS = [
    path for path in (BASE_DIR / "frontend" / "dist",)
    if path.is_dir()
]

MEDIA_URL = "/data/media/"
MEDIA_ROOT = DATA_DIR / "media"
CHAT_PRIVATE_MEDIA_ROOT = DATA_DIR / "private_chat_media"
CHAT_MEDIA_TICKET_MAX_AGE = 1800
CHAT_SETTINGS_IMPORT_MAX_BYTES = 32 * 1024 * 1024
DATA_UPLOAD_MAX_MEMORY_SIZE = CHAT_SETTINGS_IMPORT_MAX_BYTES

KODIK_DUMP_DIR = os.environ.get("KODIK_DUMP_DIR") or str(DATA_DIR / "kodik_dumps")

ANIMEGO_RESERVE_STREAMS_ENABLED = (
    os.environ.get("ANIMEGO_RESERVE_STREAMS_ENABLED", "False").lower() in ("1", "true", "yes")
)

for _sub in ("media", "staticfiles", "celerybeat", "kodik_dumps"):
    try:
        (DATA_DIR / _sub).mkdir(parents=True, exist_ok=True)
    except OSError:
        pass

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
        "rest_framework.parsers.FormParser",
        "rest_framework.parsers.MultiPartParser",
    ],
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "config.authentication.SoftJWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_FILTER_BACKENDS": [
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "1000/hour",
        "user": "5000/hour",
        "login": "5/hour",
        "email": "3/hour",
        "register": "3/hour",
        "import": "10/hour",
        "search": "60/minute",
    },
}

REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
REDIS_SOCKET_TIMEOUT = float(os.environ.get("REDIS_SOCKET_TIMEOUT", "2"))
REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))
REDIS_DB = int(os.environ.get("REDIS_DB", 0))
REDIS_PASSWORD = os.environ.get("REDIS_PASSWORD", "")

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': f'redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB + 1}',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'PASSWORD': REDIS_PASSWORD if REDIS_PASSWORD else None,
            'SOCKET_CONNECT_TIMEOUT': 5,
            'SOCKET_TIMEOUT': 5,
            'RETRY_ON_TIMEOUT': True,
        },
        'KEY_PREFIX': 'anilux',
        'TIMEOUT': 3600,
    }
}

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [{
                "address": f"redis://{REDIS_HOST}:{REDIS_PORT}/0",
                "socket_timeout": 30,
                "socket_connect_timeout": 30,
            }],
            "capacity": 5000,
            "expiry": 300,
        },
    },
}

PROJECT_BRAND_NAME = os.environ.get("PROJECT_BRAND_NAME", "AniLux").strip()
PROJECT_PUBLIC_DOMAIN = os.environ.get("PROJECT_PUBLIC_DOMAIN", "example.invalid").strip()
FRONTEND_PUBLIC_URL = os.environ.get("FRONTEND_PUBLIC_URL", "http://localhost:5173").rstrip("/")
TRANSACTIONAL_FROM_EMAIL = os.environ.get(
    "TRANSACTIONAL_FROM_EMAIL", "no-reply@example.invalid"
).strip()
TRANSACTIONAL_REPLY_TO_EMAIL = os.environ.get("TRANSACTIONAL_REPLY_TO_EMAIL", "").strip()
EMAIL_PROVIDER = os.environ.get("EMAIL_PROVIDER", "mailpit").strip().lower()
EMAIL_TIMEOUT = int(os.environ.get("EMAIL_TIMEOUT_SECONDS", "10"))
EMAIL_FAIL_SILENTLY = env_flag("EMAIL_FAIL_SILENTLY", default=False)
EMAIL_CONFIRM_TOKEN_TTL_SECONDS = int(os.environ.get("EMAIL_CONFIRM_TOKEN_TTL_SECONDS", "86400"))
PASSWORD_RESET_TOKEN_TTL_SECONDS = int(os.environ.get("PASSWORD_RESET_TOKEN_TTL_SECONDS", "3600"))
BREVO_WEBHOOK_BEARER_TOKEN = os.environ.get("BREVO_WEBHOOK_BEARER_TOKEN", "")

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
if EMAIL_PROVIDER == "mailpit":
    EMAIL_HOST = os.environ.get("MAILPIT_SMTP_HOST", "mailpit" if IN_DOCKER else "127.0.0.1")
    EMAIL_PORT = int(os.environ.get("MAILPIT_SMTP_PORT", "1025"))
    EMAIL_USE_TLS = False
    EMAIL_USE_SSL = False
    EMAIL_HOST_USER = ""
    EMAIL_HOST_PASSWORD = ""
elif EMAIL_PROVIDER == "brevo":
    EMAIL_HOST = os.environ.get("BREVO_SMTP_HOST", "smtp-relay.brevo.com")
    EMAIL_PORT = int(os.environ.get("BREVO_SMTP_PORT", "587"))
    EMAIL_USE_TLS = True
    EMAIL_USE_SSL = False
    EMAIL_HOST_USER = os.environ.get("BREVO_SMTP_LOGIN", "")
    EMAIL_HOST_PASSWORD = os.environ.get("BREVO_SMTP_KEY", "")
else:
    raise ImproperlyConfigured("EMAIL_PROVIDER must be 'mailpit' or 'brevo'")

DEFAULT_FROM_EMAIL = TRANSACTIONAL_FROM_EMAIL
SERVER_EMAIL = TRANSACTIONAL_FROM_EMAIL

ENVIRONMENT = os.environ.get("ENVIRONMENT", "development").strip().lower()
if ENVIRONMENT == "production":
    invalid_email_config = (
        EMAIL_PROVIDER != "brevo"
        or not EMAIL_HOST_USER
        or not EMAIL_HOST_PASSWORD
        or PROJECT_PUBLIC_DOMAIN.endswith(".invalid")
        or "localhost" in FRONTEND_PUBLIC_URL
        or not FRONTEND_PUBLIC_URL.startswith("https://")
        or EMAIL_FAIL_SILENTLY
    )
    if invalid_email_config:
        raise ImproperlyConfigured("Production transactional email configuration is unsafe or incomplete")

SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
X_FRAME_OPTIONS = "DENY"
if ENVIRONMENT == "production":
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET")  

PAL24_API_TOKEN = os.environ.get("PAL24_API_TOKEN", "")
PAL24_SHOP_ID = os.environ.get("PAL24_SHOP_ID", "")

CRYPTOCLOUD_API_KEY = os.environ.get("CRYPTOCLOUD_API_KEY", "")
CRYPTOCLOUD_SHOP_ID = os.environ.get("CRYPTOCLOUD_SHOP_ID", "")
CRYPTOCLOUD_SECRET_KEY = os.environ.get("CRYPTOCLOUD_SECRET_KEY", "")


SUBSCRIPTION_PRICE = 399  

SITE_URL = os.environ.get("SITE_URL") or "http://localhost:5173"
NATIVE_APP_SITE_URL = os.environ.get("NATIVE_APP_SITE_URL", "")
NATIVE_APP_VERSION = os.environ.get("NATIVE_APP_VERSION", "0.1.0")
VITE_API_URL = os.environ.get("VITE_API_URL")

PHONENUMBER_DEFAULT_REGION = "RU"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"

CELERY_BROKER_URL = f'redis://{REDIS_HOST}:{REDIS_PORT}/0'
CELERY_RESULT_BACKEND = f'redis://{REDIS_HOST}:{REDIS_PORT}/0'  
CELERY_CACHE_BACKEND = f'redis://{REDIS_HOST}:{REDIS_PORT}/1'
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 300
CELERY_RESULT_EXTENDED = True
CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'

CELERY_RESULT_EXTENDED = True
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_SEND_SENT_EVENT = True
if not DEBUG:
    SECURE_SSL_REDIRECT = False
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = "DENY"
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SESSION_COOKIE_AGE = 86400
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "None"
    CSRF_COOKIE_HTTPONLY = False
    CSRF_COOKIE_SAMESITE = "None"
    CSRF_TRUSTED_ORIGINS = _with_local(parse_env_list("CSRF_TRUSTED_ORIGINS"), _LOCAL_ORIGINS)
else:
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False
    SECURE_SSL_REDIRECT = False
    SESSION_COOKIE_SAMESITE = "Lax"
    CSRF_COOKIE_SAMESITE = "Lax"
    CSRF_TRUSTED_ORIGINS = _with_local(parse_env_list("CSRF_TRUSTED_ORIGINS"), _LOCAL_ORIGINS)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "loggers": {
        "django": {"handlers": ["console"], "level": "INFO"},
        "config.middleware": {"handlers": ["console"], "level": "DEBUG"},
        "apps.anime": {"handlers": ["console"], "level": "INFO"},
    },
}

REPORTS_MODERATOR_USERNAME = os.environ.get("REPORTS_MODERATOR_USERNAME", "moderator")
REPORTS_MODERATOR_EMAIL = os.environ.get("REPORTS_MODERATOR_EMAIL", "")

POSTER_ENHANCEMENT_ENABLED = os.environ.get("POSTER_ENHANCEMENT_ENABLED", "False").lower() in ("1", "true", "yes")
REALESRGAN_BINARY_PATH = os.environ.get("REALESRGAN_BINARY_PATH", "") or str(BASE_DIR / "bin" / ("realesrgan-ncnn-vulkan.exe" if os.name == "nt" else "realesrgan-ncnn-vulkan"))
REALESRGAN_MODEL_PATH = os.environ.get("REALESRGAN_MODEL_PATH", "") or str(BASE_DIR / "bin" / "models")
REALESRGAN_MODEL_NAME = os.environ.get("REALESRGAN_MODEL_NAME", "realesrgan-x4plus-anime")
REALESRGAN_SCALE = int(os.environ.get("REALESRGAN_SCALE", "4"))
REALESRGAN_TILE_SIZE = int(os.environ.get("REALESRGAN_TILE_SIZE", "200"))
REALESRGAN_TTA = os.environ.get("REALESRGAN_TTA", "False").lower() in ("1", "true", "yes")

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

WHITENOISE_MAX_AGE = 31536000
WHITENOISE_IMMUTABLE_FILE = True
CACHE_MIDDLEWARE_ALIAS = 'default'
CACHE_MIDDLEWARE_SECONDS = 300
CACHE_MIDDLEWARE_KEY_PREFIX = 'api'

WEB_PUSH_PUBLIC_KEY = os.environ.get('WEB_PUSH_PUBLIC_KEY', '')

SEO_SITE_NAME = os.environ.get('SEO_SITE_NAME', 'AniLux')
SEO_PUBLIC_ORIGIN = os.environ.get('SEO_PUBLIC_ORIGIN', '').rstrip('/')
SEO_INDEXING_ENABLED = os.environ.get('SEO_INDEXING_ENABLED', 'false').lower() == 'true'
SEO_FRONTEND_INDEX = os.environ.get('SEO_FRONTEND_INDEX', str(BASE_DIR / 'frontend_dist' / 'index.html'))
WEB_PUSH_PRIVATE_KEY = os.environ.get('WEB_PUSH_PRIVATE_KEY', '')
WEB_PUSH_SUBJECT = os.environ.get('WEB_PUSH_SUBJECT', '')
WEB_PUSH_ALLOWED_HOSTS = tuple(os.environ.get('WEB_PUSH_ALLOWED_HOSTS',
    'fcm.googleapis.com,updates.push.services.mozilla.com,web.push.apple.com,.notify.windows.com').split(','))
