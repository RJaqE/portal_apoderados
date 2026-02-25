import os
from django.shortcuts import render
from django.db.models import Sum
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail

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

class SolicitarEnlaceSeguridad(APIView):
    """ Envía un correo con el código mágico para cambiar la contraseña """
    permission_classes = [IsAuthenticated] # Solo el usuario recién logueado con clave temporal

    def post(self, request):
        usuario = request.user
        nuevo_correo = request.data.get('correo')

        if not nuevo_correo:
            return Response({'error': 'Debes proporcionar un correo electrónico.'}, status=status.HTTP_400_BAD_REQUEST)

        # Guardamos el correo real del apoderado
        usuario.email = nuevo_correo
        usuario.save()

        # Generamos el código secreto temporal
        token = default_token_generator.make_token(usuario)
        enlace = f"http://localhost:5173/cambiar-clave?token={token}&uid={usuario.id}"

        mensaje = f"""
        ¡Hola {usuario.username}!
        
        Hemos recibido una solicitud para asegurar tu cuenta en el Portal de Apoderados.
        Por favor, haz clic en el siguiente enlace para verificar tu correo y crear tu contraseña definitiva:
        
        {enlace}
        
        Si no solicitaste esto, puedes ignorar este correo.
        """
        
        try:
            send_mail(
                '🔒 Verifica tu correo - Portal Apoderados',
                mensaje,
                os.environ.get('EMAIL_HOST_USER'),
                [nuevo_correo],
                fail_silently=False,
            )
            return Response({'mensaje': 'Correo enviado exitosamente. Revisa tu bandeja de entrada.'})
        except Exception as e:
            return Response({'error': f'Error al enviar el correo: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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