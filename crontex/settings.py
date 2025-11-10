from pathlib import Path
from decouple import config, Csv
import dj_database_url
from typing import cast
from decouple import Config, RepositoryEnv

BASE_DIR = Path(__file__).resolve().parent.parent

# ---- Config via .env ----
SECRET_KEY = config("SECRET_KEY")
DEBUG = config("DEBUG", default=False, cast=bool)
ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="127.0.0.1,localhost", cast=Csv())
OPENAI_API_KEY = config("OPENAI_API_KEY", default=None)


# Application definition

INSTALLED_APPS = [
    "accounts",
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'crontex_ui',
    'people',
    'catalog.apps.CatalogConfig',
]


LOGIN_URL = "/entrar/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/entrar/"

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    "accounts.middleware.AccountMiddleware",
]

ROOT_URLCONF = 'crontex.urls'

TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [BASE_DIR / "templates"],
    "APP_DIRS": True,
    "OPTIONS": { "context_processors": [
        "django.template.context_processors.debug",
        "django.template.context_processors.request",
        "django.contrib.auth.context_processors.auth",
        "django.contrib.messages.context_processors.messages",
    ]},
}]

WSGI_APPLICATION = 'crontex.wsgi.application'


# Database
# mantém o SQLite local
# ---- Database por URL, com fallback para SQLite ----db_url: str = cast(str, config("DATABASE_URL", default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}"))
db_url: str = cast(str, config("DATABASE_URL", default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}"))
db_url: str = cast(str, config("DATABASE_URL", default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}"))

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": str(BASE_DIR / "db.sqlite3"),
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

# crontex/settings.py

LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_TZ = True

from decouple import config, Csv  # (se já existir, ignore)
ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="127.0.0.1,localhost,dev.crontex.com.br", cast=Csv())

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "crontex_ui" / "static"]  # só o design system global
STATIC_ROOT = BASE_DIR / "staticfiles"                   # saída do collectstatic
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
DEFAULT_FROM_EMAIL = "no-reply@crontex.local"  # opcional, mas útil

if DEBUG:
    # Em desenvolvimento: imprime os e-mails no terminal
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
else:
    # Em produção: substitua pelas credenciais do seu provedor de SMTP real
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    EMAIL_HOST = "smtp.seuprovedor.com"
    EMAIL_PORT = 587
    EMAIL_USE_TLS = True
    EMAIL_HOST_USER = "usuario@dominio.com"
    EMAIL_HOST_PASSWORD = "sua_senha"
    DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"basic": {"format": "%(asctime)s %(levelname)s %(name)s :: %(message)s"}},
    "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "basic"}},
    "loggers": {
        "crontex.app": {"handlers": ["console"], "level": "DEBUG"},
        "django.request": {"handlers": ["console"], "level": "INFO", "propagate": False},
    },
}