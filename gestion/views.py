import os
import json
import threading
import urllib.request

from django.shortcuts import render
from django.db.models import Sum
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser, IsAuthenticatedOrReadOnly
from rest_framework.views import APIView

from .models import (
    Alumno, CuentaAlumno, Abono, ConceptoCobro, Cargo, MovimientoCuenta, 
    Noticia, Evento, PerfilUsuario, DepositoPlazo, EgresoTesoreria
)
from .serializers import (
    AlumnoSerializer, AbonoSerializer, ConceptoSerializer, CargoSerializer, 
    MovimientoCuentaSerializer, NoticiaSerializer, UserSerializer, EventoSerializer,
    DepositoPlazoSerializer, EgresoTesoreriaSerializer
)

# ==============================================================================
# 1. SEGURIDAD: PRIMER INGRESO Y RECUPERACIÓN DE CLAVE
# ==============================================================================
def generar_correo_html(usuario, enlace):
    return f"""
    <html>
        <body style="font-family: Arial, sans-serif; background-color: #f4f6f9; padding: 20px;">
            <div style="max-width: 500px; margin: 0 auto; background-color: #ffffff; padding: 30px; border-radius: 10px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); text-align: center;">
                <h1 style="color: #2c3e50; margin-bottom: 5px;">🎓 Portal Apoderados</h1>
                <p style="color: #7f8c8d; font-size: 14px; margin-top: 0;">Generación 2030 - 8°B</p>
                <hr style="border: 0; height: 1px; background: #eeeeee; margin: 20px 0;">
                <h2 style="color: #34495e;">¡Hola {usuario.username}!</h2>
                <p style="color: #555555; font-size: 16px; line-height: 1.5;">Hemos recibido una solicitud para asegurar tu cuenta o cambiar tu contraseña. Para continuar, haz clic en el siguiente botón:</p>
                <a href="{enlace}" style="display: inline-block; background-color: #4CAF50; color: #ffffff; padding: 12px 25px; text-decoration: none; border-radius: 5px; font-weight: bold; font-size: 16px; margin: 20px 0;">Crear Nueva Contraseña ✨</a>
                <p style="color: #999999; font-size: 12px; margin-top: 30px;">Si tú no solicitaste este cambio, puedes ignorar este correo con total seguridad.</p>
            </div>
        </body>
    </html>
    """

class SolicitarEnlaceSeguridad(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        usuario = request.user
        nuevo_correo = request.data.get('correo')
        if not nuevo_correo:
            return Response({'error': 'Debes proporcionar un correo electrónico.'}, status=status.HTTP_400_BAD_REQUEST)

        usuario.email = nuevo_correo
        usuario.save()

        token = default_token_generator.make_token(usuario)
        enlace = f"https://portal-apoderados.netlify.app/cambiar-clave?token={token}&uid={usuario.id}"
        mensaje_html = generar_correo_html(usuario, enlace)
        
        def enviar_correo_en_hilo():
            try:
                URL_WEBHOOK_MAKE = "https://hook.us2.make.com/j2ld34kv46topljqtpgng0n6q88bg7oe" 
                datos = {"destinatario": nuevo_correo, "asunto": "🔒 Verifica tu correo - Portal", "html": mensaje_html}
                datos_json = json.dumps(datos).encode('utf-8')
                req = urllib.request.Request(URL_WEBHOOK_MAKE, data=datos_json, headers={'Content-Type': 'application/json'})
                urllib.request.urlopen(req)
            except Exception as e: print(f"Error: {str(e)}")

        threading.Thread(target=enviar_correo_en_hilo).start()
        return Response({'mensaje': 'Correo enviado exitosamente.'})

class ConfirmarCambioClave(APIView):
    permission_classes = []
    def post(self, request):
        uid = request.data.get('uid')
        token = request.data.get('token')
        nueva_clave = request.data.get('nueva_clave')

        try: usuario = User.objects.get(pk=uid)
        except User.DoesNotExist: return Response({'error': 'Usuario no válido.'}, status=status.HTTP_400_BAD_REQUEST)

        if default_token_generator.check_token(usuario, token):
            usuario.set_password(nueva_clave)
            usuario.save()
            perfil = usuario.perfil
            perfil.debe_cambiar_clave = False
            perfil.save()
            return Response({'mensaje': 'Contraseña actualizada con éxito.'})
        return Response({'error': 'El enlace es inválido o ha expirado.'}, status=status.HTTP_400_BAD_REQUEST)

class RecuperarClaveOlvidada(APIView):
    permission_classes = []
    def post(self, request):
        correo = request.data.get('correo')
        if not correo: return Response({'error': 'Debes proporcionar un correo.'}, status=status.HTTP_400_BAD_REQUEST)

        usuario = User.objects.filter(email=correo).first()
        if usuario:
            token = default_token_generator.make_token(usuario)
            enlace = f"https://portal-apoderados.netlify.app/cambiar-clave?token={token}&uid={usuario.id}"
            mensaje_html = generar_correo_html(usuario, enlace)

            def enviar_correo_en_hilo():
                try:
                    URL_WEBHOOK_MAKE = "https://hook.us2.make.com/j2ld34kv46topljqtpgng0n6q88bg7oe" 
                    datos = {"destinatario": correo, "asunto": "🔑 Recuperación de Contraseña", "html": mensaje_html}
                    datos_json = json.dumps(datos).encode('utf-8')
                    req = urllib.request.Request(URL_WEBHOOK_MAKE, data=datos_json, headers={'Content-Type': 'application/json'})
                    urllib.request.urlopen(req)
                except Exception as e: print(f"Error: {str(e)}")

            threading.Thread(target=enviar_correo_en_hilo).start()
            return Response({'mensaje': 'Enlace enviado si el correo existe.'}) 
        return Response({'error': 'correo_no_encontrado'}, status=status.HTTP_404_NOT_FOUND)


# ==============================================================================
# 2. VISTAS PRINCIPALES (GESTIÓN)
# ==============================================================================

class AlumnoViewSet(viewsets.ModelViewSet): 
    serializer_class = AlumnoSerializer
    def get_queryset(self):
        user = self.request.user 
        if user.is_staff:
            return Alumno.objects.all().order_by('numero_lista')
        return Alumno.objects.filter(apoderados__user=user).order_by('numero_lista')

class AbonoViewSet(viewsets.ModelViewSet):
    queryset = Abono.objects.all().order_by('-fecha_transferencia')
    serializer_class = AbonoSerializer

    def perform_create(self, serializer):
        abono = serializer.save()
        from django.core.exceptions import ObjectDoesNotExist
        
        try:
            cuenta = abono.alumno.cuenta
        except ObjectDoesNotExist:
            cuenta = CuentaAlumno.objects.create(alumno=abono.alumno)
        
        cuenta.saldo_disponible += abono.monto
        cuenta.save()
        
        MovimientoCuenta.objects.create(
            cuenta=cuenta,
            tipo='INGRESO',
            monto=abono.monto,
            descripcion=f"INGRESO DE FONDOS: Ref {abono.comprobante}"
        )

    def perform_destroy(self, instance):
        cuenta = instance.alumno.cuenta
        cuenta.saldo_disponible -= instance.monto
        cuenta.save()
        
        MovimientoCuenta.objects.create(
            cuenta=cuenta,
            tipo='EGRESO',
            monto=instance.monto,
            descripcion=f"ANULACIÓN DE INGRESO: Eliminado por Tesorería (Ref: {instance.comprobante})"
        )
        instance.delete()

class ConceptoViewSet(viewsets.ModelViewSet):
    queryset = ConceptoCobro.objects.all()
    serializer_class = ConceptoSerializer

    @action(detail=True, methods=['post'])
    def generar_masivo(self, request, pk=None):
        concepto = self.get_object() 
        curso_objetivo = request.data.get('curso')
        excluidos_ids = request.data.get('excluidos', []) 

        if not curso_objetivo:
            return Response({"error": "Especifica el curso"}, status=status.HTTP_400_BAD_REQUEST)

        alumnos = Alumno.objects.filter(curso=curso_objetivo).exclude(id__in=excluidos_ids)
        creados = 0
        omitidos = 0

        for alumno in alumnos:
            existe = Cargo.objects.filter(alumno=alumno, concepto=concepto).exists()
            if not existe:
                Cargo.objects.create(
                    alumno=alumno,
                    concepto=concepto,
                    monto_total=concepto.monto_estandar,
                    estado='PENDIENTE'
                )
                creados += 1
            else:
                omitidos += 1

        return Response({
            "mensaje": "Cobro masivo generado",
            "cargos_creados": creados,
            "cargos_ya_existian": omitidos,
        })
    
    @action(detail=True, methods=['post'])
    def rendir_fondo(self, request, pk=None):
        concepto = self.get_object()
        
        if concepto.estado_fondo == 'RENDIDO':
            return Response({"error": "El fondo ya fue rendido."}, status=status.HTTP_400_BAD_REQUEST)
        
        # 1. Recibimos los datos del tesorero
        monto = request.data.get('monto')
        descripcion = request.data.get('descripcion')
        fecha_gasto = request.data.get('fecha_gasto')
        comprobante = request.data.get('comprobante', '')

        # 2. Anotamos el gasto en el libro de Egresos
        EgresoTesoreria.objects.create(
            monto=monto, 
            descripcion=descripcion, 
            fecha_gasto=fecha_gasto, 
            comprobante=comprobante
        )
        
        # 3. Cerramos el Montoncito
        concepto.estado_fondo = 'RENDIDO'
        concepto.save()
        
        return Response({"mensaje": "Fondo transferido y registrado en egresos correctamente."})

class CargoViewSet(viewsets.ModelViewSet):
    queryset = Cargo.objects.all().order_by('estado', '-fecha_creacion')
    serializer_class = CargoSerializer
    permission_classes = [permissions.IsAdminUser] 

    @action(detail=True, methods=['post'])
    def pagar_con_billetera(self, request, pk=None):
        cargo = self.get_object()
        
        if cargo.estado == 'PAGADO':
            return Response({"error": "Este cargo ya está pagado."}, status=status.HTTP_400_BAD_REQUEST)
            
        cuenta = cargo.alumno.cuenta
        
        if cuenta.saldo_disponible < cargo.monto_total:
            return Response({"error": "Saldo insuficiente en billetera."}, status=status.HTTP_400_BAD_REQUEST)
            
        cuenta.saldo_disponible -= cargo.monto_total
        cuenta.save()
        
        cargo.estado = 'PAGADO'
        cargo.save()

        MovimientoCuenta.objects.create(
            cuenta=cuenta,
            tipo='EGRESO',
            monto=cargo.monto_total,
            descripcion=f"PAGO DE DEUDA: {cargo.concepto.nombre}"
        )
        
        return Response({"mensaje": "Cargo pagado exitosamente."})

    @action(detail=True, methods=['post'])
    def reversar_pago(self, request, pk=None):
        cargo = self.get_object()

        # 👇 NUEVA REGLA: Si el montoncito ya se transfirió al proveedor, no se puede devolver la plata.
        if cargo.concepto.estado_fondo == 'RENDIDO':
            return Response({"error": "No puedes anular este pago. Los fondos de este concepto ya fueron rendidos/transferidos al proveedor."}, status=status.HTTP_400_BAD_REQUEST)
        
        if cargo.estado != 'PAGADO':
            return Response({"error": "Solo se pueden reversar cuotas pagadas."}, status=status.HTTP_400_BAD_REQUEST)
            
        cuenta = cargo.alumno.cuenta
        
        cuenta.saldo_disponible += cargo.monto_total
        cuenta.save()
        
        cargo.estado = 'PENDIENTE'
        cargo.save()

        MovimientoCuenta.objects.create(
            cuenta=cuenta,
            tipo='INGRESO',
            monto=cargo.monto_total,
            descripcion=f"REVERSO DE PAGO: Devolución por {cargo.concepto.nombre}"
        )
        
        return Response({"mensaje": "Pago reversado. Dinero devuelto a la billetera."})

class EgresoTesoreriaViewSet(viewsets.ModelViewSet):
    queryset = EgresoTesoreria.objects.all()
    serializer_class = EgresoTesoreriaSerializer
    permission_classes = [IsAuthenticated]

class NoticiaViewSet(viewsets.ModelViewSet):
    queryset = Noticia.objects.all().order_by('-es_importante', '-fecha_creacion')
    serializer_class = NoticiaSerializer
    permission_classes = [IsAuthenticatedOrReadOnly] 
    def perform_create(self, serializer):
        serializer.save(autor=self.request.user)

class EventoViewSet(viewsets.ModelViewSet):
    queryset = Evento.objects.all().order_by('fecha')
    serializer_class = EventoSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

class MovimientoCuentaViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = MovimientoCuenta.objects.all()
    serializer_class = MovimientoCuentaSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return MovimientoCuenta.objects.all()
        return MovimientoCuenta.objects.filter(cuenta__alumno__apoderados__user=user)


# ==============================================================================
# 3. FUNCIONES DE APOYO Y PRORRATEO
# ==============================================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def quien_soy(request):
    serializer = UserSerializer(request.user)
    data = serializer.data
    data['es_staff'] = request.user.is_staff          
    data['es_admin'] = request.user.is_superuser      
    data['debe_cambiar_clave'] = False 
    return Response(data)

@api_view(['GET'])
@permission_classes([IsAdminUser]) 
def resumen_tesoreria(request):
    recaudado_banco = Abono.objects.filter(estado='APROBADO').aggregate(Sum('monto'))['monto__sum'] or 0
    historico = CuentaAlumno.objects.aggregate(Sum('cuenta_ahorro'))['cuenta_ahorro__sum'] or 0
    viaje_actual = Cargo.objects.filter(estado='PAGADO', concepto__destino='VIAJE').aggregate(Sum('monto_total'))['monto_total__sum'] or 0
    
    fondo_viaje_total = historico + viaje_actual
    dinero_billeteras = CuentaAlumno.objects.aggregate(Sum('saldo_disponible'))['saldo_disponible__sum'] or 0
    recaudacion_externa = Cargo.objects.filter(estado='PAGADO', concepto__destino='EXTERNO').aggregate(Sum('monto_total'))['monto_total__sum'] or 0
    deuda_pendiente = Cargo.objects.filter(estado='PENDIENTE').aggregate(Sum('monto_total'))['monto_total__sum'] or 0

    return Response({
        'banco_estimado': recaudado_banco,
        'fondo_gira_estudio': fondo_viaje_total,
        'saldo_flotante_apoderados': dinero_billeteras,
        'por_transferir_terceros': recaudacion_externa,
        'morosidad_pendiente': deuda_pendiente
    })

@api_view(['POST'])
@permission_classes([IsAdminUser])
def prorratear_monto(request):
    """
    Divide ganancias o gastos globales equitativamente entre los alumnos elegidos.
    Body esperado: { "alumnos_ids": [1, 2, 3], "monto_total": 200000, "tipo": "INGRESO", "descripcion": "Rifa de Navidad" }
    """
    alumnos_ids = request.data.get('alumnos_ids', [])
    monto_total = int(request.data.get('monto_total', 0))
    tipo = request.data.get('tipo', 'INGRESO')
    descripcion = request.data.get('descripcion', 'Repartición general')

    if not alumnos_ids or monto_total <= 0:
        return Response({"error": "Debes seleccionar alumnos y un monto válido."}, status=status.HTTP_400_BAD_REQUEST)

    cantidad = len(alumnos_ids)
    monto_individual = monto_total // cantidad
    sobrante = monto_total % cantidad 

    cuentas = CuentaAlumno.objects.filter(alumno__id__in=alumnos_ids)

    for i, cuenta in enumerate(cuentas):
        monto_aplicar = monto_individual + (1 if i < sobrante else 0)

        if tipo == 'INGRESO':
            cuenta.saldo_disponible += monto_aplicar
        else:
            cuenta.saldo_disponible -= monto_aplicar

        cuenta.save()

        MovimientoCuenta.objects.create(
            cuenta=cuenta,
            tipo=tipo,
            monto=monto_aplicar,
            descripcion=f"{descripcion} (Total: ${monto_total} dividido en {cantidad} alumnos)"
        )

    return Response({"mensaje": f"¡Éxito! Se aplicaron ${monto_individual} a la cuenta de {cantidad} alumnos."})

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def gestionar_deposito(request):
    # Buscamos el primer depósito (asumiendo que es un único fondo del curso)
    deposito = DepositoPlazo.objects.first()
    
    if request.method == 'GET':
        if not deposito:
            return Response({}) # Retorna vacío si aún no se ha creado
        serializer = DepositoPlazoSerializer(deposito)
        return Response(serializer.data)
        
    elif request.method == 'POST':
        # Si ya existe, lo actualizamos. Si no, lo creamos desde cero.
        if deposito:
            serializer = DepositoPlazoSerializer(deposito, data=request.data)
        else:
            serializer = DepositoPlazoSerializer(data=request.data)
            
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)