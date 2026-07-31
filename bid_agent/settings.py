"""
Django settings for bid_agent project.
"""

import os
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse


BASE_DIR = Path(__file__).resolve().parent.parent


def env_flag(name, default=False):
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def env_list(name, default=None):
    raw = os.getenv(name, "")
    items = [item.strip() for item in raw.split(",") if item.strip()]
    if items:
        return items
    return list(default or [])


def build_database_config():
    # MYSQL_DATABASE_URL takes precedence during a zero-downtime migration
    # while DATABASE_URL may still point at the previous PostgreSQL database.
    database_url = os.getenv("MYSQL_DATABASE_URL", "").strip()
    database_url = database_url or os.getenv("DATABASE_URL", "").strip()
    if not database_url:
        if os.getenv("VERCEL"):
            raise RuntimeError("DATABASE_URL is required when deploying to Vercel.")
        return {
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": BASE_DIR / "db.sqlite3",
            }
        }

    parsed = urlparse(database_url)
    scheme = parsed.scheme.lower()

    if scheme in {"postgres", "postgresql"}:
        options = {}
        query = parse_qs(parsed.query)
        if "sslmode" in query and query["sslmode"]:
            options["sslmode"] = query["sslmode"][-1]

        return {
            "default": {
                "ENGINE": "django.db.backends.postgresql",
                "NAME": unquote(parsed.path.lstrip("/")),
                "USER": unquote(parsed.username or ""),
                "PASSWORD": unquote(parsed.password or ""),
                "HOST": parsed.hostname or "",
                "PORT": str(parsed.port or ""),
                "CONN_MAX_AGE": int(os.getenv("DB_CONN_MAX_AGE", "600")),
                "OPTIONS": options,
            }
        }

    if scheme in {"mysql", "mysql+pymysql"}:
        query = parse_qs(parsed.query)
        options = {
            "charset": query.get("charset", ["utf8mb4"])[-1],
            "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
        }

        ssl_ca = query.get("ssl_ca", [""])[-1]
        ssl_mode = query.get("sslmode", query.get("ssl-mode", [""]))[-1]
        if ssl_ca:
            options["ssl"] = {"ca": ssl_ca}
        elif ssl_mode.lower() in {"require", "required", "verify_ca", "verify_identity"}:
            options["ssl"] = {}

        return {
            "default": {
                "ENGINE": "django.db.backends.mysql",
                "NAME": unquote(parsed.path.lstrip("/")),
                "USER": unquote(parsed.username or ""),
                "PASSWORD": unquote(parsed.password or ""),
                "HOST": parsed.hostname or "",
                "PORT": str(parsed.port or 3306),
                "CONN_MAX_AGE": int(os.getenv("DB_CONN_MAX_AGE", "0")),
                "OPTIONS": options,
            }
        }

    if scheme == "sqlite":
        sqlite_path = parsed.path or "/db.sqlite3"
        return {
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": Path(sqlite_path.lstrip("/")),
            }
        }

    raise RuntimeError(f"Unsupported DATABASE_URL scheme: {scheme}")


VERCEL_URL = os.getenv("VERCEL_URL", "").strip()
DEBUG = env_flag("DEBUG", default=not os.getenv("VERCEL"))
AUTO_SEED_DEMO_DATA = env_flag("AUTO_SEED_DEMO_DATA", default=bool(os.getenv("VERCEL")))
DATA_ACCESS_CONTROL_ENABLED = env_flag("DATA_ACCESS_CONTROL_ENABLED", default=bool(os.getenv("VERCEL")))
SECRET_KEY = os.getenv("SECRET_KEY", "django-insecure-local-dev-key")

allowed_hosts = {"127.0.0.1", "localhost"}
allowed_hosts.update(env_list("ALLOWED_HOSTS"))
if VERCEL_URL:
    allowed_hosts.add(VERCEL_URL)
ALLOWED_HOSTS = sorted(allowed_hosts)

csrf_trusted_origins = set(env_list("CSRF_TRUSTED_ORIGINS"))
if VERCEL_URL:
    csrf_trusted_origins.add(f"https://{VERCEL_URL}")
CSRF_TRUSTED_ORIGINS = sorted(csrf_trusted_origins)


INSTALLED_APPS = [
    "simpleui",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "tenders",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "tenders.middleware.PasswordChangeRequiredMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "bid_agent.urls"

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

WSGI_APPLICATION = "bid_agent.wsgi.application"

DATABASES = build_database_config()


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


LANGUAGE_CODE = "zh-hans"
TIME_ZONE = "Asia/Shanghai"
USE_I18N = True
USE_TZ = True


STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "/media/"
MEDIA_ROOT = Path("/tmp/media") if os.getenv("VERCEL") else BASE_DIR / "media"
if os.getenv("VERCEL"):
    FILE_UPLOAD_TEMP_DIR = Path("/tmp")

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = "Lax"
# SimpleUI loads Django admin pages in a same-origin frame. Keep external
# framing blocked while allowing the administration shell to render its pages.
X_FRAME_OPTIONS = "SAMEORIGIN"
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
SECURE_SSL_REDIRECT = not DEBUG
SECURE_HSTS_SECONDS = int(os.getenv("SECURE_HSTS_SECONDS", "3600")) if not DEBUG else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False


SIMPLEUI_HOME_TITLE = "AI 招投标 Agent 后台"
SIMPLEUI_HOME_ICON = "fa fa-gavel"
SIMPLEUI_INDEX = "/admin/"


SIMPLEUI_CONFIG = {
    "system_keep": True,
    "menu_display": ["数据表"],
    "dynamic": False,
    "menus": [
        {
            "name": "数据表",
            "icon": "fa fa-database",
            "models": [
                {
                    "name": "contract",
                    "icon": "fa fa-table",
                    "url": "/admin/tenders/contract/",
                },
            ],
        },
    ],
}


DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
