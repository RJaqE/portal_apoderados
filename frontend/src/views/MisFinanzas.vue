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

        // 2. Cargamos Alumnos
        const resAlumnos = await api.get('mis-alumnos/')
        alumnos.value = resAlumnos.data

        // 3. Seleccionamos el primer alumno por defecto automáticamente
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

// Ordenamiento por Número de Lista
const alumnosOrdenados = computed(() => {
    let listaProcesada = [...alumnos.value]

    listaProcesada.sort((a, b) => {
        const numA = a.numero_lista || 999;
        const numB = b.numero_lista || 999;
        return numA - numB;
    })

    if (busquedaAlumno.value) {
        const termino = busquedaAlumno.value.toLowerCase()
        listaProcesada = listaProcesada.filter(a =>
            a.nombre_completo.toLowerCase().includes(termino) ||
            (a.numero_lista && a.numero_lista.toString() === termino)
        )
    }

    return listaProcesada
})

// Alumno activo
const alumnoActivo = computed(() => {
    return alumnos.value.find(a => a.id === alumnoSeleccionadoId.value) || null
})

// === ORDENAMIENTO DE COBROS (PAGADOS ARRIBA, PENDIENTES ABAJO) ===
const cargosOrdenados = computed(() => {
    if (!alumnoActivo.value || !alumnoActivo.value.cargos) return []
    // Clonamos para no mutar el original
    return [...alumnoActivo.value.cargos].sort((a, b) => {
        if (a.estado === 'PAGADO' && b.estado !== 'PAGADO') return -1;
        if (a.estado !== 'PAGADO' && b.estado === 'PAGADO') return 1;
        return 0;
    })
})


// === CÁLCULOS MATEMÁTICOS PARA LA VISTA ===

// 1. Total Transferido (Suma de todos los abonos)
const totalTransferencias = computed(() => {
    if (!alumnoActivo.value || !alumnoActivo.value.abonos) return 0
    return alumnoActivo.value.abonos.reduce((sum, abono) => sum + parseFloat(abono.monto || 0), 0)
})

// 2. Total de Cobros ya PAGADOS (Para el pie de tabla derecha y la ecuación)
const totalCargosPagados = computed(() => {
    if (!alumnoActivo.value || !alumnoActivo.value.cargos) return 0
    return alumnoActivo.value.cargos
        .filter(cargo => cargo.estado === 'PAGADO')
        .reduce((sum, cargo) => sum + parseFloat(cargo.monto_total || 0), 0)
})


// Auto-Scroll Inteligente para móviles
const seleccionarAlumno = (id) => {
    alumnoSeleccionadoId.value = id;

    setTimeout(() => {
        if (window.innerWidth <= 900) {
            const zonaDatos = document.getElementById('seccion-datos-alumno');
            if (zonaDatos) {
                const offsetY = zonaDatos.getBoundingClientRect().top + window.scrollY - 10;
                window.scrollTo({ top: offsetY, behavior: 'smooth' });
            }
        }
    }, 50);
}

const formatearDinero = (monto) => {
    return new Intl.NumberFormat('es-CL', { style: 'currency', currency: 'CLP' }).format(monto || 0)
}

const formatearFecha = (fechaString) => {
    if (!fechaString) return '---'
    const partes = fechaString.split('-')
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
                    <div class="dato-item"><small>Banco</small><strong>Banco de Chile</strong></div>
                    <div class="dato-item"><small>Tipo de Cuenta</small><strong>Cuenta Vista</strong></div>
                    <div class="dato-item"><small>N° Cuenta</small><strong>59025105</strong></div>
                    <div class="dato-item"><small>Nombre</small><strong>Ana Fuenzalida</strong></div>
                    <div class="dato-item"><small>RUT</small><strong>13.855.344-2</strong></div>
                    <div class="dato-item"><small>Correo</small><strong>generacion2030.coe@gmail.com</strong></div>
                </div>
            </div>

            <div class="layout-principal">

                <aside class="columna-sidebar">
                    <div class="encabezado-col">
                        <h3>👥 {{ esStaff ? 'Curso (' + alumnosOrdenados.length + ')' : 'Mis Pupilos' }}</h3>
                    </div>

                    <div v-if="esStaff" class="buscador-wrapper">
                        <input v-model="busquedaAlumno" type="text" placeholder="🔍 Buscar nombre o n°..."
                            class="input-busqueda" />
                    </div>

                    <ul class="lista-nombres">
                        <li v-for="alumno in alumnosOrdenados" :key="alumno.id" @click="seleccionarAlumno(alumno.id)"
                            :class="{ 'activo': alumnoSeleccionadoId === alumno.id }">
                            <span class="avatar-letra">{{ alumno.numero_lista || '#' }}</span>
                            <span class="nombre-lista">
                                {{ alumno.nombre_completo }}
                            </span>
                        </li>
                    </ul>
                </aside>

                <div class="area-datos" id="seccion-datos-alumno">

                    <div v-if="alumnoActivo" class="header-sticky-alumno">
                        <div class="perfil-info">
                            <div class="avatar-mini">{{ alumnoActivo.numero_lista || '#' }}</div>
                            <div class="info-sticky">
                                <small>Viendo finanzas de:</small>
                                <span class="nombre-sticky">{{ alumnoActivo.nombre_completo }}</span>
                            </div>
                        </div>

                        <div class="ecuacion-billetera">
                            <span class="formula">
                                Transferencias ({{ formatearDinero(totalTransferencias) }})
                                - Pagado ({{ formatearDinero(totalCargosPagados) }}) =
                            </span>
                            <strong class="resultado-billetera">
                                Billetera: {{ formatearDinero(alumnoActivo.cuenta?.saldo_disponible) }}
                            </strong>
                        </div>
                    </div>

                    <div class="grid-tablas">

                        <section class="columna-datos">
                            <div class="encabezado-col color-transferencias">
                                <h3>💸 Transferencias Realizadas</h3>
                            </div>

                            <div class="contenedor-tabla" v-if="alumnoActivo">
                                <table class="tabla-compacta"
                                    v-if="alumnoActivo.abonos && alumnoActivo.abonos.length > 0">
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
                                <strong style="color: #27ae60; font-size: 1.1em;">{{
                                    formatearDinero(totalTransferencias) }}</strong>
                            </div>
                        </section>

                        <section class="columna-datos">
                            <div class="encabezado-col color-cobros">
                                <h3>📋 Cuotas y Cobros</h3>
                            </div>

                            <div class="contenedor-tabla" v-if="alumnoActivo">
                                <table class="tabla-compacta" v-if="cargosOrdenados.length > 0">
                                    <thead>
                                        <tr>
                                            <th>Concepto</th>
                                            <th>Vence</th>
                                            <th style="text-align: right;">Estado</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        <tr v-for="cargo in cargosOrdenados" :key="cargo.id">
                                            <td>
                                                <strong>{{ cargo.concepto_nombre }}</strong><br>
                                                <span class="texto-menor"
                                                    :style="{ color: cargo.estado === 'PAGADO' ? '#27ae60' : '#7f8c8d' }">
                                                    {{ formatearDinero(cargo.monto_total) }}
                                                </span>
                                            </td>
                                            <td class="texto-menor">{{ formatearFecha(cargo.fecha_vencimiento ||
                                                cargo.concepto_fecha_vencimiento) }}</td>
                                            <td style="text-align: right;">
                                                <span class="badge-estado-mini" :class="cargo.estado">{{ cargo.estado
                                                    }}</span>
                                            </td>
                                        </tr>
                                    </tbody>
                                </table>
                                <p v-else class="hint-vacio">No hay deudas registradas.</p>
                            </div>

                            <div class="pie-columna" v-if="alumnoActivo">
                                <span>Total Pagado:</span>
                                <strong style="color: #27ae60; font-size: 1.1em;">{{ formatearDinero(totalCargosPagados)
                                    }}</strong>
                            </div>
                        </section>

                    </div>
                </div>
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
    margin-bottom: 15px;
}

.datos-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
    gap: 15px;
    background: white;
    padding: 15px;
    border-radius: 8px;
    border: 1px dashed #b8daff;
    text-align: center;
}

.dato-item {
    display: flex;
    flex-direction: column;
    gap: 5px;
}

.dato-item small {
    color: #7f8c8d;
    font-size: 0.75em;
    text-transform: uppercase;
    font-weight: 700;
    letter-spacing: 0.5px;
}

.dato-item strong { 
    color: #2c3e50; 
    font-size: 1.05em; 
    word-break: break-all; /* 👈 Obliga a romper palabras largas */
    overflow-wrap: break-word; /* 👈 Soporte para navegadores modernos */
}

/* === LAYOUT === */
.layout-principal {
    display: grid;
    grid-template-columns: 280px 1fr;
    gap: 20px;
    align-items: start;
}

/* === SIDEBAR === */
.columna-sidebar {
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
    max-height: 450px;
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

/* === AREA DATOS & STICKY HEADER === */
.area-datos {
    display: flex;
    flex-direction: column;
    gap: 15px;
}

.header-sticky-alumno {
    position: sticky;
    top: 5px;
    z-index: 10;
    background: #2c3e50;
    color: white;
    padding: 12px 20px;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 15px;
}

.perfil-info {
    display: flex;
    align-items: center;
    gap: 15px;
}

.avatar-mini {
    background: #3498db;
    color: white;
    width: 36px;
    height: 36px;
    border-radius: 50%;
    display: flex;
    justify-content: center;
    align-items: center;
    font-size: 1.1rem;
    font-weight: bold;
    border: 2px solid white;
}

.info-sticky {
    display: flex;
    flex-direction: column;
}

.info-sticky small {
    color: #bdc3c7;
    font-size: 0.75em;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.nombre-sticky {
    font-size: 1.1em;
    font-weight: bold;
    margin-top: 2px;
}

/* 🧮 ECUACIÓN */
.ecuacion-billetera {
    background: rgba(0, 0, 0, 0.2);
    padding: 8px 15px;
    border-radius: 6px;
    text-align: right;
}

.formula {
    font-size: 0.85em;
    color: #bdc3c7;
    display: block;
    margin-bottom: 3px;
}

.resultado-billetera {
    font-size: 1.15em;
    color: #2ecc71;
    letter-spacing: 0.5px;
}

/* === GRILLA TABLAS === */
.grid-tablas {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
}

.columna-datos {
    background: white;
    border-radius: 10px;
    border: 1px solid #eaeaea;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.04);
    display: flex;
    flex-direction: column;
    overflow: hidden;
}

.color-transferencias {
    border-top: 4px solid #27ae60;
}

.color-cobros {
    border-top: 4px solid #f39c12;
}

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

/* 📊 PIE DE COLUMNA */
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
    .layout-principal {
        grid-template-columns: 1fr;
        gap: 15px;
    }

    .grid-tablas {
        grid-template-columns: 1fr;
    }

    .lista-nombres {
        max-height: 250px;
    }

    .header-sticky-alumno {
        top: 10px;
        flex-direction: column;
        align-items: flex-start;
    }

    .ecuacion-billetera {
        text-align: left;
        width: 100%;
        box-sizing: border-box;
    }
}
</style>