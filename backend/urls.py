from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

# === 1. NUEVOS IMPORTS PARA LAS IMÁGENES ===
from django.conf import settings
from django.conf.urls.static import static

# Vistas para el Token (JWT)
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

# Función "Portero": Si alguien llega a la raíz, mándalo al Admin
def redirect_to_admin(request):
    return redirect('/admin/')

urlpatterns = [
    # La ruta vacía '' ahora ejecuta la redirección
    path('', redirect_to_admin),
    
    path('admin/', admin.site.urls),
    path('api/', include('gestion.urls')),
    
    # Rutas de Autenticación
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]

# === 2. CONFIGURACIÓN MÁGICA PARA VER FOTOS ===
# Esto le dice a Django: "Si estamos en modo desarrollo (DEBUG),
# permite ver los archivos que están en la carpeta media".
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)