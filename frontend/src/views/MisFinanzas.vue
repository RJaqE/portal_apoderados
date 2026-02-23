<script setup>
import { ref, onMounted, computed } from 'vue'
import api from '../axios'
// 👇 IMPORTAMOS EL COMPONENTE NUEVO
import TarjetaAlumno from '../components/TarjetaAlumno.vue'

const alumnos = ref([])
const cargando = ref(true)
const esStaff = ref(false)

// Variables exclusivas para Staff (Buscador y Selección)
const busquedaAlumno = ref('')
const alumnoSeleccionadoId = ref(null)

onMounted(async () => {
    try {
        // 1. Verificamos Rol
        const resUser = await api.get('quien-soy/')
        esStaff.value = resUser.data.es_staff || resUser.data.es_admin

        // 2. Cargamos Alumnos
        const resAlumnos = await api.get('mis-alumnos/')
        alumnos.value = resAlumnos.data

        // 3. (Solo Staff) Seleccionamos el primero por defecto
        if (esStaff.value && alumnos.value.length > 0) {
            setTimeout(() => {
                if (alumnosOrdenados.value.length > 0) {
                    alumnoSeleccionadoId.value = alumnosOrdenados.value[0].id
                }
            }, 100)
        }
    } catch (error) {
        console.error("Error:", error)
    } finally {
        cargando.value = false
    }
})

// 👇 LÓGICA DE ORDENAMIENTO (Corregida en Frontend)
const alumnosOrdenados = computed(() => {
    // 1. Mapeamos para crear un campo temporal "nombre_lista" formateado
    let listaProcesada = alumnos.value.map(a => {
        const nombreLimpio = a.nombre_completo.trim()
        const partes = nombreLimpio.split(' ')
        let nombreFormateado = nombreLimpio

        // Lógica: Si tiene 2 palabras (Nombre Apellido) -> "Apellido, Nombre"
        if (partes.length === 2) {
            nombreFormateado = `${partes[1]}, ${partes[0]}`
        }
        // Si tiene 3 o más (Nombre Apellido1 Apellido2) -> "Apellido1 Apellido2, Nombre"
        else if (partes.length >= 3) {
            const apellidos = `${partes[partes.length - 2]} ${partes[partes.length - 1]}`
            const nombre = partes.slice(0, -2).join(' ')
            nombreFormateado = `${apellidos}, ${nombre}`
        }

        return {
            ...a,
            nombre_lista_frontend: nombreFormateado // Guardamos el nombre invertido aquí
        }
    })

    // 2. Ordenamos por ese nuevo campo
    listaProcesada.sort((a, b) => a.nombre_lista_frontend.localeCompare(b.nombre_lista_frontend))

    // 3. Filtramos por buscador
    if (busquedaAlumno.value) {
        const termino = busquedaAlumno.value.toLowerCase()
        listaProcesada = listaProcesada.filter(a =>
            a.nombre_completo.toLowerCase().includes(termino) ||
            a.nombre_lista_frontend.toLowerCase().includes(termino)
        )
    }

    return listaProcesada
})

const seleccionarAlumno = (id) => {
    alumnoSeleccionadoId.value = id
    const el = document.getElementById('detalle-staff')
    if (el) el.scrollIntoView({ behavior: 'smooth' })
}
</script>

<template>
    <div class="contenedor-principal">
        <div v-if="cargando" class="loading">Cargando... ⏳</div>

        <div v-else>

            <div v-if="!esStaff" class="vista-apoderado">
                <h1 class="titulo-centro">🎓 Mis Finanzas</h1>
                <div v-for="alumno in alumnos" :key="alumno.id" class="card-wrapper">
                    <TarjetaAlumno :alumno="alumno" />
                </div>
            </div>

            <div v-else class="vista-staff-layout">

                <aside class="sidebar-nomina">
                    <div class="nomina-header">
                        <h3>📚 Nómina ({{ alumnosOrdenados.length }})</h3>

                        <div class="buscador-wrapper">
                            <input v-model="busquedaAlumno" type="text" placeholder="🔍 Buscar..."
                                class="input-nomina" />
                            <button v-if="busquedaAlumno" @click="busquedaAlumno = ''" class="btn-limpiar"
                                title="Borrar búsqueda">
                                ✕
                            </button>
                        </div>
                    </div>
                    <ul class="lista-nombres">
                        <li v-for="alumno in alumnosOrdenados" :key="alumno.id" @click="seleccionarAlumno(alumno.id)"
                            :class="{ 'activo': alumnoSeleccionadoId === alumno.id }">
                            <span class="avatar-letra">{{ alumno.nombre_completo.charAt(0) }}</span>
                            <span class="nombre-lista">{{ alumno.nombre_completo }}</span>
                            <span v-if="alumno.saldo_a_favor < 0" class="dot-deuda"></span>
                        </li>
                    </ul>
                </aside>

                <main class="contenido-detalle" id="detalle-staff">
                    <div v-if="alumnoSeleccionadoId">
                        <TarjetaAlumno :alumno="alumnos.find(a => a.id === alumnoSeleccionadoId)" />
                    </div>
                </main>
            </div>

        </div>
    </div>
</template>

<style scoped>
/* === ESTILOS GENERALES === */
.contenedor-principal {
    font-family: 'Segoe UI', sans-serif;
    color: #333;
    max-width: 1400px;
    margin: 0 auto;
    padding: 20px;
}

.loading {
    text-align: center;
    padding: 50px;
    font-size: 1.2rem;
    color: #7f8c8d;
}

.titulo-centro {
    text-align: center;
    color: #2c3e50;
    margin-bottom: 30px;
}

/* === ESTILOS APODERADO (VISTA SIMPLE) === */
.vista-apoderado {
    max-width: 1000px;
    margin: 0 auto;
}

.card-wrapper {
    background: white;
    border-radius: 12px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
    margin-bottom: 40px;
    border: 1px solid #eaeaea;

    /* 👇 CLAVE: Permite que el sticky interno funcione */
    overflow: visible;
}

/* === ESTILOS STAFF (VISTA AVANZADA - PC) === */
.vista-staff-layout {
    display: grid;
    grid-template-columns: 280px 1fr;
    gap: 30px;
    /* En PC fijamos la altura para que scrollee solo el contenido */
    height: calc(100vh - 100px);
}

.sidebar-nomina {
    background: white;
    border-radius: 12px;
    border: 1px solid #eaeaea;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    height: 100%;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
}

.nomina-header {
    padding: 15px;
    background: #f8f9fa;
    border-bottom: 1px solid #eee;
}

.nomina-header h3 {
    margin: 0 0 10px 0;
    font-size: 1rem;
    color: #2c3e50;
}

.lista-nombres {
    list-style: none;
    padding: 0;
    margin: 0;
    overflow-y: auto;
    flex-grow: 1;
}

.lista-nombres li {
    padding: 12px 15px;
    border-bottom: 1px solid #f9f9f9;
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 10px;
}

.lista-nombres li:hover {
    background: #f0f8ff;
}

.lista-nombres li.activo {
    background: #e3f2fd;
    border-left: 4px solid #3498db;
}

.avatar-letra {
    background: #bdc3c7;
    color: white;
    width: 24px;
    height: 24px;
    border-radius: 50%;
    display: flex;
    justify-content: center;
    align-items: center;
    font-size: 0.8rem;
    font-weight: bold;
}

.lista-nombres li.activo .avatar-letra {
    background: #3498db;
}

.nombre-lista {
    font-size: 0.9rem;
    color: #34495e;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.dot-deuda {
    width: 8px;
    height: 8px;
    background: #e74c3c;
    border-radius: 50%;
    margin-left: auto;
}

/* Contenedor de la derecha (Detalle) */
.contenido-detalle {
    background: white;
    border-radius: 12px;
    border: 1px solid #eaeaea;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);

    /* En PC tiene scroll propio */
    overflow-y: auto;

    /* Freno para links directos */
    scroll-margin-top: 90px;
}

/* === RESPONSIVE (MÓVIL) - AQUÍ ESTÁ EL ARREGLO ✅ === */
@media (max-width: 900px) {
    .vista-staff-layout {
        display: flex;
        /* Cambiamos Grid por Flex para mejor control */
        flex-direction: column;
        height: auto;
        /* Quitamos la altura fija */
        gap: 15px;
    }

    .sidebar-nomina {
        height: auto;
        max-height: 250px;
        /* Limitamos la altura de la lista */
        margin-bottom: 0;
        border-bottom: 2px solid #3498db;
        /* Separador visual bonito */
    }

    /* 👇 ESTO FALTABA: ROMPEMOS LA JAULA DEL SCROLL */
    .contenido-detalle {
        overflow: visible !important;
        /* Permite que el Sticky se pegue a la ventana */
        height: auto !important;
        /* Crece con el contenido */
        min-height: 500px;
        border: none;
        box-shadow: none;
    }
}

/* === ESTILOS BUSCADOR CON X === */
.buscador-wrapper {
    position: relative;
    width: 100%;
}

.input-nomina {
    width: 100%;
    padding: 8px 30px 8px 10px;
    /* Espacio para la X */
    border: 1px solid #ddd;
    border-radius: 6px;
    box-sizing: border-box;
}

.btn-limpiar {
    position: absolute;
    right: 8px;
    top: 50%;
    transform: translateY(-50%);
    background: none;
    border: none;
    color: #95a5a6;
    font-weight: bold;
    cursor: pointer;
    font-size: 0.9rem;
    padding: 0;
}

.btn-limpiar:hover {
    color: #e74c3c;
}
</style>