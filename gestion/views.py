from django.shortcuts import render
from django.db.models import Sum
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser, IsAuthenticatedOrReadOnly

# === IMPORTACIONES DE MODELOS ===
from .models import (
    Alumno, 
    Abono, 
    AsignacionPago, 
    ConceptoCobro, 
    Cargo, 
    Noticia, 
    Evento
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

# ==========================================
#              VISTAS PRINCIPALES
# ==========================================

class AlumnoViewSet(viewsets.ModelViewSet): 
    """
    Vista que entrega los alumnos.
    - Si eres Tesorero (Staff): Ves a TODOS.
    - Si eres Apoderado: Ves solo a TUS pupilos.
    """
    serializer_class = AlumnoSerializer

    def get_queryset(self):
        # 1. Obtenemos al usuario que está logueado (ej: maria)
        user = self.request.user 
        
        # 2. CASO TESORERO: Si es parte del staff, le mostramos TODO.
        if user.is_staff:
            return Alumno.objects.all()
            
        # 3. CASO APODERADO: Filtramos para que vea solo sus hijos.
        # Buscamos alumnos donde el 'apoderado' tenga el 'user' igual al conectado.
        return Alumno.objects.filter(apoderado__user=user)

class AbonoViewSet(viewsets.ModelViewSet):
    """
    Esta vista permite al Tesorero registrar y ver pagos.
    """
    queryset = Abono.objects.all()
    serializer_class = AbonoSerializer

class AsignacionPagoViewSet(viewsets.ModelViewSet):
    """ Permite crear y ver las asignaciones de fondos """
    queryset = AsignacionPago.objects.all()
    serializer_class = AsignacionPagoSerializer

class ConceptoViewSet(viewsets.ModelViewSet):
    """
    Vista para ver los tipos de cobro (Matrícula, Marzo, Rifa, etc.)
    y lanzar cobros masivos.
    """
    queryset = ConceptoCobro.objects.all()
    serializer_class = ConceptoSerializer

    @action(detail=True, methods=['post'])
    def generar_masivo(self, request, pk=None):
        """
        Genera cargos automáticos para todos los alumnos de un curso específico.
        Uso: POST /api/conceptos/{id}/generar_masivo/
        Body: { "curso": "1MA" }
        """
        concepto = self.get_object() # El concepto seleccionado (ej: Marzo)
        curso_objetivo = request.data.get('curso')

        if not curso_objetivo:
            return Response({"error": "Debes especificar el curso (ej: '1MA')"}, status=status.HTTP_400_BAD_REQUEST)

        # 1. Buscar a las víctimas (los alumnos del curso)
        alumnos = Alumno.objects.filter(curso=curso_objetivo)
        
        if not alumnos.exists():
            return Response({"error": f"No se encontraron alumnos en el curso {curso_objetivo}"}, status=status.HTTP_404_NOT_FOUND)

        cantidad_creados = 0
        cantidad_omitidos = 0

        # 2. El Bucle de Creación
        for alumno in alumnos:
            # Validamos si YA tiene este cobro para no duplicarlo
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
    """
    Vista para que el Tesorero administre las deudas (Cargos).
    Solo el Staff (Tesorero) puede tocar esto.
    """
    queryset = Cargo.objects.all()
    serializer_class = CargoSerializer
    permission_classes = [permissions.IsAdminUser] # Solo Admin/Staff puede acceder a esta vista

class NoticiaViewSet(viewsets.ModelViewSet):
    # Esto ordena primero las IMPORTANTES y luego por FECHA (las nuevas arriba)
    queryset = Noticia.objects.all().order_by('-es_importante', '-fecha_creacion')
    serializer_class = NoticiaSerializer
    permission_classes = [IsAuthenticatedOrReadOnly] # Lectura pública, escritura privada

    # 👇 ESTO FALTABA: Asigna automáticamente el autor al crear la noticia
    def perform_create(self, serializer):
        serializer.save(autor=self.request.user)

class EventoViewSet(viewsets.ModelViewSet):
    # Traemos todos los eventos ordenados por fecha
    queryset = Evento.objects.all().order_by('fecha')
    serializer_class = EventoSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

# ==========================================
#              FUNCIONES API
# ==========================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def quien_soy(request):
    """
    Devuelve los datos del usuario conectado y sus permisos (banderas).
    """
    serializer = UserSerializer(request.user)
    data = serializer.data
    
    # Agregamos manualmente las banderas de poder
    data['es_staff'] = request.user.is_staff          # Para Directiva
    data['es_admin'] = request.user.is_superuser      # Para Tesorero (El Mago)
    
    return Response(data)

@api_view(['GET'])
@permission_classes([IsAdminUser]) # <--- Protegido: Solo Directiva/Staff
def resumen_tesoreria(request):
    """
    Calcula los totales para los gráficos del Dashboard.
    """
    # 1. Calcular cuánto dinero ha entrado real (Suma de abonos)
    total_recaudado = Abono.objects.aggregate(Sum('monto_recibido'))['monto_recibido__sum'] or 0
    
    # 2. Calcular cuánto dinero falta por cobrar (Deuda total)
    # Sumamos todos los montos de los cargos y restamos lo pagado
    total_esperado = Cargo.objects.aggregate(Sum('monto_total'))['monto_total__sum'] or 0
    deuda_pendiente = total_esperado - total_recaudado
    
    # 3. Contar morosos (Gente con deuda pendiente)
    morosos_count = Cargo.objects.filter(estado='PENDIENTE').count()

    return Response({
        'recaudado': total_recaudado,
        'por_cobrar': deuda_pendiente,
        'morosos': morosos_count
    })