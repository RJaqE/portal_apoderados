from django.urls import path, include
from rest_framework.routers import DefaultRouter

# IMPORTANTE: Agregamos todas las vistas, incluyendo las nuevas de seguridad y finanzas
from .views import (
    AlumnoViewSet, 
    AbonoViewSet, 
    ConceptoViewSet, 
    CargoViewSet,      
    quien_soy,         
    NoticiaViewSet,    
    resumen_tesoreria, 
    EventoViewSet,     
    MovimientoCuentaViewSet, 
    prorratear_monto,  # <--- NUEVO IMPORT (La función mágica de división de dinero)
    
    # === NUEVAS VISTAS DE SEGURIDAD ===
    SolicitarEnlaceSeguridad,
    ConfirmarCambioClave,
    RecuperarClaveOlvidada,
)

router = DefaultRouter()
router.register(r'mis-alumnos', AlumnoViewSet, basename='alumno')
router.register(r'pagos', AbonoViewSet)
router.register(r'conceptos', ConceptoViewSet)
# Si tu panel de tesorero usa cargos, no olvides esta línea:
router.register(r'cargos', CargoViewSet) 
# === NUEVA RUTA DE NOTICIAS ===
router.register(r'noticias', NoticiaViewSet) 
# === NUEVA RUTA DE EVENTOS ===
router.register(r'eventos', EventoViewSet) 
# === NUEVA RUTA DE MOVIMIENTOS DE CUENTA (Cartola Histórica) ===
router.register(r'movimientos', MovimientoCuentaViewSet, basename='movimiento') 

urlpatterns = [
    # Rutas automáticas del router (ViewSets)
    path('', include(router.urls)),
    
    # === RUTAS MANUALES Y DE FUNCIONES ===
    # Como 'quien_soy' es una función solitaria, va aquí aparte:
    path('quien-soy/', quien_soy, name='quien_soy'),
    
    # === RUTAS PARA TESORERÍA ===
    path('resumen-tesoreria/', resumen_tesoreria, name='resumen_tesoreria'),
    path('prorrateo/', prorratear_monto, name='prorrateo'), # <--- NUEVA RUTA CONECTADA AL FRONTEND

    # === RUTAS DE SEGURIDAD (RECUPERACIÓN Y CAMBIO DE CLAVES) ===
    path('seguridad/solicitar-enlace/', SolicitarEnlaceSeguridad.as_view(), name='solicitar-enlace'),
    path('seguridad/confirmar-clave/', ConfirmarCambioClave.as_view(), name='confirmar-clave'),
    path('seguridad/recuperar-clave/', RecuperarClaveOlvidada.as_view(), name='recuperar-clave'),
]