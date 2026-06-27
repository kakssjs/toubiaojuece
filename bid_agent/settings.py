"""
Django settings for bid_agent project.
"""

import os
from pathlib import Path
from urllib.parse import parse_qs, urlparse


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
    database_url = os.getenv("DATABASE_URL", "").strip()
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
                "NAME": parsed.path.lstrip("/"),
                "USER": parsed.username or "",
                "PASSWORD": parsed.password or "",
                "HOST": parsed.hostname or "",
                "PORT": str(parsed.port or ""),
                "CONN_MAX_AGE": int(os.getenv("DB_CONN_MAX_AGE", "600")),
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
MEDIA_ROOT = BASE_DIR / "media"

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG


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
