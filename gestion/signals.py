from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Alumno, CuentaAlumno

# ==============================================================================
# 1. CREACIÓN AUTOMÁTICA DE LA BILLETERA
# ==============================================================================

@receiver(post_save, sender=Alumno)
def crear_cuenta_alumno(sender, instance, created, **kwargs):
    """
    MAGIA 1: Cuando se inscribe un Alumno nuevo en el sistema, se le crea 
    automáticamente su 'Billetera' (CuentaAlumno) con saldos en $0.
    """
    if created:
        CuentaAlumno.objects.create(alumno=instance)


# ==============================================================================
# NOTA DEL ARQUITECTO:
# Las magias 2 y 3 (Ingreso de dinero y Pago de deudas) fueron movidas 
# a gestion/views.py (AbonoViewSet y CargoViewSet) para permitir un control
# más estricto, revertir pagos y generar historial de auditoría de forma manual.
# ==============================================================================