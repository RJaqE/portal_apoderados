from django.contrib import admin
from .models import (PerfilUsuario, Apoderado, Alumno, CuentaAlumno, ConceptoCobro, 
                     Cargo, Abono, MovimientoCuenta, Noticia, Evento, DepositoPlazo,
                     EgresoTesoreria, ImagenGaleria) # 👈 Agregamos ImagenGaleria

@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'debe_cambiar_clave')
    list_filter = ('debe_cambiar_clave',)

admin.site.register(Apoderado)

@admin.register(Alumno)
class AlumnoAdmin(admin.ModelAdmin):
    list_display = ('numero_lista', 'nombre_completo', 'curso', 'ver_apoderados')
    search_fields = ('nombre_completo', 'numero_lista')
    
    def ver_apoderados(self, obj):
        nombres = [str(apoderado) for apoderado in obj.apoderados.all()]
        return ", ".join(nombres) if nombres else "Sin apoderado"
    ver_apoderados.short_description = 'Apoderados'

@admin.register(CuentaAlumno)
class CuentaAlumnoAdmin(admin.ModelAdmin):
    list_display = ('alumno', 'cuenta_ahorro', 'saldo_disponible', 'total_viaje')
    search_fields = ('alumno__nombre_completo',)

@admin.register(ConceptoCobro)
class ConceptoCobroAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'monto_estandar', 'destino', 'fecha_vencimiento')
    list_filter = ('destino',)

@admin.register(Cargo)
class CargoAdmin(admin.ModelAdmin):
    list_display = ('alumno', 'concepto', 'monto_total', 'estado', 'fecha_creacion')
    list_filter = ('estado', 'concepto')
    search_fields = ('alumno__nombre_completo',)

@admin.register(Abono)
class AbonoAdmin(admin.ModelAdmin):
    list_display = ('alumno', 'monto', 'fecha_transferencia', 'estado')
    list_filter = ('estado',)
    search_fields = ('alumno__nombre_completo',)

@admin.register(MovimientoCuenta)
class MovimientoCuentaAdmin(admin.ModelAdmin):
    list_display = ('cuenta', 'tipo', 'monto', 'descripcion', 'fecha')
    list_filter = ('tipo',)
    search_fields = ('cuenta__alumno__nombre_completo', 'descripcion')

# 👇 NUEVO: Configuración para que la galería se vea DENTRO de la Noticia
class ImagenGaleriaInline(admin.TabularInline):
    model = ImagenGaleria
    extra = 1  # Muestra 1 espacio en blanco por defecto para subir fotos

@admin.register(Noticia)
class NoticiaAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'etiqueta', 'fecha_creacion', 'autor', 'es_importante')
    list_filter = ('etiqueta', 'es_importante')
    search_fields = ('titulo', 'contenido')
    inlines = [ImagenGaleriaInline] # 👈 Aquí conectamos la galería

admin.site.register(Evento)
admin.site.register(DepositoPlazo)
admin.site.register(EgresoTesoreria)