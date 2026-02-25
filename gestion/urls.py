from django.urls import path, include
from rest_framework.routers import DefaultRouter

# IMPORTANTE: Agregamos todas las vistas, incluyendo las nuevas de seguridad
from .views import (
    AlumnoViewSet, 
    AbonoViewSet, 
    AsignacionPagoViewSet, 
    ConceptoViewSet, 
    CargoViewSet,      # <--- OJO: Asegúrate de tener este si usas la gestión de cargos
    quien_soy,         # <--- NUEVO IMPORT
    NoticiaViewSet,    # <--- NUEVO IMPORT para noticias
    resumen_tesoreria, # <--- NUEVO IMPORT para resumen de tesorería
    EventoViewSet,     # <--- NUEVO IMPORT para eventos
    
    # === NUEVAS VISTAS DE SEGURIDAD ===
    SolicitarEnlaceSeguridad,
    ConfirmarCambioClave,
    RecuperarClaveOlvidada,
)

router = DefaultRouter()
router.register(r'mis-alumnos', AlumnoViewSet, basename='alumno')
router.register(r'pagos', AbonoViewSet)
router.register(r'asignaciones', AsignacionPagoViewSet)
router.register(r'conceptos', ConceptoViewSet)
# Si tu panel de tesorero usa cargos, no olvides esta línea:
router.register(r'cargos', CargoViewSet) 
# === NUEVA RUTA DE NOTICIAS ===
router.register(r'noticias', NoticiaViewSet) 
# === NUEVA RUTA DE EVENTOS ===
router.register(r'eventos', EventoViewSet) 

urlpatterns = [
    # Rutas automáticas del router (ViewSets)
    path('', include(router.urls)),
    
    # === RUTAS MANUALES Y DE FUNCIONES ===
    # Como 'quien_soy' es una función solitaria, va aquí aparte:
    path('quien-soy/', quien_soy, name='quien_soy'),
    
    # RUTA PARA EL RESUMEN DE TESORERÍA
    path('resumen-tesoreria/', resumen_tesoreria, name='resumen_tesoreria'),

    # === RUTAS DE SEGURIDAD (RECUPERACIÓN Y CAMBIO DE CLAVES) ===
    path('seguridad/solicitar-enlace/', SolicitarEnlaceSeguridad.as_view(), name='solicitar-enlace'),
    path('seguridad/confirmar-clave/', ConfirmarCambioClave.as_view(), name='confirmar-clave'),
    path('seguridad/recuperar-clave/', RecuperarClaveOlvidada.as_view(), name='recuperar-clave'),
]