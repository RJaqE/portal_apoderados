from django.contrib import admin
from .models import (
    PerfilUsuario, 
    Apoderado, 
    Alumno, 
    ConceptoCobro, 
    Cargo, 
    Abono, 
    AsignacionPago, 
    Noticia, 
    Evento
)

# ==============================================================================
# 1. SEGURIDAD Y PERFILES
# ==============================================================================

# Usamos un decorador (@) para darle "súperpoderes" a la vista en el panel
@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    # list_display: Muestra estas columnas como una tabla en el panel principal
    list_display = ('usuario', 'debe_cambiar_clave')
    # list_filter: Agrega un menú a la derecha para filtrar a los que ya la cambiaron
    list_filter = ('debe_cambiar_clave',)


# ==============================================================================
# 2. ACTORES PRINCIPALES
# ==============================================================================

admin.site.register(Apoderado)
admin.site.register(Alumno)


# ==============================================================================
# 3. TESORERÍA Y FINANZAS
# ==============================================================================

admin.site.register(ConceptoCobro)
admin.site.register(Cargo)
admin.site.register(Abono)
admin.site.register(AsignacionPago)


# ==============================================================================
# 4. COMUNICACIÓN Y EVENTOS
# ==============================================================================

admin.site.register(Noticia)
admin.site.register(Evento)