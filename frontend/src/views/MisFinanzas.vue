<script setup>
import { ref, onMounted, computed } from 'vue'
import api from '../axios'

const alumnos = ref([])
const cargando = ref(true)
const esStaff = ref(false)

// Variables de UI
const busquedaAlumno = ref('')
const alumnoSeleccionadoId = ref(null)

onMounted(async () => {
    try {
        // 1. Verificamos Rol
        const resUser = await api.get('quien-soy/')
        esStaff.value = resUser.data.es_staff || resUser.data.es_admin

        // 2. Cargamos Alumnos (El backend envía todos al Staff, o solo los pupilos al Apoderado)
        const resAlumnos = await api.get('mis-alumnos/')
        alumnos.value = resAlumnos.data

        // 3. Seleccionamos el primer alumno por defecto automáticamente (para todos)
        if (alumnos.value.length > 0) {
            setTimeout(() => {
                if (alumnosOrdenados.value.length > 0) {
                    alumnoSeleccionadoId.value = alumnosOrdenados.value[0].id
                }
            }, 100)
        }
    } catch (error) {
        console.error("Error cargando finanzas:", error)
    } finally {
        cargando.value = false
    }
})

// Ordenamiento y Buscador
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

    // Ordenar alfabéticamente
    listaProcesada.sort((a, b) => a.nombre_lista_frontend.localeCompare(b.nombre_lista_frontend))

    // Filtro de búsqueda (útil para el staff)
    if (busquedaAlumno.value) {
        const termino = busquedaAlumno.value.toLowerCase()
        listaProcesada = listaProcesada.filter(a =>
            a.nombre_completo.toLowerCase().includes(termino) ||
            a.nombre_lista_frontend.toLowerCase().includes(termino)
        )
    }
    return listaProcesada
})

// Alumno activo para llenar las columnas 2 y 3
const alumnoActivo = computed(() => {
    return alumnos.value.find(a => a.id === alumnoSeleccionadoId.value) || null
})

// Cálculos matemáticos de la vista
const totalTransferencias = computed(() => {
    if (!alumnoActivo.value || !alumnoActivo.value.abonos) return 0
    return alumnoActivo.value.abonos.reduce((sum, abono) => sum + parseFloat(abono.monto || 0), 0)
})

const seleccionarAlumno = (id) => {
    alumnoSeleccionadoId.value = id
}

const formatearDinero = (monto) => {
    return new Intl.NumberFormat('es-CL', { style: 'currency', currency: 'CLP' }).format(monto || 0)
}

const formatearFecha = (fechaString) => {
    if (!fechaString) return '---'
    const partes = fechaString.split('-') // Asume YYYY-MM-DD
    if (partes.length === 3) return `${partes[2]}/${partes[1]}/${partes[0]}`
    return fechaString
}
</script>

<template>
    <div class="contenedor-principal">
        <div v-if="cargando" class="loading">Cargando Bóveda... 🏦</div>

        <div v-else class="contenido-finanzas">
            <h1 class="titulo-pagina">🎓 Estado de Cuentas</h1>

            <div class="tarjeta-banco">
                <div class="header-banco">
                    <h3>🏦 Datos para realizar transferencias</h3>
                    <small>Recuerda enviar tu comprobante a la tesorería para que sea validado.</small>
                </div>
                <div class="datos-grid">
                    <div class="dato-item"><small>Banco</small><strong>BancoEstado</strong></div>
                    <div class="dato-item"><small>Tipo de Cuenta</small><strong>Cuenta RUT</strong></div>
                    <div class="dato-item"><small>N° Cuenta</small><strong>12.345.678-9</strong></div>
                    <div class="dato-item"><small>Nombre</small><strong>Tesorería Curso 8B</strong></div>
                    <div class="dato-item"><small>RUT</small><strong>12.345.678-9</strong></div>
                    <div class="dato-item"><small>Correo</small><strong>tesoreria8b@colegio.cl</strong></div>
                </div>
            </div>

            <div class="layout-3-columnas">

                <aside class="columna columna-lista">
                    <div class="encabezado-col">
                        <h3>👥 {{ esStaff ? 'Curso (' + alumnosOrdenados.length + ')' : 'Mis Pupilos' }}</h3>
                    </div>

                    <div v-if="esStaff" class="buscador-wrapper">
                        <input v-model="busquedaAlumno" type="text" placeholder="🔍 Buscar alumno..."
                            class="input-busqueda" />
                    </div>

                    <ul class="lista-nombres">
                        <li v-for="alumno in alumnosOrdenados" :key="alumno.id" @click="seleccionarAlumno(alumno.id)"
                            :class="{ 'activo': alumnoSeleccionadoId === alumno.id }">
                            <span class="avatar-letra">{{ alumno.nombre_completo.charAt(0) }}</span>
                            <span class="nombre-lista">
                                <span v-if="esStaff" style="color:#7f8c8d; font-size: 0.8em; margin-right: 5px;">{{
                                    alumno.numero_lista }}.</span>
                                {{ alumno.nombre_completo }}
                            </span>
                        </li>
                    </ul>
                </aside>

                <section class="columna columna-datos">
                    <div class="encabezado-col color-transferencias">
                        <h3>💸 Transferencias Realizadas</h3>
                    </div>

                    <div class="contenedor-tabla" v-if="alumnoActivo">
                        <table class="tabla-compacta" v-if="alumnoActivo.abonos && alumnoActivo.abonos.length > 0">
                            <thead>
                                <tr>
                                    <th>Fecha</th>
                                    <th>Detalle</th>
                                    <th style="text-align: right;">Monto</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr v-for="abono in alumnoActivo.abonos" :key="abono.id">
                                    <td class="texto-menor">{{ formatearFecha(abono.fecha_transferencia) }}</td>
                                    <td class="texto-menor">{{ abono.comprobante || 'Depósito' }}</td>
                                    <td style="text-align: right; font-weight: bold; color: #27ae60;">
                                        +{{ formatearDinero(abono.monto) }}
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                        <p v-else class="hint-vacio">No hay transferencias registradas.</p>
                    </div>

                    <div class="pie-columna" v-if="alumnoActivo">
                        <span>Total Transferido:</span>
                        <strong style="color: #27ae60; font-size: 1.1em;">{{ formatearDinero(totalTransferencias)
                            }}</strong>
                    </div>
                </section>

                <section class="columna columna-datos">
                    <div class="encabezado-col color-cobros">
                        <h3>📋 Cuotas y Cobros</h3>
                    </div>

                    <div class="contenedor-tabla" v-if="alumnoActivo">
                        <table class="tabla-compacta" v-if="alumnoActivo.cargos && alumnoActivo.cargos.length > 0">
                            <thead>
                                <tr>
                                    <th>Concepto</th>
                                    <th>Vence</th>
                                    <th style="text-align: right;">Estado</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr v-for="cargo in alumnoActivo.cargos" :key="cargo.id">
                                    <td>
                                        <strong>{{ cargo.concepto_nombre }}</strong><br>
                                        <span class="texto-menor">{{ formatearDinero(cargo.monto_total) }}</span>
                                    </td>
                                    <td class="texto-menor">{{ formatearFecha(cargo.fecha_vencimiento ||
                                        cargo.concepto_fecha_vencimiento) }}</td>
                                    <td style="text-align: right;">
                                        <span class="badge-estado-mini" :class="cargo.estado">{{ cargo.estado }}</span>
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                        <p v-else class="hint-vacio">No hay deudas registradas.</p>
                    </div>
                </section>

            </div>
        </div>
    </div>
</template>

<style scoped>
.contenedor-principal {
    font-family: 'Segoe UI', sans-serif;
    color: #333;
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
}

.loading {
    text-align: center;
    padding: 50px;
    font-size: 1.2rem;
    color: #7f8c8d;
}

.titulo-pagina {
    text-align: center;
    color: #2c3e50;
    margin-bottom: 25px;
    font-size: 1.8rem;
}

/* === TARJETA BANCO === */
.tarjeta-banco {
    background: #f8fbff;
    border: 1px solid #cce5ff;
    border-radius: 8px;
    padding: 15px 20px;
    margin-bottom: 25px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.03);
}

.header-banco h3 {
    margin: 0 0 5px 0;
    color: #004085;
}

.header-banco small {
    color: #666;
    display: block;
    margin-bottom: 10px;
}

.datos-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 10px;
    font-size: 0.9em;
    background: white;
    padding: 10px;
    border-radius: 6px;
    border: 1px dashed #b8daff;
}

/* === LAYOUT 3 COLUMNAS === */
.layout-3-columnas {
    display: grid;
    grid-template-columns: 260px 1fr 1fr;
    gap: 20px;
    align-items: start;
}

.columna {
    background: white;
    border-radius: 10px;
    border: 1px solid #eaeaea;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.04);
    display: flex;
    flex-direction: column;
    overflow: hidden;
    height: 100%;
}

.encabezado-col {
    padding: 12px 15px;
    background: #f8f9fa;
    border-bottom: 1px solid #eee;
}

.encabezado-col h3 {
    margin: 0;
    font-size: 1.1em;
    color: #2c3e50;
}

.color-transferencias {
    border-top: 4px solid #27ae60;
}

.color-cobros {
    border-top: 4px solid #f39c12;
}

/* === COLUMNA 1: LISTA === */
.buscador-wrapper {
    padding: 10px;
    border-bottom: 1px solid #f0f0f0;
}

.input-busqueda {
    width: 100%;
    padding: 8px;
    border: 1px solid #ddd;
    border-radius: 4px;
    box-sizing: border-box;
    font-size: 0.9em;
}

.lista-nombres {
    list-style: none;
    padding: 0;
    margin: 0;
    max-height: 400px;
    /* Evita que crezca infinito */
    overflow-y: auto;
}

.lista-nombres li {
    padding: 10px 15px;
    border-bottom: 1px solid #f9f9f9;
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 10px;
    transition: background 0.2s;
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
    width: 26px;
    height: 26px;
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
    font-size: 0.9em;
    color: #34495e;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

/* === COLUMNAS 2 Y 3: TABLAS COMPACTAS === */
.contenedor-tabla {
    flex-grow: 1;
    max-height: 400px;
    overflow-y: auto;
    padding: 0;
}

.tabla-compacta {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.85em;
}

.tabla-compacta th {
    background: #fafafa;
    color: #7f8c8d;
    padding: 8px 12px;
    text-align: left;
    font-weight: 600;
    position: sticky;
    top: 0;
    z-index: 1;
    border-bottom: 2px solid #eee;
}

.tabla-compacta td {
    padding: 10px 12px;
    border-bottom: 1px solid #f5f5f5;
    vertical-align: middle;
}

.tabla-compacta tr:last-child td {
    border-bottom: none;
}

.tabla-compacta tr:hover {
    background-color: #fafafa;
}

.texto-menor {
    font-size: 0.95em;
    color: #555;
}

.badge-estado-mini {
    padding: 3px 6px;
    border-radius: 4px;
    font-size: 0.75em;
    font-weight: bold;
    color: white;
}

.badge-estado-mini.PENDIENTE {
    background: #e74c3c;
}

.badge-estado-mini.PAGADO {
    background: #2ecc71;
}

.hint-vacio {
    text-align: center;
    color: #95a5a6;
    padding: 20px;
    font-style: italic;
    font-size: 0.9em;
}

.pie-columna {
    background: #f8fbff;
    border-top: 1px solid #eee;
    padding: 12px 15px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 0.95em;
}

/* === RESPONSIVO === */
@media (max-width: 900px) {
    .layout-3-columnas {
        grid-template-columns: 1fr;
        /* Todo en una columna hacia abajo */
        gap: 15px;
    }

    .lista-nombres {
        max-height: 200px;
    }

    /* Menos alto en celular para dejar ver lo demás */
    .contenedor-tabla {
        max-height: 300px;
    }
}
</style>