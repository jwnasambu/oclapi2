"""
Django settings for core project.

Generated by 'django-admin startproject' using Django 3.0.7.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.0/ref/settings/
"""

import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
from corsheaders.defaults import default_headers
from kombu import Queue, Exchange

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

API_BASE_URL = os.environ.get('API_BASE_URL', 'http://localhost:8000')

API_INTERNAL_BASE_URL = os.environ.get('API_INTERNAL_BASE_URL', 'http://api:8000')

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '=q1%fd62$x!35xzzlc3lix3g!s&!2%-1d@5a=rm!n4lu74&6)p'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']

CORS_ALLOW_HEADERS = default_headers + (
    'INCLUDEFACETS',
)

CORS_EXPOSE_HEADERS = (
    'num_found',
    'num_returned',
    'pages',
    'page_number',
    'next',
    'previous',
    'offset',
    'Content-Length',
    'Content-Range'
)

CORS_ORIGIN_ALLOW_ALL = True
# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework.authtoken',
    'drf_yasg',
    'django_elasticsearch_dsl',
    'corsheaders',
    'core.common.apps.CommonConfig',
    'core.users',
    'core.orgs',
    'core.sources.apps.SourceConfig',
    'core.collections',
    'core.concepts',
    'core.mappings',
    'core.importers',
]

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.TokenAuthentication',
    ),
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
        'core.common.renderers.ZippedJSONRenderer',
    ),
    'COERCE_DECIMAL_TO_STRING': False,
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'DEFAULT_VERSIONING_CLASS': 'rest_framework.versioning.AcceptHeaderVersioning',
    'DEFAULT_SCHEMA_CLASS': 'rest_framework.schemas.coreapi.AutoSchema',
    'DEFAULT_CONTENT_NEGOTIATION_CLASS': 'core.common.negotiation.OptionallyCompressContentNegotiation',
}

SWAGGER_SETTINGS = {
    'PERSIST_AUTH': True,
    'SECURITY_DEFINITIONS': {
        'Basic': {
            'type': 'basic'
        },
        'Token': {
            'type': 'apiKey',
            'name': 'Authorization',
            'in': 'header'
        }
    },
    'DOC_EXPANSION': 'none',
}

REDOC_SETTINGS = {
    'LAZY_RENDERING': True,
    'NATIVE_SCROLLBARS': True,
}

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'core.middlewares.middlewares.FixMalformedLimitParamMiddleware',
    'core.middlewares.middlewares.RequestLogMiddleware',
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'core.wsgi.application'

# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB', 'postgres'),
        'USER': 'postgres',
        'PASSWORD': os.environ.get('DB_PASSWORD', 'Postgres123'),
        'HOST': os.environ.get('DB_HOST', 'db'),
        'PORT': os.environ.get('DB_PORT', 5432),
    }
}

ELASTICSEARCH_DSL = {
    'default': {
        'hosts': [os.environ.get('ES_HOST', 'es') + ':' + os.environ.get('ES_PORT', '9200')]
    },
}

# LOGGING = {
#     'version': 1,
#     'disable_existing_loggers': False,
#     'formatters': {
#         'verbose': {
#             'format': '%(levelname)s %(asctime)s %(message)s'
#         },
#         'simple': {
#             'format': '%(levelname)s %(message)s'
#         },
#     },
#     'filters': {
#         'require_debug_true': {
#             '()': 'django.utils.log.RequireDebugTrue',
#         },
#         'require_debug_false': {
#             '()': 'django.utils.log.RequireDebugFalse',
#         },
#     },
#     'handlers': {
#         'console': {
#             'level': 'DEBUG',
#             'filters': ['require_debug_true'],
#             'class': 'logging.StreamHandler',
#             'formatter': 'verbose',
#         },
#         'request_handler': {
#             'level': 'DEBUG',
#             'filters': ['require_debug_false'],
#             'class': 'logging.StreamHandler',
#             'formatter': 'verbose',
#         }
#     },
#     'loggers': {
#         'django.db.backends': {
#             'level': 'DEBUG',
#             'handlers': ['console'],
#         },
#         'django.request': {
#             'handlers': ['console', 'request_handler'],
#             'level': 'DEBUG',
#             'propagate': False,
#         },
#     }
# }

# Password validation
# https://docs.djangoproject.com/en/3.0/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/3.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'
TIME_ZONE_PLACE = 'America/New_York'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.0/howto/static-files/

STATIC_URL = '/static/'
AUTH_USER_MODEL = 'users.UserProfile'
TEST_RUNNER = 'core.common.tests.CustomTestRunner'
DEFAULT_LOCALE = os.environ.get('DEFAULT_LOCALE', 'en')
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID', '')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY', '')
AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME', 'ocl-api-dev')
AWS_REGION_NAME = os.environ.get('AWS_REGION_NAME', 'us-east-1')
DISABLE_VALIDATION = os.environ.get('DISABLE_VALIDATION', False)
API_SUPERUSER_PASSWORD = os.environ.get('API_SUPERUSER_PASSWORD', 'Root123')  # password for ocladmin superuser
API_SUPERUSER_TOKEN = os.environ.get(
    'API_SUPERUSER_TOKEN', '891b4b17feab99f3ff7e5b5d04ccc5da7aa96da6'
)

#celery/redis
REDIS_PORT = os.environ.get('REDIS_PORT', 6379)
REDIS_DB = 0
REDIS_HOST = os.environ.get('REDIS_HOST', 'redis')

CELERY_DEFAULT_QUEUE = 'default'
CELERY_QUEUES = (
    Queue('default', Exchange('default'), routing_key='default'),
)
CELERY_ENABLE_UTC = True
CELERY_TIMEZONE = "UTC"
# Sensible settings for celery
CELERY_ALWAYS_EAGER = False
CELERY_ACKS_LATE = True
CELERY_TASK_PUBLISH_RETRY = True
CELERY_DISABLE_RATE_LIMITS = False
CELERY_IGNORE_RESULT = False
CELERY_SEND_TASK_ERROR_EMAILS = False
CELERY_RESULT_BACKEND = 'redis://%s:%s/%s' % (REDIS_HOST, REDIS_PORT, REDIS_DB)
CELERY_BROKER_URL = CELERY_RESULT_BACKEND
CELERY_TASK_SERIALIZER = "json"
CELERY_ACCEPT_CONTENT = ['application/json']
CELERYD_HIJACK_ROOT_LOGGER = False
CELERYD_PREFETCH_MULTIPLIER = 1
CELERYD_MAX_TASKS_PER_CHILD = 1000
BROKER_URL = CELERY_RESULT_BACKEND
CELERY_ROUTES = {
    'tasks.bulk_import': {'queue': 'bulk_import'},
    'tasks.bulk_priority_import': {'queue': 'bulk_priority_import'}
}
CELERY_TASK_RESULT_EXPIRES = 259200  # 72 hours
CELERY_TRACK_STARTED = True
ELASTICSEARCH_DSL_PARALLEL = True
ELASTICSEARCH_DSL_AUTO_REFRESH = True
ELASTICSEARCH_DSL_AUTOSYNC = True
ELASTICSEARCH_DSL_SIGNAL_PROCESSOR = 'core.common.models.CelerySignalProcessor'
ES_SYNC = True
USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
ENV = os.environ.get('ENVIRONMENT', 'development')
# Only used for flower
FLOWER_USER = os.environ.get('FLOWER_USER', 'root')
FLOWER_PWD = os.environ.get('FLOWER_PWD', 'Root123')
FLOWER_HOST = os.environ.get('FLOWER_HOST', 'flower')
FLOWER_PORT = os.environ.get('FLOWER_PORT', 5555)
DATA_UPLOAD_MAX_MEMORY_SIZE = 100*1024*1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 100*1024*1024
