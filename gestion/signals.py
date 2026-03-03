from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import Alumno, CuentaAlumno, Abono, MovimientoCuenta, Cargo

# ==============================================================================
# 1. CREACIÓN AUTOMÁTICA DE LA BILLETERA
# ==============================================================================

@receiver(post_save, sender=Alumno)
def crear_cuenta_alumno(sender, instance, created, **kwargs):
    """
    MAGIA 1: Cuando se inscribe un Alumno nuevo, se le crea automáticamente 
    su 'Billetera' (CuentaAlumno) con saldos en $0.
    """
    if created:
        CuentaAlumno.objects.create(alumno=instance)


# ==============================================================================
# 2. INGRESO DE DINERO: Aprobación de Abonos
# ==============================================================================

@receiver(pre_save, sender=Abono)
def capturar_estado_anterior_abono(sender, instance, **kwargs):
    """ Toma una 'foto' del estado del Abono justo antes de guardarse en la BD. """
    if instance.pk:
        instance._estado_anterior = Abono.objects.get(pk=instance.pk).estado
    else:
        instance._estado_anterior = None

@receiver(post_save, sender=Abono)
def procesar_abono_aprobado(sender, instance, created, **kwargs):
    """
    MAGIA 2: Si el tesorero aprueba un Abono (comprobante de transferencia), 
    el dinero entra al Saldo Disponible y queda registrado en la Cartola Histórica.
    """
    estado_anterior = getattr(instance, '_estado_anterior', None)
    
    # Solo ejecutamos la matemática si acaba de cambiar a APROBADO
    if instance.estado == 'APROBADO' and estado_anterior != 'APROBADO':
        cuenta = instance.alumno.cuenta
        
        # 1. Engordamos la billetera
        cuenta.saldo_disponible += instance.monto
        cuenta.save()
        
        # 2. Dejamos el comprobante en la cartola
        fecha_str = instance.fecha_transferencia.strftime('%d/%m/%Y')
        MovimientoCuenta.objects.create(
            cuenta=cuenta,
            tipo='INGRESO',
            monto=instance.monto,
            descripcion=f"Abono aprobado (Transferencia del {fecha_str})"
        )


# ==============================================================================
# 3. EGRESO DE DINERO: Pago de Deudas (Cargos) y Enrutador
# ==============================================================================

@receiver(pre_save, sender=Cargo)
def capturar_estado_anterior_cargo(sender, instance, **kwargs):
    """ Toma una 'foto' del estado del Cargo justo antes de guardarse. """
    if instance.pk:
        instance._estado_anterior = Cargo.objects.get(pk=instance.pk).estado
    else:
        instance._estado_anterior = None

@receiver(post_save, sender=Cargo)
def procesar_cargo_pagado(sender, instance, created, **kwargs):
    """
    MAGIA 3: Si un Cargo se marca como PAGADO:
    1. Se descuenta de la Billetera (Saldo Disponible).
    2. Enrutador: Si es para el VIAJE, engorda el pozo actual.
    3. Se registra el movimiento en la Cartola.
    """
    estado_anterior = getattr(instance, '_estado_anterior', None)

    # Solo ejecutamos si acaba de ser marcado como PAGADO
    if instance.estado == 'PAGADO' and estado_anterior != 'PAGADO':
        cuenta = instance.alumno.cuenta
        
        # 1. Descontamos la plata de la billetera
        cuenta.saldo_disponible -= instance.monto_total
        
        # 2. ENRUTADOR: ¿A dónde va la plata?
        # Si es para el viaje, engordamos el ahorro de este año.
        # Si es EXTERNO (ej: Centro de Padres), el dinero "se esfuma" lógicamente
        # porque la tesorera se lo entregará a un tercero.
        if instance.concepto.destino == 'VIAJE':
            cuenta.fondo_viaje_actual += instance.monto_total
            
        cuenta.save()
        
        # 3. Dejamos el registro del gasto en la cartola
        MovimientoCuenta.objects.create(
            cuenta=cuenta,
            tipo='EGRESO',
            monto=instance.monto_total,
            descripcion=f"Pago de {instance.concepto.nombre}"
        )