import os
from pathlib import Path
from decouple import AutoConfig, Csv, Choices
from django.urls import reverse_lazy

import cloudinary
import cloudinary.uploader
import cloudinary.api

config = AutoConfig(search_path='envs')

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config('SECRET_KEY')

DEBUG = config('DEBUG', cast=bool)

ALLOWED_HOSTS = config('ALLOWED_HOSTS', cast=Csv())

# Production
CSRF_TRUSTED_ORIGINS = [f'https://{x}' for x in ALLOWED_HOSTS]

# Allauth configs
SITE_ID = config('SITE_ID', cast=int)
ACCOUNT_LOGIN_METHODS = ['email',]
ACCOUNT_SIGNUP_FIELDS = ['email*',]
ACCOUNT_USER_MODEL_USERNAME_FIELD = None
SOCIALACCOUNT_LOGIN_ON_GET = True
SOCIALACCOUNT_ADAPTER = 'house_manager.accounts.adapters.CustomSocialAccountAdapter'
SECURE_PROXY_SSL_HEADER_STR = config('SECURE_PROXY_SSL_HEADER')
SECURE_PROXY_SSL_HEADER = tuple(SECURE_PROXY_SSL_HEADER_STR.split(','))

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'django.contrib.sitemaps',

    'cloudinary_storage',
    'cloudinary',

    "house_manager.accounts.apps.AccountsConfig",
    "house_manager.common.apps.CommonConfig",
    "house_manager.houses.apps.HousesConfig",
    "house_manager.clients.apps.ClientsConfig",
    "house_manager.house_bills.apps.HouseBillsConfig",
    "house_manager.client_bills.apps.ClientBillsConfig",

    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",

    "import_export",
    "django_recaptcha",
    "axes",
    "debug_toolbar",
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    "allauth.account.middleware.AccountMiddleware",
    "axes.middleware.AxesMiddleware",
    "debug_toolbar.middleware.DebugToolbarMiddleware",
]

ROOT_URLCONF = 'house_manager.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates']
        ,
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.i18n',
                'house_manager.common.seo.context_processors.global_settings',
            ],
        },
    },
]

WSGI_APPLICATION = 'house_manager.wsgi.application'

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": config('DB_NAME'),
        "USER": config('DB_USER'),
        "PASSWORD": config('DB_PASSWORD'),
        "HOST": config('DB_HOST'),
        "PORT": config('DB_PORT'),
    }
}

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

# Development
if DEBUG:
    CSRF_TRUSTED_ORIGINS = ['http://127.0.0.1:81']
    AUTH_PASSWORD_VALIDATORS = ()

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True
USE_L10N = True
USE_TZ = True

LANGUAGES = [
    ('en-us', 'English'),
    ('bg', 'Bulgarian'),
]

LOCALE_PATHS = [os.path.join(BASE_DIR, 'locale'), ]

STATIC_URL = '/static/'

STATICFILES_DIRS = (
    BASE_DIR / 'staticfiles',
)

STATIC_ROOT = config('STATIC_ROOT')

MEDIA_URL = '/mediafiles/'
MEDIA_ROOT = config('MEDIA_ROOT')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = "accounts.HouseManagerUser"

LOGIN_REDIRECT_URL = reverse_lazy("index")

LOGIN_URL = reverse_lazy("account_login")

LOGOUT_REDIRECT_URL = reverse_lazy("index")

cloudinary.config(
    cloud_name=config("cloud_name"),
    api_key=config("api_key"),
    api_secret=config("api_secret")
)

CLOUDINARY_STORAGE = {
    "CLOUD_NAME": config("cloud_name"),
    "API_KEY": config("api_key"),
    "API_SECRET": config("api_secret")
}

EMAIL_BACKEND = config("EMAIL_BACKEND")
EMAIL_HOST = config("EMAIL_HOST")
EMAIL_PORT = config("EMAIL_PORT")
EMAIL_USE_TLS = config("EMAIL_USE_TLS")
EMAIL_HOST_USER = config("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD")
DEFAULT_FROM_EMAIL = config("DEFAULT_FROM_EMAIL")

SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': [
            'profile',
            'email',
        ],
        'AUTH_PARAMS': {
            'access_type': 'online',
        }
    }
}

AUTHENTICATION_BACKENDS = (
    "axes.backends.AxesBackend",
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
)

SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = config('SOCIAL_AUTH_GOOGLE_OAUTH2_KEY')
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = config('SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET')

RECAPTCHA_PUBLIC_KEY = config('RECAPTCHA_PUBLIC_KEY')
RECAPTCHA_PRIVATE_KEY = config('RECAPTCHA_PRIVATE_KEY')
RECAPTCHA_USE_SSL = True

AXES_FAILURE_LIMIT = 3  # Lock after 3 attempts
AXES_COOLOFF_TIME = 0.5  # 30 minutes lockout
AXES_LOCKOUT_PARAMETERS = [["username"]]
AXES_DISABLE_ACCESS_LOG = False
AXES_RESET_ON_SUCCESS = False
AXES_USERNAME_FORM_FIELD = "username"
AXES_ENABLE_ACCESS_FAILURE_LOG = True
AXES_LOCKOUT_TEMPLATE = 'common/429_template.html'

# Django Debug Toolbar settings
INTERNAL_IPS = ['127.0.0.1']

DEBUG_TOOLBAR_CONFIG = {
    'SHOW_TOOLBAR_CALLBACK': lambda request: DEBUG,  # Only show if DEBUG=True
    'RENDER_PANELS': True,
    'PRETTIFY_SQL': True,
    'SQL_WARNING_THRESHOLD': 100,
    'RECORD_SQL': True,
    'EXTRA_SIGNALS': [],
    'ENABLE_STACKTRACES': True,
}

DEBUG_TOOLBAR_PANELS = [
    'debug_toolbar.panels.history.HistoryPanel',
    'debug_toolbar.panels.versions.VersionsPanel',
    'debug_toolbar.panels.timer.TimerPanel',
    'debug_toolbar.panels.settings.SettingsPanel',
    'debug_toolbar.panels.headers.HeadersPanel',
    'debug_toolbar.panels.request.RequestPanel',
    'debug_toolbar.panels.sql.SQLPanel',
    'debug_toolbar.panels.staticfiles.StaticFilesPanel',
    'debug_toolbar.panels.templates.TemplatesPanel',
    'debug_toolbar.panels.alerts.AlertsPanel',
    'debug_toolbar.panels.cache.CachePanel',
    'debug_toolbar.panels.signals.SignalsPanel',
    'debug_toolbar.panels.redirects.RedirectsPanel',
    'debug_toolbar.panels.profiling.ProfilingPanel',
]

GOOGLE_ANALYTICS_ID=config('GOOGLE_ANALYTICS_ID')