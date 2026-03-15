from django.db import models
from django.db.models import Sum
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


# === 1. SEGURIDAD Y PERFILES ===
class PerfilUsuario(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    debe_cambiar_clave = models.BooleanField(default=True)

    def __str__(self):
        return f"Perfil de {self.usuario.username}"

@receiver(post_save, sender=User)
def crear_perfil_usuario(sender, instance, created, **kwargs):
    if created:
        PerfilUsuario.objects.create(usuario=instance)


# === 2. ACTORES PRINCIPALES ===
class Apoderado(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    rut = models.CharField(max_length=12, unique=True, blank=True, null=True) # 👈 Agregado blank y null
    telefono = models.CharField(max_length=15, blank=True)

    def __str__(self):
        if self.user.first_name:
            return f"{self.user.first_name} {self.user.last_name}"
        return self.user.username

class Alumno(models.Model):
    CURSOS = [('8B', '8° Básico')]
    apoderados = models.ManyToManyField(Apoderado, related_name='pupilos')
    nombre_completo = models.CharField(max_length=100)
    numero_lista = models.IntegerField()
    curso = models.CharField(max_length=10, choices=CURSOS, default='8B')

    def __str__(self):
        return f"{self.numero_lista}. {self.nombre_completo}"


# === 3. TESORERÍA Y FINANZAS ===
class CuentaAlumno(models.Model):
    alumno = models.OneToOneField(Alumno, on_delete=models.CASCADE, related_name='cuenta')
    
    # 1. Plata intocable de años anteriores
    cuenta_ahorro = models.IntegerField(default=0) 
    
    # 2. La "Cuenta" operativa del año (Abonos, Rifas, Pago de Cuotas)
    saldo_disponible = models.IntegerField(default=0)

    def __str__(self):
        return f"Cuenta de {self.alumno.nombre_completo}"

    @property
    def total_viaje(self):
        """Calcula mágicamente el dinero del viaje: Ahorro Anterior + Cuotas de Viaje Pagadas este año"""
        pagado_este_ano = self.alumno.cargos.filter(estado='PAGADO', concepto__destino='VIAJE').aggregate(Sum('monto_total'))['monto_total__sum'] or 0
        return self.cuenta_ahorro + pagado_este_ano

class ConceptoCobro(models.Model):
    TIPO_DESTINO = [
        ('CUENTA', 'Fondo del Curso (Cuotas, Salidas, Regalos)'),
        ('EXTERNO', 'Aportes Extra o Voluntarios (Rifas, Solidario, Otros)')
    ]
    nombre = models.CharField(max_length=100)
    monto_estandar = models.IntegerField()
    fecha_vencimiento = models.DateField()
    destino = models.CharField(max_length=20, choices=TIPO_DESTINO, default='CUENTA')

    def __str__(self):
        return f"{self.nombre} (${self.monto_estandar}) - Va a: {self.destino}"

class Cargo(models.Model):
    ESTADOS = [('PENDIENTE', 'Pendiente'), ('PAGADO', 'Pagado completamente')]
    alumno = models.ForeignKey(Alumno, related_name='cargos', on_delete=models.CASCADE)
    concepto = models.ForeignKey(ConceptoCobro, on_delete=models.PROTECT)
    monto_total = models.IntegerField()
    estado = models.CharField(max_length=10, choices=ESTADOS, default='PENDIENTE')
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['estado', '-fecha_creacion']

    def __str__(self):
        return f"[{self.estado}] {self.concepto.nombre} - {self.alumno.nombre_completo}"

class Abono(models.Model):
    ESTADOS = [('REVISION', 'En Revisión'), ('APROBADO', 'Aprobado (Saldo Disponible)'), ('RECHAZADO', 'Rechazado')]
    alumno = models.ForeignKey(Alumno, related_name='abonos', on_delete=models.CASCADE)
    monto = models.IntegerField()
    fecha_transferencia = models.DateField()
    comprobante = models.CharField(max_length=100, blank=True, null=True) 
    estado = models.CharField(max_length=15, choices=ESTADOS, default='REVISION')
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Abono ${self.monto} - {self.alumno.nombre_completo} ({self.estado})"

class MovimientoCuenta(models.Model):
    TIPOS = [('INGRESO', 'Ingreso de Dinero (+)'), ('EGRESO', 'Pago de Deuda o Retiro (-)')]
    cuenta = models.ForeignKey(CuentaAlumno, related_name='movimientos', on_delete=models.CASCADE)
    tipo = models.CharField(max_length=10, choices=TIPOS)
    monto = models.IntegerField()
    descripcion = models.CharField(max_length=200) 
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha']

    def __str__(self):
        return f"{self.tipo} ${self.monto} - {self.cuenta.alumno.nombre_completo}"


# === 4. COMUNICACIÓN Y EVENTOS ===
class Noticia(models.Model):
    ETIQUETAS = [('GENERAL', 'General 📢'), ('FINANZAS', 'Finanzas 💰'), ('ACADEMICO', 'Académico 🎓'), ('URGENTE', 'Urgente 🚨'), ('SOCIAL', 'Social 🎉')]
    titulo = models.CharField(max_length=200)
    contenido = models.TextField()
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    autor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    imagen = models.ImageField(upload_to='noticias/', null=True, blank=True)
    es_importante = models.BooleanField(default=False)
    etiqueta = models.CharField(max_length=20, choices=ETIQUETAS, default='GENERAL')

    def __str__(self):
        return f"{self.titulo} ({self.fecha_creacion.strftime('%d/%m/%Y')})"

class Evento(models.Model):
    TIPOS = [('REUNION', 'Reunión'), ('ACTIVIDAD', 'Actividad'), ('COBRO', 'Cobro / Rifa'), ('ACADEMICO', 'Académico')]
    titulo = models.CharField(max_length=100)
    fecha = models.DateTimeField()
    tipo = models.CharField(max_length=20, choices=TIPOS, default='ACTIVIDAD')
    descripcion = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['fecha'] 

    def __str__(self):
        return f"{self.titulo} - {self.fecha.strftime('%d/%m')}"


# === 5. AHORRO DEL CURSO ===
class DepositoPlazo(models.Model):
    monto = models.IntegerField(default=0)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    alumnos_beneficiarios = models.ManyToManyField(Alumno, related_name='depositos', blank=True)

    def __str__(self):
        return f"Fondo Depósito a Plazo: ${self.monto}"


# === 6. LIBRO DE GASTOS GLOBALES (EGRESOS) ===
class EgresoTesoreria(models.Model):
    monto = models.IntegerField()
    descripcion = models.CharField(max_length=200)
    fecha_gasto = models.DateField()
    comprobante = models.CharField(max_length=100, blank=True, null=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha_gasto', '-fecha_registro']

    def __str__(self):
        return f"Gasto: ${self.monto} - {self.descripcion}"