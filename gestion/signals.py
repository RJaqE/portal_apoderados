from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import AsignacionPago

@receiver(post_save, sender=AsignacionPago)
def actualizar_saldos_al_asignar(sender, instance, created, **kwargs):
    if created:
        # 1. Descontar del Abono (Billetera)
        abono = instance.abono
        abono.saldo_disponible -= instance.monto_asignado
        abono.save()

        # 2. Abonar al Cargo (Deuda)
        cargo = instance.cargo
        cargo.monto_pagado += instance.monto_asignado
        
        # 3. Verificar si se pagó completo
        if cargo.monto_pagado >= cargo.monto_total:
            cargo.estado = 'PAGADO'
        elif cargo.monto_pagado > 0:
            cargo.estado = 'PARCIAL'
        
        cargo.save()

@receiver(post_delete, sender=AsignacionPago)
def devolver_saldos_al_eliminar(sender, instance, **kwargs):
    # Si el tesorero se equivocó y borra la asignación, devolvemos la plata
    
    # 1. Devolver plata al Abono
    abono = instance.abono
    abono.saldo_disponible += instance.monto_asignado
    abono.save()

    # 2. Restar plata al Cargo
    cargo = instance.cargo
    cargo.monto_pagado -= instance.monto_asignado
    
    # Recalcular estado
    if cargo.monto_pagado == 0:
        cargo.estado = 'PENDIENTE'
    elif cargo.monto_pagado < cargo.monto_total:
        cargo.estado = 'PARCIAL'
        
    cargo.save()