from django.db import models
from django.contrib.auth.models import User

class Apoderado(models.Model):
    # Enlace directo al sistema de Login de Django
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    rut = models.CharField(max_length=12, unique=True)
    telefono = models.CharField(max_length=15, blank=True)

    def __str__(self):
        # Evita error si el usuario no tiene nombre puesto
        if self.user.first_name:
            return f"{self.user.first_name} {self.user.last_name}"
        return self.user.username

class Alumno(models.Model):
    CURSOS = [
        ('8B', '8° Básico'),
        ('1M', '1° Medio'),
        ('2M', '2° Medio'),
        ('3M', '3° Medio'),
        ('4M', '4° Medio'),
    ]
    apoderado = models.ForeignKey(Apoderado, related_name='pupilos', on_delete=models.CASCADE)
    nombre_completo = models.CharField(max_length=100)
    rut = models.CharField(max_length=12, unique=True)
    curso = models.CharField(max_length=10, choices=CURSOS)

    def __str__(self):
        return self.nombre_completo

class ConceptoCobro(models.Model):
    """
    Define los tipos de cobros (Marzo, Abril, Rifa, etc.)
    """
    # === AQUÍ ESTÁ EL CAMBIO CLAVE ===
    TIPO_CHOICES = [
        ('MENSUALIDAD', 'Mensualidad (Cuota)'),
        ('EXTRA', 'Extra (Paseos, Rifas, etc.)')
    ]

    nombre = models.CharField(max_length=100)
    monto_estandar = models.IntegerField()
    fecha_vencimiento = models.DateField()
    
    # Campo nuevo con default para no romper la base de datos existente
    tipo = models.CharField(
        max_length=20, 
        choices=TIPO_CHOICES, 
        default='MENSUALIDAD' 
    )

    def __str__(self):
        return f"{self.nombre} (${self.monto_estandar})"

class Cargo(models.Model):
    """ Representa una DEUDA que el alumno debe pagar """
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
    """ Representa el DINERO que ingresó por transferencia """
    alumno = models.ForeignKey(Alumno, related_name='abonos', on_delete=models.CASCADE)
    monto_recibido = models.IntegerField()
    saldo_disponible = models.IntegerField()
    fecha_pago = models.DateField()
    comprobante = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"Pago de {self.alumno.nombre_completo} - ${self.monto_recibido}"

class AsignacionPago(models.Model):
    """ La 'Goma' que pega un Abono con un Cargo específico """
    abono = models.ForeignKey(Abono, on_delete=models.CASCADE, related_name='asignaciones')
    cargo = models.ForeignKey(Cargo, on_delete=models.CASCADE, related_name='asignaciones')
    monto_asignado = models.IntegerField()
    fecha_asignacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"${self.monto_asignado} de {self.abono.id} a {self.cargo.concepto.nombre}"
    
class Noticia(models.Model):
    # Opciones para la etiqueta
    ETIQUETAS = [
        ('GENERAL', 'General 📢'),
        ('FINANZAS', 'Finanzas 💰'),
        ('ACADEMICO', 'Académico 🎓'),
        ('URGENTE', 'Urgente 🚨'),
        ('SOCIAL', 'Social 🎉'),
    ]

    titulo = models.CharField(max_length=200)
    contenido = models.TextField() # Texto largo para el detalle
    fecha_creacion = models.DateTimeField(auto_now_add=True) # Se pone sola la fecha
    
    # Autor: Quién escribió la noticia (Enlazado al usuario del sistema)
    autor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    # Imagen: Opcional (blank=True) por si solo es texto
    imagen = models.ImageField(upload_to='noticias/', null=True, blank=True)
    
    # Destacado: Para que aparezca arriba o con color
    es_importante = models.BooleanField(default=False)
    
    etiqueta = models.CharField(max_length=20, choices=ETIQUETAS, default='GENERAL')

    def __str__(self):
        return f"{self.titulo} ({self.fecha_creacion.strftime('%d/%m/%Y')})"
    
# ... tus otros modelos (Alumno, Noticia, etc.)

class Evento(models.Model):
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

    def __str__(self):
        return f"{self.titulo} - {self.fecha.strftime('%d/%m')}"

    class Meta:
        ordering = ['fecha'] # Ordenar siempre por el más próximo