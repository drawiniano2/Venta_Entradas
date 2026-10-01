import os
from datetime import timedelta
from pathlib import Path
from dotenv import load_dotenv


# ============================================================
# RUTAS BASE DEL PROYECTO
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

# Carga las variables privadas almacenadas en .env
load_dotenv(BASE_DIR / '.env')


# ============================================================
# CONFIGURACIÓN GENERAL
# ============================================================

SECRET_KEY = 'django-insecure-s$_=2++#&k+aj^xk#$rqm5cx9vlq_4&8ln56gzk$p%6+-!ib62'

DEBUG = False

ALLOWED_HOSTS = [
    "127.0.0.1",
    "localhost",
]


# ============================================================
# APLICACIONES INSTALADAS
# ============================================================

INSTALLED_APPS = [
    # Aplicaciones propias de Django
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',

    # Django REST Framework
    'rest_framework',

    # Filtros para la API
    'django_filters',

    # Documentación OpenAPI / Swagger
    'drf_spectacular',

    # Aplicaciones del proyecto
    'accounts',
    'eventos',
    'carrito',
    'compras',
    'entradas',
]


# ============================================================
# MIDDLEWARE
# ============================================================

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


ROOT_URLCONF = 'config.urls'


# ============================================================
# TEMPLATES
# ============================================================

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',

        'DIRS': [
            BASE_DIR / 'templates',
        ],

        'APP_DIRS': True,

        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]


WSGI_APPLICATION = 'config.wsgi.application'


# ============================================================
# BASE DE DATOS - POSTGRESQL
# ============================================================

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'venta_entradas_db'),
        'USER': os.environ.get('DB_USER', 'venta_entradas_user'),
        'PASSWORD': os.environ.get('DB_PASSWORD', ''),
        'HOST': os.environ.get('DB_HOST', '127.0.0.1'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}


# ============================================================
# MODELO DE USUARIO PERSONALIZADO
# ============================================================

AUTH_USER_MODEL = 'accounts.Usuario'


# ============================================================
# VALIDACIÓN DE CONTRASEÑAS
# ============================================================

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


# ============================================================
# INTERNACIONALIZACIÓN
# ============================================================

LANGUAGE_CODE = 'es-cl'

TIME_ZONE = 'America/Santiago'

USE_I18N = True

USE_TZ = True


# ============================================================
# ARCHIVOS ESTÁTICOS
# ============================================================

STATIC_URL = 'static/'

STATIC_ROOT = BASE_DIR / 'staticfiles'


# ============================================================
# DJANGO REST FRAMEWORK
# ============================================================

REST_FRAMEWORK = {
    # JWT será el mecanismo principal de autenticación de la API.
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),

    # Por defecto los endpoints requerirán autenticación.
    # Los endpoints públicos se habilitarán explícitamente.
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),

    # Permite filtros declarativos con django-filter.
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
    ),

    # drf-spectacular genera el esquema OpenAPI.
    'DEFAULT_SCHEMA_CLASS':
        'drf_spectacular.openapi.AutoSchema',
}


# ============================================================
# JWT
# ============================================================

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=30),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),

    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': False,

    'AUTH_HEADER_TYPES': ('Bearer',),
}


# ============================================================
# OPENAPI / SWAGGER
# ============================================================

SPECTACULAR_SETTINGS = {
    'TITLE': 'API Venta de Entradas',
    'DESCRIPTION': (
        'API REST para la gestión de eventos, recintos, '
        'reservas, compras y entradas.'
    ),
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
}


# ============================================================
# EMAIL - DESARROLLO
# ============================================================

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'


# ============================================================
# CLAVE PRIMARIA POR DEFECTO
# ============================================================

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'







# ============================================================
# MEDIA
# ============================================================

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"



# ============================================================
# AUTENTICACION WEB
# ============================================================

LOGIN_URL = "/login/"
LOGIN_REDIRECT_URL = "/"

