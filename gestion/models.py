from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

# ==============================================================================
# 1. SEGURIDAD Y PERFILES (Fase 2 de validación de correos)
# ==============================================================================

class PerfilUsuario(models.Model):
    """
    La 'mochila' de seguridad del usuario. 
    Controla si el apoderado debe cambiar su contraseña obligatoriamente al primer ingreso.
    """
    # Relación 1 a 1: Cada Usuario tiene exactamente 1 Perfil
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    
    # LA MARCA DEL NOVATO: Por defecto, todo usuario nuevo DEBE cambiar su clave
    debe_cambiar_clave = models.BooleanField(default=True)

    def __str__(self):
        return f"Perfil de {self.usuario.username}"

# ⚡ MAGIA AUTOMÁTICA (Señal): 
# Cada vez que se crea un Usuario nuevo, Django automáticamente le crea su PerfilUsuario
@receiver(post_save, sender=User)
def crear_perfil_usuario(sender, instance, created, **kwargs):
    if created:
        PerfilUsuario.objects.create(usuario=instance)


# ==============================================================================
# 2. ACTORES PRINCIPALES (Apoderados y Alumnos)
# ==============================================================================

class Apoderado(models.Model):
    """ Representa al adulto responsable. Está enlazado al sistema de Login (User). """
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    rut = models.CharField(max_length=12, unique=True)
    telefono = models.CharField(max_length=15, blank=True)

    def __str__(self):
        # Evita error en el panel de admin si el usuario no tiene nombre puesto
        if self.user.first_name:
            return f"{self.user.first_name} {self.user.last_name}"
        return self.user.username

class Alumno(models.Model):
    """ Representa al estudiante. Un apoderado puede tener varios pupilos. """
    CURSOS = [
        ('8B', '8° Básico'),
        # Cursos comentados para ir agregándolos a medida que se necesite implementar:
        # ('1M', '1° Medio'),
        # ('2M', '2° Medio'),
        # ('3M', '3° Medio'),
        # ('4M', '4° Medio'),
    ]
    apoderado = models.ForeignKey(Apoderado, related_name='pupilos', on_delete=models.CASCADE)
    nombre_completo = models.CharField(max_length=100)
    rut = models.CharField(max_length=12, unique=True)
    curso = models.CharField(max_length=10, choices=CURSOS, default='8B')

    def __str__(self):
        return self.nombre_completo


# ==============================================================================
# 3. TESORERÍA Y FINANZAS
# ==============================================================================

class ConceptoCobro(models.Model):
    """ Define los tipos de cobros generales (Mensualidad de Marzo, Rifa, etc.) """
    TIPO_CHOICES = [
        ('MENSUALIDAD', 'Mensualidad (Cuota)'),
        ('EXTRA', 'Extra (Paseos, Rifas, etc.)')
    ]

    nombre = models.CharField(max_length=100)
    monto_estandar = models.IntegerField()
    fecha_vencimiento = models.DateField()
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='MENSUALIDAD')

    def __str__(self):
        return f"{self.nombre} (${self.monto_estandar})"

class Cargo(models.Model):
    """ Representa una DEUDA específica que un alumno debe pagar """
    ESTADOS = [
        ('PENDIENTE', 'Pendiente'),
        ('PARCIAL', 'Pago Parcial'),
        ('PAGADO', 'Pagado completamente'),
    ]
    alumno = models.ForeignKey(Alumno, related_name='cargos', on_delete=models.CASCADE)
    concepto = models.ForeignKey(ConceptoCobro, on_delete=models.PROTECT)
    monto_total = models.IntegerField()
    monto_pagado = models.IntegerField(default=0)
    estado = models.CharField(max_length=10, choices=ESTADOS, default='PENDIENTE')

    def __str__(self):
        return f"{self.concepto.nombre} - {self.alumno.nombre_completo} ({self.estado})"

class Abono(models.Model):
    """ Representa el DINERO real que ingresó a la cuenta por transferencia """
    alumno = models.ForeignKey(Alumno, related_name='abonos', on_delete=models.CASCADE)
    monto_recibido = models.IntegerField()
    saldo_disponible = models.IntegerField()
    fecha_pago = models.DateField()
    comprobante = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"Pago de {self.alumno.nombre_completo} - ${self.monto_recibido}"

class AsignacionPago(models.Model):
    """ La 'Goma' que pega un Abono con un Cargo específico para justificar el pago """
    abono = models.ForeignKey(Abono, on_delete=models.CASCADE, related_name='asignaciones')
    cargo = models.ForeignKey(Cargo, on_delete=models.CASCADE, related_name='asignaciones')
    monto_asignado = models.IntegerField()
    fecha_asignacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"${self.monto_asignado} de {self.abono.id} a {self.cargo.concepto.nombre}"


# ==============================================================================
# 4. COMUNICACIÓN Y EVENTOS
# ==============================================================================

class Noticia(models.Model):
    """ Publicaciones para el muro principal de los apoderados """
    ETIQUETAS = [
        ('GENERAL', 'General 📢'),
        ('FINANZAS', 'Finanzas 💰'),
        ('ACADEMICO', 'Académico 🎓'),
        ('URGENTE', 'Urgente 🚨'),
        ('SOCIAL', 'Social 🎉'),
    ]

    titulo = models.CharField(max_length=200)
    contenido = models.TextField()
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    autor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    imagen = models.ImageField(upload_to='noticias/', null=True, blank=True) # Se guarda en Cloudinary
    es_importante = models.BooleanField(default=False)
    etiqueta = models.CharField(max_length=20, choices=ETIQUETAS, default='GENERAL')

    def __str__(self):
        return f"{self.titulo} ({self.fecha_creacion.strftime('%d/%m/%Y')})"

class Evento(models.Model):
    """ Calendario de actividades del curso """
    TIPOS = [
        ('REUNION', 'Reunión'),
        ('ACTIVIDAD', 'Actividad'),
        ('COBRO', 'Cobro / Rifa'),
        ('ACADEMICO', 'Académico'),
    ]

    titulo = models.CharField(max_length=100)
    fecha = models.DateTimeField()
    tipo = models.CharField(max_length=20, choices=TIPOS, default='ACTIVIDAD')
    descripcion = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['fecha'] # Ordenar siempre por el más próximo

    def __str__(self):
        return f"{self.titulo} - {self.fecha.strftime('%d/%m')}"