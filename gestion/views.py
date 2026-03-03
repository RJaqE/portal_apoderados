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

# === IMPORTACIONES ===
from .models import (
    Alumno, CuentaAlumno, Abono, ConceptoCobro, Cargo, MovimientoCuenta, 
    Noticia, Evento, PerfilUsuario
)
from .serializers import (
    AlumnoSerializer, AbonoSerializer, ConceptoSerializer, CargoSerializer, 
    MovimientoCuentaSerializer, NoticiaSerializer, UserSerializer, EventoSerializer
)

# ==============================================================================
# 1. SEGURIDAD: PRIMER INGRESO Y RECUPERACIÓN DE CLAVE (Sin cambios)
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
            return Alumno.objects.all()
        return Alumno.objects.filter(apoderado__user=user)

class AbonoViewSet(viewsets.ModelViewSet):
    queryset = Abono.objects.all().order_by('-fecha_transferencia')
    serializer_class = AbonoSerializer

    def perform_create(self, serializer):
        """ Cuando se CREA un ingreso, sumamos la plata y lo anotamos en la Cartola """
        abono = serializer.save()
        
        # 👇 TRAMPA INTELIGENTE PARA ALUMNOS ANTIGUOS SIN BILLETERA
        from .models import CuentaAlumno
        from django.core.exceptions import ObjectDoesNotExist
        
        try:
            cuenta = abono.alumno.cuenta
        except ObjectDoesNotExist:
            # Si explota porque no tiene cuenta, ¡se la creamos en el acto!
            cuenta = CuentaAlumno.objects.create(alumno=abono.alumno)
            print(f"Cuenta creada automáticamente para {abono.alumno.nombre_completo}")

        # Ahora sí, continuamos normalmente sumando la plata
        cuenta.saldo_disponible += abono.monto
        cuenta.save()
        
        # Anotación en la Cartola de Auditoría
        MovimientoCuenta.objects.create(
            cuenta=cuenta,
            tipo='INGRESO',
            monto=abono.monto,
            descripcion=f"INGRESO DE FONDOS: Ref {abono.comprobante}"
        )

    def perform_destroy(self, instance):
        """ Cuando se ELIMINA un ingreso por error, restamos la plata y lo anotamos """
        cuenta = instance.alumno.cuenta
        
        # Descontamos la plata que se había sumado por error
        cuenta.saldo_disponible -= instance.monto
        cuenta.save()
        
        # Dejamos el registro de la anulación en la Cartola
        MovimientoCuenta.objects.create(
            cuenta=cuenta,
            tipo='EGRESO',
            monto=instance.monto,
            descripcion=f"ANULACIÓN DE INGRESO: Eliminado por Tesorería (Ref: {instance.comprobante})"
        )
        
        # Borramos el registro del abono
        instance.delete()

class ConceptoViewSet(viewsets.ModelViewSet):
    queryset = ConceptoCobro.objects.all()
    serializer_class = ConceptoSerializer

    @action(detail=True, methods=['post'])
    def generar_masivo(self, request, pk=None):
        """ 
        Genera cargos automáticos. Permite excluir IDs específicos.
        Body: { "curso": "8B", "excluidos": [3, 5, 12] }
        """
        concepto = self.get_object() 
        curso_objetivo = request.data.get('curso')
        excluidos_ids = request.data.get('excluidos', []) # Array de IDs de alumnos a omitir

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
            "alumnos_excluidos": len(excluidos_ids)
        })

class CargoViewSet(viewsets.ModelViewSet):
    queryset = Cargo.objects.all().order_by('estado', '-fecha_creacion')
    serializer_class = CargoSerializer
    permission_classes = [permissions.IsAdminUser] 

    @action(detail=True, methods=['post'])
    def pagar_con_billetera(self, request, pk=None):
        """ Saca plata de la billetera, paga la deuda y anota en la cartola """
        cargo = self.get_object()
        
        if cargo.estado == 'PAGADO':
            return Response({"error": "Este cargo ya está pagado."}, status=status.HTTP_400_BAD_REQUEST)
            
        cuenta = cargo.alumno.cuenta
        
        if cuenta.saldo_disponible < cargo.monto_total:
            return Response({"error": "Saldo insuficiente en billetera."}, status=status.HTTP_400_BAD_REQUEST)
            
        # 1. Descontar saldo
        cuenta.saldo_disponible -= cargo.monto_total
        cuenta.save()
        
        # 2. Marcar como pagado
        cargo.estado = 'PAGADO'
        cargo.save()

        # 3. Registrar en Cartola de Auditoría
        MovimientoCuenta.objects.create(
            cuenta=cuenta,
            tipo='EGRESO',
            monto=cargo.monto_total,
            descripcion=f"PAGO DE DEUDA: {cargo.concepto.nombre}"
        )
        
        return Response({"mensaje": "Cargo pagado exitosamente."})

    @action(detail=True, methods=['post'])
    def reversar_pago(self, request, pk=None):
        """ Devuelve la plata a la billetera, revive la deuda y anota en la cartola """
        cargo = self.get_object()
        
        if cargo.estado != 'PAGADO':
            return Response({"error": "Solo se pueden reversar cuotas pagadas."}, status=status.HTTP_400_BAD_REQUEST)
            
        cuenta = cargo.alumno.cuenta
        
        # 1. Devolver saldo a la billetera
        cuenta.saldo_disponible += cargo.monto_total
        cuenta.save()
        
        # 2. Volver la deuda a PENDIENTE
        cargo.estado = 'PENDIENTE'
        cargo.save()

        # 3. Registrar la devolución en Cartola de Auditoría
        MovimientoCuenta.objects.create(
            cuenta=cuenta,
            tipo='INGRESO',
            monto=cargo.monto_total,
            descripcion=f"REVERSO DE PAGO: Devolución por {cargo.concepto.nombre}"
        )
        
        return Response({"mensaje": "Pago reversado. Dinero devuelto a la billetera."})

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
    """ Para ver la Cartola de cada alumno """
    queryset = MovimientoCuenta.objects.all()
    serializer_class = MovimientoCuentaSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return MovimientoCuenta.objects.all()
        return MovimientoCuenta.objects.filter(cuenta__alumno__apoderado__user=user)


# ==============================================================================
# 3. FUNCIONES DE APOYO (API)
# ==============================================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def quien_soy(request):
    serializer = UserSerializer(request.user)
    data = serializer.data
    data['es_staff'] = request.user.is_staff          
    data['es_admin'] = request.user.is_superuser      
    data['debe_cambiar_clave'] = False # 🔥 MODO TESTING 🔥
    return Response(data)

@api_view(['GET'])
@permission_classes([IsAdminUser]) 
def resumen_tesoreria(request):
    """ Dashboard Matemático Inteligente del Tesorero """
    
    # 1. Total real en el banco (Abonos Aprobados)
    recaudado_banco = Abono.objects.filter(estado='APROBADO').aggregate(Sum('monto'))['monto__sum'] or 0
    
    # 2. Total para la Gira (Ahorro Histórico + Fondo Viaje Actual de todos)
    historico = CuentaAlumno.objects.aggregate(Sum('ahorro_historico'))['ahorro_historico__sum'] or 0
    viaje_actual = CuentaAlumno.objects.aggregate(Sum('fondo_viaje_actual'))['fondo_viaje_actual__sum'] or 0
    fondo_viaje_total = historico + viaje_actual
    
    # 3. Dinero flotante (Saldos a favor sin usar en las billeteras)
    dinero_billeteras = CuentaAlumno.objects.aggregate(Sum('saldo_disponible'))['saldo_disponible__sum'] or 0
    
    # 4. Dinero para terceros (Cargos pagados cuyo destino es EXTERNO)
    recaudacion_externa = Cargo.objects.filter(estado='PAGADO', concepto__destino='EXTERNO').aggregate(Sum('monto_total'))['monto_total__sum'] or 0
    
    # 5. Deuda morosa
    deuda_pendiente = Cargo.objects.filter(estado='PENDIENTE').aggregate(Sum('monto_total'))['monto_total__sum'] or 0

    return Response({
        'banco_estimado': recaudado_banco,
        'fondo_gira_estudio': fondo_viaje_total,
        'saldo_flotante_apoderados': dinero_billeteras,
        'por_transferir_terceros': recaudacion_externa,
        'morosidad_pendiente': deuda_pendiente
    })