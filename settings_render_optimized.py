# Configuration optimisée pour Render
import os
from pathlib import Path
from decouple import config
import dj_database_url

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY', default='django-insecure-key')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=False, cast=bool)

ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    '.onrender.com',
    config('ALLOWED_HOSTS', default='').split(',') if config('ALLOWED_HOSTS', default='') else []
]

# Configuration CSRF pour CinetPay
CSRF_TRUSTED_ORIGINS = [
    'https://checkout.cinetpay.com',
    'https://api-checkout.cinetpay.com',
    'https://cuddly-bassoon-xa8c.onrender.com',
    'http://localhost:8000',
]

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'channels',
    'blizzgame',
    'django.contrib.sites',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'blizzgame.middleware.BanCheckMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
]

ROOT_URLCONF = 'socialgame.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'socialgame.wsgi.application'
ASGI_APPLICATION = 'socialgame.asgi.application'

# Configuration Channels avec Redis
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [config('REDIS_URL', default='redis://localhost:6379')],
        },
    },
}

# Configuration du cache Redis pour Render
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': config('REDIS_URL', default='redis://localhost:6379'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 50,
                'retry_on_timeout': True,
            }
        }
    }
}

# Configuration du rate limiting
RATELIMIT_USE_CACHE = 'default'
RATELIMIT_ENABLE = True

# Configuration de la base de données optimisée pour Render
DATABASES = {
    'default': dj_database_url.parse(
        config('DATABASE_URL', default='sqlite:///db.sqlite3'),
        conn_max_age=600,  # Pool de connexions
        conn_health_checks=True,  # Vérification de santé
    )
}

# Optimisations de base de données
DATABASES['default']['OPTIONS'] = {
    'sslmode': 'require',  # SSL requis pour Render
    'connect_timeout': 10,
    'options': '-c default_transaction_isolation=read_committed'
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
        'OPTIONS': {
            'max_similarity': 0.7,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
    {
        'NAME': 'blizzgame.validators.BlizzPasswordValidator',
    },
]

SITE_ID = 1

# Internationalization
LANGUAGE_CODE = 'fr'
TIME_ZONE = 'Europe/Paris'
USE_I18N = True
USE_L10N = True
USE_TZ = True

LANGUAGES = [
    ('fr', 'Français'),
    ('en', 'English'),
]

LOCALE_PATHS = [
    os.path.join(BASE_DIR, 'locale'),
]

# Static files configuration pour Render
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Configuration pour les fichiers statiques sur Render
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
)

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Configuration CinetPay
CINETPAY_API_KEY = config('CINETPAY_API_KEY', default='')
CINETPAY_SITE_ID = config('CINETPAY_SITE_ID', default='')
CINETPAY_SECRET_KEY = config('CINETPAY_SECRET_KEY', default='')

# Modes test CinetPay
CINETPAY_GAMING_TEST_MODE = config('CINETPAY_GAMING_TEST_MODE', default=False, cast=bool)
CINETPAY_DROPSHIPPING_TEST_MODE = config('CINETPAY_DROPSHIPPING_TEST_MODE', default=False, cast=bool)
CINETPAY_TEST_MODE = False

# URL de base pour les callbacks CinetPay
if config('ENVIRONMENT', default='production') == 'production':
    BASE_URL = 'https://cuddly-bassoon-xa8c.onrender.com'
else:
    BASE_URL = config('BASE_URL', default='http://localhost:8000')

# Configuration email Gmail SMTP
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

# Configuration de vérification email
EMAIL_VERIFICATION_REQUIRED = True
EMAIL_VERIFICATION_EXPIRE_HOURS = 24

# Payment Timeout Settings
PAYMENT_TIMEOUT_MINUTES = 30
TRANSACTION_CLEANUP_INTERVAL_MINUTES = 5

# Configuration Pusher
PUSHER_APP_ID = '2048748'
PUSHER_KEY = '6c5ea23d443700ec8467'
PUSHER_SECRET = '90b110685b3e2349c93f'
PUSHER_CLUSTER = 'eu'

# Optimisations de sécurité pour la production
if not DEBUG:
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
