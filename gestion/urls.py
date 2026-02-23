from django.urls import path, include
from rest_framework.routers import DefaultRouter
# IMPORTANTE: Agregamos 'quien_soy' a los imports
from .views import (
    AlumnoViewSet, 
    AbonoViewSet, 
    AsignacionPagoViewSet, 
    ConceptoViewSet, 
    CargoViewSet, # <--- OJO: Asegúrate de tener este si usas la gestión de cargos
    quien_soy,     # <--- NUEVO IMPORT
    NoticiaViewSet, # <--- NUEVO IMPORT para noticias
    resumen_tesoreria, # <--- NUEVO IMPORT para resumen de tesorería
    EventoViewSet, # <--- NUEVO IMPORT para eventos
)

router = DefaultRouter()
router.register(r'mis-alumnos', AlumnoViewSet, basename='alumno')
router.register(r'pagos', AbonoViewSet)
router.register(r'asignaciones', AsignacionPagoViewSet)
router.register(r'conceptos', ConceptoViewSet)
# Si tu panel de tesorero usa cargos, no olvides esta línea:
router.register(r'cargos', CargoViewSet) 
# === NUEVA RUTA DE NOTICIAS ===
router.register(r'noticias', NoticiaViewSet) # <--- 2. AGREGAR ESTA LÍNEA
# ... dentro de router.register ...
router.register(r'eventos', EventoViewSet) # <--- 2. AGREGAR ESTA LÍNEA

urlpatterns = [
    # Rutas automáticas del router (ViewSets)
    path('', include(router.urls)),
    
    # === NUEVA RUTA MANUAL ===
    # Como 'quien_soy' es una función solitaria, va aquí aparte:
    path('quien-soy/', quien_soy, name='quien_soy'),
    # RUTA PARA EL RESUMEN DE TESORERÍA
    path('resumen-tesoreria/', resumen_tesoreria, name='resumen_tesoreria'),
]