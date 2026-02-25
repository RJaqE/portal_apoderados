import os
from pathlib import Path
from datetime import timedelta
import dj_database_url
from dotenv import load_dotenv

# ==============================================================================
# 1. ENTORNO Y RUTAS BASE
# ==============================================================================

# Cargar variables de entorno desde el archivo .env (solo para desarrollo local)
load_dotenv()

# Ruta principal de tu proyecto
BASE_DIR = Path(__file__).resolve().parent.parent

# ==============================================================================
# 2. SEGURIDAD PRINCIPAL
# ==============================================================================

# Clave secreta (lee la de Railway en producción, o usa una por defecto en local)
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-@$*vfr6=$8t7y9bh$%rt0%#=6+8u0a*3552=-db&=q05caj4!d')

# Modo depuración (True en tu PC para ver errores, False en Railway por seguridad)
DEBUG = os.environ.get('DEBUG', 'True') == 'True'

# Dominios permitidos para alojar esta API
ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    'portalapoderados-production.up.railway.app',
]

# ==============================================================================
# 3. APLICACIONES Y MIDDLEWARE
# ==============================================================================

INSTALLED_APPS = [
    # Apps por defecto de Django
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Librerías de terceros instaladas
    'rest_framework', 
    'corsheaders',

    # 👇 AGREGAR ESTAS DOS LÍNEAS AQUÍ:
    'cloudinary',
    'cloudinary_storage',
    
    # Tus aplicaciones
    'gestion', 
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',            # 👈 CORS siempre debe ir primero
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',       # 👈 Whitenoise justo después de Security
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'backend.urls'
WSGI_APPLICATION = 'backend.wsgi.application'

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

# ==============================================================================
# 4. BASE DE DATOS
# ==============================================================================

if os.environ.get('DATABASE_URL'):
    # ESTAMOS EN RAILWAY 🚂 (Producción)
    DATABASES = {
        'default': dj_database_url.config(
            default=os.environ.get('DATABASE_URL'),
            conn_max_age=600 # Mantiene conexiones abiertas para mayor rapidez
        )
    }
else:
    # ESTAMOS EN TU PC LOCAL 💻 (Desarrollo)
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

# ==============================================================================
# 5. CONFIGURACIÓN REGIONAL Y VALIDACIONES
# ==============================================================================

LANGUAGE_CODE = 'es-cl'
TIME_ZONE = 'America/Santiago'
USE_I18N = True
USE_TZ = True

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ==============================================================================
# 6. ARCHIVOS ESTÁTICOS Y MULTIMEDIA
# ==============================================================================

# Archivos CSS/JS/Imágenes del sistema (Whitenoise)
STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Archivos subidos por los usuarios (Fotos, PDFs, etc.)
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# 👇 Le dice a Django: "Guarda las fotos de los usuarios en Cloudinary"
DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'

# ==============================================================================
# 7. SEGURIDAD EXTERNA (CORS Y CSRF)
# ==============================================================================

# Orígenes Frontend que tienen permiso para leer la API (Netlify y tu Localhost)
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://portal-apoderados.netlify.app",
]

# Orígenes que tienen permiso para enviar datos y formularios de forma segura
CSRF_TRUSTED_ORIGINS = [
    'https://portalapoderados-production.up.railway.app',
    'https://portal-apoderados.netlify.app',
]

# ==============================================================================
# 8. AUTENTICACIÓN POR TOKENS (JWT)
# ==============================================================================

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60), # La sesión activa dura 1 hora
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),    # Permite renovar sesión sin pedir clave por 1 día
    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': False,
}