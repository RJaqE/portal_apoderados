from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    Alumno, 
    CuentaAlumno, 
    MovimientoCuenta,
    Cargo, 
    Abono, 
    ConceptoCobro, 
    Noticia, 
    Evento
)

# === SERIALIZER DE USUARIO ===
class UserSerializer(serializers.ModelSerializer):
    nombre_completo = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'nombre_completo']

    def get_nombre_completo(self, obj):
        if obj.first_name and obj.last_name:
            return f"{obj.first_name} {obj.last_name}"
        return obj.username


# === FINANZAS ===
class CuentaAlumnoSerializer(serializers.ModelSerializer):
    class Meta:
        model = CuentaAlumno
        fields = ['id', 'ahorro_historico', 'fondo_viaje_actual', 'saldo_disponible', 'total_ahorrado_viaje']

class MovimientoCuentaSerializer(serializers.ModelSerializer):
    class Meta:
        model = MovimientoCuenta
        fields = '__all__'

class ConceptoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConceptoCobro
        fields = '__all__'

class CargoSerializer(serializers.ModelSerializer):
    concepto_nombre = serializers.ReadOnlyField(source='concepto.nombre')
    fecha_vencimiento = serializers.DateField(source='concepto.fecha_vencimiento', read_only=True)
    concepto_destino = serializers.ReadOnlyField(source='concepto.destino')
    alumno_nombre = serializers.ReadOnlyField(source='alumno.nombre_completo')

    class Meta:
        model = Cargo
        fields = [
            'id', 'alumno', 'alumno_nombre', 'concepto', 'concepto_nombre', 
            'concepto_destino', 'fecha_vencimiento', 'monto_total', 
            'estado', 'fecha_creacion'
        ]

class AbonoSerializer(serializers.ModelSerializer):
    alumno_nombre = serializers.ReadOnlyField(source='alumno.nombre_completo')
    
    class Meta:
        model = Abono
        fields = ['id', 'alumno', 'alumno_nombre', 'monto', 'fecha_transferencia', 'comprobante', 'estado', 'fecha_registro']


# === ALUMNO ===
class AlumnoSerializer(serializers.ModelSerializer):
    # Relaciones y anidaciones
    cargos = CargoSerializer(many=True, read_only=True)
    abonos = AbonoSerializer(many=True, read_only=True)
    cuenta = CuentaAlumnoSerializer(read_only=True)
    
    # Campos calculados
    deuda_por_pagar = serializers.SerializerMethodField()
    nombre_lista = serializers.SerializerMethodField()
    apoderado_nombre = serializers.SerializerMethodField()
    apoderado_email = serializers.SerializerMethodField()

    class Meta:
        model = Alumno
        fields = [
            'id', 'nombre_completo', 'rut', 'curso', 'cargos', 'abonos', 'cuenta',
            'deuda_por_pagar', 'nombre_lista', 'apoderado_nombre', 'apoderado_email'
        ]

    def get_deuda_por_pagar(self, obj):
        # Suma todos los cargos cuyo estado sea PENDIENTE
        return sum(c.monto_total for c in obj.cargos.filter(estado='PENDIENTE'))

    def get_nombre_lista(self, obj):
        if not obj.nombre_completo:
            return "Sin Nombre"
        partes = obj.nombre_completo.strip().split() 
        if len(partes) == 2:
            return f"{partes[1]}, {partes[0]}" 
        elif len(partes) >= 3:
            apellidos = f"{partes[-2]} {partes[-1]}"
            nombres = " ".join(partes[:-2])
            return f"{apellidos}, {nombres}" 
        return obj.nombre_completo.strip()

    def get_apoderado_nombre(self, obj):
        try:
            user = obj.apoderado.user
            if user.first_name and user.last_name:
                return f"{user.first_name} {user.last_name}"
            return user.username
        except AttributeError:
            return "Sin Apoderado Asignado"

    def get_apoderado_email(self, obj):
        try:
            email = obj.apoderado.user.email
            return email if email else "Sin Email Registrado"
        except AttributeError:
            return "---"

# === MURO ===
class NoticiaSerializer(serializers.ModelSerializer):
    autor_nombre = serializers.SerializerMethodField()
    class Meta:
        model = Noticia
        fields = '__all__'
        read_only_fields = ['autor', 'fecha_creacion']

    def get_autor_nombre(self, obj):
        if obj.autor:
            if obj.autor.first_name and obj.autor.last_name:
                return f"{obj.autor.first_name} {obj.autor.last_name}"
            return obj.autor.username
        return "Anónimo"

class EventoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Evento
        fields = '__all__'