
from pathlib import Path
import os

import dj_database_url
from dotenv import load_dotenv

# 👇 ESTO LEE EL ARCHIVO .env (que ignoramos en git)
load_dotenv() 


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/6.0/howto/deployment/checklist/



# 👇 SEGURIDAD: Ahora lee la clave secreta desde el servidor (Railway) o usa la local de respaldo
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-@$*vfr6=$8t7y9bh$%rt0%#=6+8u0a*3552=-db&=q05caj4!d')

# SECURITY WARNING: don't run with debug turned on in production!
# 👇 DEBUG: En tu PC será True, en Railway será False
DEBUG = os.environ.get('DEBUG', 'False') == 'True'

# 👇 ALLOWED_HOSTS: Permitimos que cualquier dominio se conecte (luego lo restringiremos por seguridad)
ALLOWED_HOSTS = ['*']

# 👇 Le dice a Django que confíe en los formularios que vienen de tu dominio de Railway
CSRF_TRUSTED_ORIGINS = [
    'https://portalapoderados-production.up.railway.app',
]

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # TUS APPS Y LIBRERIAS:
    'rest_framework',   # <--- ¡ESTA LÍNEA ES OBLIGATORIA!
    'corsheaders',
    'gestion',                             
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware', # <--- AGREGAR AQUÍ AL PRINCIPIO
    'django.middleware.security.SecurityMiddleware',
    # 👇 AGREGAR ESTA LÍNEA EXACTAMENTE AQUÍ
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'backend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'backend.wsgi.application'


# Database
# https://docs.djangoproject.com/en/6.0/ref/settings/#databases



# 👇 REEMPLAZA TU SECCIÓN DATABASES POR ESTO:

if os.environ.get('DATABASE_URL'):
    # ESTAMOS EN RAILWAY 🚂
    DATABASES = {
        'default': dj_database_url.config(
            default=os.environ.get('DATABASE_URL'),
            conn_max_age=600 # Mantiene conexiones abiertas para mayor rapidez
        )
    }
else:
    # ESTAMOS EN TU PC LOCAL 💻 (Mantén tu configuración exacta aquí)
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': 'portal_apoderados_db',
            'USER': 'root',
            'PASSWORD': 'Carla2012',
            'HOST': 'localhost',
            'PORT': '3306',
        }
    }

# Password validation
# https://docs.djangoproject.com/en/6.0/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/6.0/topics/i18n/

LANGUAGE_CODE = 'es-cl'

TIME_ZONE = 'America/Santiago'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/6.0/howto/static-files/

STATIC_URL = 'static/'

# 👇 AGREGAR ESTO PARA PRODUCCIÓN:
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

CORS_ALLOW_ALL_ORIGINS = True      # <--- AGREGAR ESTA LÍNEA PARA PERMITIR TODAS LAS ORÍGENES

# === CONFIGURACIÓN DE SEGURIDAD (JWT) ===

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
}

from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60), # La pulsera dura 1 hora
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),    # Puedes renovarla por 1 dia
    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': False,
}

# URL base para acceder a los archivos (ej: http://localhost:8000/media/foto.jpg)
MEDIA_URL = '/media/'

# Dónde se guardan físicamente en tu carpeta del proyecto
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')