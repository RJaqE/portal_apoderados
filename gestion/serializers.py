from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    Alumno, 
    Cargo, 
    Abono, 
    ConceptoCobro, 
    AsignacionPago, 
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
class ConceptoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConceptoCobro
        fields = '__all__'

class CargoSerializer(serializers.ModelSerializer):
    concepto_nombre = serializers.ReadOnlyField(source='concepto.nombre')
    fecha_vencimiento = serializers.DateField(source='concepto.fecha_vencimiento', read_only=True)
    concepto_tipo = serializers.ReadOnlyField(source='concepto.tipo')
    alumno_nombre = serializers.ReadOnlyField(source='alumno.nombre_completo')

    class Meta:
        model = Cargo
        fields = [
            'id', 'alumno', 'alumno_nombre', 'concepto', 'concepto_nombre', 
            'concepto_tipo', 'fecha_vencimiento', 'monto_total', 
            'monto_pagado', 'estado'
        ]

class AbonoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Abono
        fields = ['id', 'alumno', 'monto_recibido', 'saldo_disponible', 'fecha_pago', 'comprobante']

class AsignacionPagoSerializer(serializers.ModelSerializer):
    class Meta:
        model = AsignacionPago
        fields = '__all__'

# === ALUMNO ===
class AlumnoSerializer(serializers.ModelSerializer):
    cargos = CargoSerializer(many=True, read_only=True)
    abonos = AbonoSerializer(many=True, read_only=True)
    
    deuda_por_pagar = serializers.SerializerMethodField()
    saldo_a_favor = serializers.SerializerMethodField()
    
    # Campo calculado: "Jaque, Pablo"
    nombre_lista = serializers.SerializerMethodField()
    
    # 👇 NUEVO: Campos extraídos del Apoderado asociado 👇
    apoderado_nombre = serializers.SerializerMethodField()
    apoderado_email = serializers.SerializerMethodField()

    class Meta:
        model = Alumno
        fields = [
            'id', 'nombre_completo', 'rut', 'curso', 'cargos', 'abonos', 
            'deuda_por_pagar', 'saldo_a_favor', 'nombre_lista',
            'apoderado_nombre', 'apoderado_email' # <- Agregamos los campos aquí
        ]

    def get_deuda_por_pagar(self, obj):
        return sum((c.monto_total - c.monto_pagado) for c in obj.cargos.all())

    def get_saldo_a_favor(self, obj):
        return sum(a.saldo_disponible for a in obj.abonos.all())

    # Magia para ordenar por apellido
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

    # 👇 NUEVO: Lógica para rescatar los datos del apoderado
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