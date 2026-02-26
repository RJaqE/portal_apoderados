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

# === IMPORTACIONES DE MODELOS ===
from .models import (
    Alumno, 
    Abono, 
    AsignacionPago, 
    ConceptoCobro, 
    Cargo, 
    Noticia, 
    Evento,
    PerfilUsuario
)

# === IMPORTACIONES DE SERIALIZERS ===
from .serializers import (
    AlumnoSerializer, 
    AbonoSerializer, 
    AsignacionPagoSerializer, 
    ConceptoSerializer, 
    CargoSerializer, 
    NoticiaSerializer, 
    UserSerializer,
    EventoSerializer
)

# ==============================================================================
# 1. SEGURIDAD: PRIMER INGRESO Y RECUPERACIÓN DE CLAVE
# ==============================================================================

# 🎨 PLANTILLA HTML PARA LOS CORREOS (Diseño Premium)
# Nota: Las triples comillas (""") permiten escribir texto en varias líneas, no es un comentario.
def generar_correo_html(usuario, enlace):
    return f"""
    <html>
        <body style="font-family: Arial, sans-serif; background-color: #f4f6f9; padding: 20px;">
            <div style="max-width: 500px; margin: 0 auto; background-color: #ffffff; padding: 30px; border-radius: 10px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); text-align: center;">
                <h1 style="color: #2c3e50; margin-bottom: 5px;">🎓 Portal Apoderados</h1>
                <p style="color: #7f8c8d; font-size: 14px; margin-top: 0;">Generación 2030 - 8°B</p>
                
                <hr style="border: 0; height: 1px; background: #eeeeee; margin: 20px 0;">
                
                <h2 style="color: #34495e;">¡Hola {usuario.username}!</h2>
                <p style="color: #555555; font-size: 16px; line-height: 1.5;">
                    Hemos recibido una solicitud para asegurar tu cuenta o cambiar tu contraseña. 
                    Para continuar, haz clic en el siguiente botón:
                </p>
                
                <a href="{enlace}" style="display: inline-block; background-color: #4CAF50; color: #ffffff; padding: 12px 25px; text-decoration: none; border-radius: 5px; font-weight: bold; font-size: 16px; margin: 20px 0;">
                    Crear Nueva Contraseña ✨
                </a>
                
                <p style="color: #999999; font-size: 12px; margin-top: 30px;">
                    Si tú no solicitaste este cambio, puedes ignorar este correo con total seguridad. El enlace caducará pronto.
                </p>
            </div>
        </body>
    </html>
    """

class SolicitarEnlaceSeguridad(APIView):
    """ Envía un correo con el código mágico para usuarios nuevos (Primer Ingreso) """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        usuario = request.user
        nuevo_correo = request.data.get('correo')

        if not nuevo_correo:
            return Response({'error': 'Debes proporcionar un correo electrónico.'}, status=status.HTTP_400_BAD_REQUEST)

        # Guardamos el correo real del apoderado
        usuario.email = nuevo_correo
        usuario.save()

        token = default_token_generator.make_token(usuario)
        # OJO: Cambiar por la URL real de Netlify cuando pases a producción definitiva
        enlace = f"https://portal-apoderados.netlify.app/cambiar-clave?token={token}&uid={usuario.id}"
        mensaje_html = generar_correo_html(usuario, enlace)
        
        # 🧵 MAGIA WEBHOOK: Despacha la info a Make.com en segundo plano
        def enviar_correo_en_hilo():
            try:
                # 👇 URL REAL DE MAKE.COM
                URL_WEBHOOK_MAKE = "https://hook.us2.make.com/j2ld34kv46topljqtpgng0n6q88bg7oe" 
                
                datos = {
                    "destinatario": nuevo_correo,
                    "asunto": "🔒 Verifica tu correo - Portal Apoderados",
                    "html": mensaje_html
                }
                
                datos_json = json.dumps(datos).encode('utf-8')
                req = urllib.request.Request(
                    URL_WEBHOOK_MAKE, 
                    data=datos_json, 
                    headers={'Content-Type': 'application/json'}
                )
                urllib.request.urlopen(req)
                print("Webhook (Primer Ingreso) enviado con éxito a Make.com")
            except Exception as e:
                print(f"Error enviando webhook: {str(e)}")

        # 🚀 Ejecutamos el hilo y respondemos inmediatamente a Vue
        hilo = threading.Thread(target=enviar_correo_en_hilo)
        hilo.start()

        return Response({'mensaje': 'Correo enviado exitosamente. Revisa tu bandeja de entrada.'})


class ConfirmarCambioClave(APIView):
    """ Recibe el click del correo, valida el token y guarda la nueva contraseña """
    permission_classes = [] # Público, porque el usuario llega aquí sin estar logueado (desde el correo)

    def post(self, request):
        uid = request.data.get('uid')
        token = request.data.get('token')
        nueva_clave = request.data.get('nueva_clave')

        try:
            usuario = User.objects.get(pk=uid)
        except User.DoesNotExist:
            return Response({'error': 'Usuario no válido.'}, status=status.HTTP_400_BAD_REQUEST)

        # Si el token es correcto y no ha expirado
        if default_token_generator.check_token(usuario, token):
            usuario.set_password(nueva_clave)
            usuario.save()

            # Le quitamos la marca de novato (¡Es libre!)
            perfil = usuario.perfil
            perfil.debe_cambiar_clave = False
            perfil.save()

            return Response({'mensaje': 'Contraseña actualizada con éxito. Ya puedes iniciar sesión.'})
        else:
            return Response({'error': 'El enlace es inválido o ha expirado.'}, status=status.HTTP_400_BAD_REQUEST)


class RecuperarClaveOlvidada(APIView):
    """ Envía un enlace para cambiar contraseña si el usuario olvidó la suya """
    permission_classes = [] # Público

    def post(self, request):
        correo = request.data.get('correo')

        if not correo:
            return Response({'error': 'Debes proporcionar un correo electrónico.'}, status=status.HTTP_400_BAD_REQUEST)

        # Buscamos al usuario por su correo
        usuario = User.objects.filter(email=correo).first()

        if usuario:
            # Si lo encontramos, reciclamos la lógica de tokens
            token = default_token_generator.make_token(usuario)
            
            # OJO: Cambiar por la URL real de Netlify en el futuro
            enlace = f"https://portal-apoderados.netlify.app/cambiar-clave?token={token}&uid={usuario.id}"
            mensaje_html = generar_correo_html(usuario, enlace)

            # 🧵 MAGIA WEBHOOK
            def enviar_correo_en_hilo():
                try:
                    # 👇 URL REAL DE MAKE.COM
                    URL_WEBHOOK_MAKE = "https://hook.us2.make.com/j2ld34kv46topljqtpgng0n6q88bg7oe" 
                    
                    datos = {
                        "destinatario": correo,
                        "asunto": "🔑 Recuperación de Contraseña - Portal Apoderados",
                        "html": mensaje_html
                    }
                    
                    datos_json = json.dumps(datos).encode('utf-8')
                    req = urllib.request.Request(
                        URL_WEBHOOK_MAKE, 
                        data=datos_json, 
                        headers={'Content-Type': 'application/json'}
                    )
                    urllib.request.urlopen(req)
                    print("Webhook (Recuperar Clave) enviado con éxito a Make.com")
                except Exception as e:
                    print(f"Error enviando webhook: {str(e)}")

            # 🚀 Despachamos el hilo
            hilo = threading.Thread(target=enviar_correo_en_hilo)
            hilo.start()

            # Le respondemos a Vue INMEDIATAMENTE
            return Response({'mensaje': 'Enlace enviado si el correo existe.'}) 
        else:
            # 🚨 El correo no existe. Le avisamos a Vue con un código especial.
            return Response({'error': 'correo_no_encontrado'}, status=status.HTTP_404_NOT_FOUND)


# ==============================================================================
# 2. VISTAS PRINCIPALES (GESTIÓN)
# ==============================================================================

class AlumnoViewSet(viewsets.ModelViewSet): 
    """
    Vista que entrega los alumnos.
    - Tesorero (Staff): Ve a TODOS.
    - Apoderado: Ve solo a TUS pupilos.
    """
    serializer_class = AlumnoSerializer

    def get_queryset(self):
        user = self.request.user 
        
        if user.is_staff:
            return Alumno.objects.all()
            
        return Alumno.objects.filter(apoderado__user=user)

class AbonoViewSet(viewsets.ModelViewSet):
    """ Registra y muestra pagos """
    queryset = Abono.objects.all()
    serializer_class = AbonoSerializer

class AsignacionPagoViewSet(viewsets.ModelViewSet):
    """ Asigna un pago a una deuda específica """
    queryset = AsignacionPago.objects.all()
    serializer_class = AsignacionPagoSerializer

class ConceptoViewSet(viewsets.ModelViewSet):
    """ Tipos de cobro y generación masiva """
    queryset = ConceptoCobro.objects.all()
    serializer_class = ConceptoSerializer

    @action(detail=True, methods=['post'])
    def generar_masivo(self, request, pk=None):
        """
        Genera cargos automáticos para todos los alumnos de un curso.
        Body: { "curso": "8B" }
        """
        concepto = self.get_object() 
        curso_objetivo = request.data.get('curso')

        if not curso_objetivo:
            return Response({"error": "Debes especificar el curso (ej: '8B')"}, status=status.HTTP_400_BAD_REQUEST)

        alumnos = Alumno.objects.filter(curso=curso_objetivo)
        if not alumnos.exists():
            return Response({"error": f"No se encontraron alumnos en el curso {curso_objetivo}"}, status=status.HTTP_404_NOT_FOUND)

        cantidad_creados = 0
        cantidad_omitidos = 0

        for alumno in alumnos:
            existe = Cargo.objects.filter(alumno=alumno, concepto=concepto).exists()
            if not existe:
                Cargo.objects.create(
                    alumno=alumno,
                    concepto=concepto,
                    monto_total=concepto.monto_estandar,
                    monto_pagado=0,
                    estado='PENDIENTE'
                )
                cantidad_creados += 1
            else:
                cantidad_omitidos += 1

        return Response({
            "mensaje": "Proceso finalizado",
            "cargos_creados": cantidad_creados,
            "cargos_ya_existian": cantidad_omitidos,
            "curso": curso_objetivo,
            "concepto": concepto.nombre
        })

class CargoViewSet(viewsets.ModelViewSet):
    """ Panel de deudas, solo visible para el Tesorero """
    queryset = Cargo.objects.all()
    serializer_class = CargoSerializer
    permission_classes = [permissions.IsAdminUser] 

class NoticiaViewSet(viewsets.ModelViewSet):
    """ Muro de noticias: Las importantes primero """
    queryset = Noticia.objects.all().order_by('-es_importante', '-fecha_creacion')
    serializer_class = NoticiaSerializer
    permission_classes = [IsAuthenticatedOrReadOnly] 

    def perform_create(self, serializer):
        serializer.save(autor=self.request.user)

class EventoViewSet(viewsets.ModelViewSet):
    """ Calendario """
    queryset = Evento.objects.all().order_by('fecha')
    serializer_class = EventoSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


# ==============================================================================
# 3. FUNCIONES DE APOYO (API)
# ==============================================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def quien_soy(request):
    """ Devuelve los datos del usuario conectado y sus permisos. """
    serializer = UserSerializer(request.user)
    data = serializer.data
    
    data['es_staff'] = request.user.is_staff          
    data['es_admin'] = request.user.is_superuser      
    
    # 👇 ESTO ES CLAVE: Le avisamos a Vue si el usuario está obligado a cambiar clave
    try:
        data['debe_cambiar_clave'] = request.user.perfil.debe_cambiar_clave
    except:
        # Si por algún motivo el usuario no tiene perfil, lo dejamos pasar por defecto
        data['debe_cambiar_clave'] = False 

    return Response(data)

@api_view(['GET'])
@permission_classes([IsAdminUser]) 
def resumen_tesoreria(request):
    """ Cálculos rápidos para el Dashboard """
    total_recaudado = Abono.objects.aggregate(Sum('monto_recibido'))['monto_recibido__sum'] or 0
    total_esperado = Cargo.objects.aggregate(Sum('monto_total'))['monto_total__sum'] or 0
    deuda_pendiente = total_esperado - total_recaudado
    morosos_count = Cargo.objects.filter(estado='PENDIENTE').count()

    return Response({
        'recaudado': total_recaudado,
        'por_cobrar': deuda_pendiente,
        'morosos': morosos_count
    })