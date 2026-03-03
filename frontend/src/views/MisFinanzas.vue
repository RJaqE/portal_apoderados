<script setup>
import { ref, onMounted, computed } from 'vue'
import api from '../axios'
import TarjetaAlumno from '../components/TarjetaAlumno.vue'

const alumnos = ref([])
const cargando = ref(true)
const esStaff = ref(false)

// Variables exclusivas para Staff
const busquedaAlumno = ref('')
const alumnoSeleccionadoId = ref(null)

// 👇 NUEVO: Variable para el Dashboard del Tesorero
const resumen = ref({
    banco_estimado: 0,
    fondo_gira_estudio: 0,
    saldo_flotante_apoderados: 0,
    por_transferir_terceros: 0,
    morosidad_pendiente: 0
})

onMounted(async () => {
    try {
        // 1. Verificamos Rol
        const resUser = await api.get('quien-soy/')
        esStaff.value = resUser.data.es_staff || resUser.data.es_admin

        // 2. Si es Tesorero, cargamos el Dashboard Global
        if (esStaff.value) {
            const resDashboard = await api.get('resumen-tesoreria/')
            resumen.value = resDashboard.data
        }

        // 3. Cargamos Alumnos (El backend ya sabe si mandar todos o solo los pupilos)
        const resAlumnos = await api.get('mis-alumnos/')
        alumnos.value = resAlumnos.data

        // 4. Seleccionamos el primero por defecto (Solo Staff)
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

// Lógica de Ordenamiento y Buscador (¡Intacta, está excelente!)
const alumnosOrdenados = computed(() => {
    let listaProcesada = alumnos.value.map(a => {
        const nombreLimpio = a.nombre_completo.trim()
        const partes = nombreLimpio.split(' ')
        let nombreFormateado = nombreLimpio

        if (partes.length === 2) {
            nombreFormateado = `${partes[1]}, ${partes[0]}`
        } else if (partes.length >= 3) {
            const apellidos = `${partes[partes.length - 2]} ${partes[partes.length - 1]}`
            const nombre = partes.slice(0, -2).join(' ')
            nombreFormateado = `${apellidos}, ${nombre}`
        }
        return { ...a, nombre_lista_frontend: nombreFormateado }
    })

    listaProcesada.sort((a, b) => a.nombre_lista_frontend.localeCompare(b.nombre_lista_frontend))

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

// Utilidad para formatear dinero
const formatearDinero = (monto) => {
    return new Intl.NumberFormat('es-CL', { style: 'currency', currency: 'CLP' }).format(monto || 0)
}
</script>

<template>
    <div class="contenedor-principal">
        <div v-if="cargando" class="loading">Cargando Bóveda... 🏦</div>

        <div v-else>
            <div v-if="!esStaff" class="vista-apoderado">
                <h1 class="titulo-centro">🎓 Mis Finanzas</h1>
                <div v-for="alumno in alumnos" :key="alumno.id" class="card-wrapper">
                    <TarjetaAlumno :alumno="alumno" />
                </div>
            </div>

            <div v-else>
                <div class="header-finanzas">
                    <h2>💰 Panel de Tesorería</h2>
                    <p>Control de Billeteras Virtuales y Fondo de Viaje</p>
                </div>

                <div class="dashboard-grid">
                    <div class="tarjeta-stat principal">
                        <span class="icono">✈️</span>
                        <div class="info">
                            <small>Fondo Gira (Total)</small>
                            <h3>{{ formatearDinero(resumen.fondo_gira_estudio) }}</h3>
                        </div>
                    </div>

                    <div class="tarjeta-stat secundaria">
                        <span class="icono">💳</span>
                        <div class="info">
                            <small>En Banco (Estimado)</small>
                            <h3>{{ formatearDinero(resumen.banco_estimado) }}</h3>
                        </div>
                    </div>

                    <div class="tarjeta-stat flotante">
                        <span class="icono">👛</span>
                        <div class="info">
                            <small>Billeteras (Saldos a Favor)</small>
                            <h3>{{ formatearDinero(resumen.saldo_flotante_apoderados) }}</h3>
                        </div>
                    </div>

                    <div class="tarjeta-stat alerta">
                        <span class="icono">📤</span>
                        <div class="info">
                            <small>Pagar a Terceros (Rifas)</small>
                            <h3>{{ formatearDinero(resumen.por_transferir_terceros) }}</h3>
                        </div>
                    </div>
                </div>

                <hr class="divisor" />

                <div class="vista-staff-layout">
                    <aside class="sidebar-nomina">
                        <div class="nomina-header">
                            <h3>📚 Nómina ({{ alumnosOrdenados.length }})</h3>
                            <div class="buscador-wrapper">
                                <input v-model="busquedaAlumno" type="text" placeholder="🔍 Buscar..."
                                    class="input-nomina" />
                                <button v-if="busquedaAlumno" @click="busquedaAlumno = ''"
                                    class="btn-limpiar">✕</button>
                            </div>
                        </div>
                        <ul class="lista-nombres">
                            <li v-for="alumno in alumnosOrdenados" :key="alumno.id"
                                @click="seleccionarAlumno(alumno.id)"
                                :class="{ 'activo': alumnoSeleccionadoId === alumno.id }">
                                <span class="avatar-letra">{{ alumno.nombre_completo.charAt(0) }}</span>
                                <span class="nombre-lista">{{ alumno.nombre_completo }}</span>
                                <span v-if="alumno.deuda_por_pagar > 0" class="dot-deuda" title="Tiene deudas"></span>
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
    </div>
</template>

<style scoped>
/* === ESTILOS ORIGINALES INTACTOS === */
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
    overflow: visible;
}

.vista-staff-layout {
    display: grid;
    grid-template-columns: 280px 1fr;
    gap: 30px;
    height: calc(100vh - 250px);
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

.contenido-detalle {
    background: white;
    border-radius: 12px;
    border: 1px solid #eaeaea;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
    overflow-y: auto;
    scroll-margin-top: 90px;
}

.buscador-wrapper {
    position: relative;
    width: 100%;
}

.input-nomina {
    width: 100%;
    padding: 8px 30px 8px 10px;
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

/* === NUEVOS ESTILOS PARA EL DASHBOARD === */
.header-finanzas {
    margin-bottom: 20px;
}

.header-finanzas h2 {
    margin: 0;
    font-size: 1.8rem;
    color: #2c3e50;
}

.header-finanzas p {
    margin: 5px 0 0 0;
    color: #7f8c8d;
}

.divisor {
    border: 0;
    height: 1px;
    background: #ecf0f1;
    margin: 25px 0;
}

.dashboard-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 15px;
}

.tarjeta-stat {
    background: white;
    padding: 15px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    gap: 15px;
    border-left: 5px solid #bdc3c7;
    border-right: 1px solid #eee;
    border-top: 1px solid #eee;
    border-bottom: 1px solid #eee;
}

.tarjeta-stat.principal {
    border-color: #3498db;
}

.tarjeta-stat.secundaria {
    border-color: #2ecc71;
}

.tarjeta-stat.flotante {
    border-color: #9b59b6;
}

.tarjeta-stat.alerta {
    border-color: #f39c12;
}

.tarjeta-stat .icono {
    font-size: 2rem;
}

.tarjeta-stat .info small {
    display: block;
    color: #7f8c8d;
    font-weight: bold;
    font-size: 0.75rem;
    text-transform: uppercase;
}

.tarjeta-stat .info h3 {
    margin: 5px 0 0 0;
    color: #2c3e50;
    font-size: 1.3rem;
}

@media (max-width: 900px) {
    .vista-staff-layout {
        display: flex;
        flex-direction: column;
        height: auto;
        gap: 15px;
    }

    .sidebar-nomina {
        height: auto;
        max-height: 250px;
        margin-bottom: 0;
        border-bottom: 2px solid #3498db;
    }

    .contenido-detalle {
        overflow: visible !important;
        height: auto !important;
        min-height: 500px;
        border: none;
        box-shadow: none;
    }
}
</style>