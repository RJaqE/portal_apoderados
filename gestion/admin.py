from django.contrib import admin
from .models import Apoderado, Alumno, ConceptoCobro, Cargo, Abono, AsignacionPago, Noticia, Evento # <--- Asegúrate de importar Noticia y Evento aquí

# Registramos los modelos para que aparezcan en el panel
admin.site.register(Apoderado)
admin.site.register(Alumno)
admin.site.register(ConceptoCobro)
admin.site.register(Evento)
admin.site.register(Cargo)
admin.site.register(Abono)
admin.site.register(AsignacionPago)
admin.site.register(Noticia) # <--- Registramos Noticia para que sea editable desde el admin