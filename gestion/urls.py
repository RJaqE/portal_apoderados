from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

# === IMPORTS PARA IMÁGENES Y MEDIA ===
from django.conf import settings
from django.conf.urls.static import static

# === IMPORTS DE AUTENTICACIÓN (JWT) ===
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

# === IMPORTS DE VISTAS DE SEGURIDAD PROPIAS ===
# 👇 CORRECCIÓN: Agregamos RecuperarClaveOlvidada a la importación
from gestion.views import SolicitarEnlaceSeguridad, ConfirmarCambioClave, RecuperarClaveOlvidada

# ==============================================================================
# FUNCIÓN PORTERO
# ==============================================================================
def redirect_to_admin(request):
    return redirect('/admin/')

# ==============================================================================
# RUTAS PRINCIPALES DEL SISTEMA (URLS)
# ==============================================================================

urlpatterns = [
    # 1. Redirección base (Raíz del sitio)
    path('', redirect_to_admin),
    
    # 2. Panel de Administración de Django
    path('admin/', admin.site.urls),
    
    # 3. Autenticación por Tokens (Login tradicional de Vue)
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # 4. Seguridad: Cambio Obligatorio y Recuperación de Claves (NUEVAS)
    path('api/seguridad/solicitar-enlace/', SolicitarEnlaceSeguridad.as_view(), name='solicitar_enlace'),
    path('api/seguridad/confirmar-clave/', ConfirmarCambioClave.as_view(), name='confirmar_clave'),
    # 👇 CORRECCIÓN: Agregamos la ruta para recuperar clave
    path('api/seguridad/recuperar-clave/', RecuperarClaveOlvidada.as_view(), name='recuperar_clave'),

    # 5. Rutas de la Aplicación de Gestión (Alumnos, Pagos, Noticias, etc.)
    path('api/', include('gestion.urls')),
]

# ==============================================================================
# CONFIGURACIÓN PARA VER ARCHIVOS MULTIMEDIA EN DESARROLLO (LOCAL)
# ==============================================================================
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)