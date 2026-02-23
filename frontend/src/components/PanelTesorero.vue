<script setup>
import { ref, onMounted } from 'vue'
import api from '../axios' // Usamos tu configuración con Token

// === ESTADO ===
const alumnos = ref([])
const alumnoSeleccionado = ref(null)

// Selección Manual (Mesa de trabajo)
const abonoSeleccionado = ref(null)
const cargoSeleccionado = ref(null)
const montoAImputar = ref(0)

// Generador Masivo
const conceptos = ref([])
const conceptoSeleccionado = ref(null)
const cursoObjetivo = ref('')
const procesandoMasivo = ref(false)

// === NUEVO: INGRESO RÁPIDO DE ABONOS ===
const mostrandoFormularioAbono = ref(false)
const nuevoAbono = ref({
    monto: '',
    fecha: new Date().toISOString().split('T')[0], // Hoy
    comprobante: ''
})

// === LISTA DE CURSOS ===
const listaCursos = [
    { cod: '8B', nombre: '8° Básico' },
    { cod: '1M', nombre: '1° Medio' },
    { cod: '2M', nombre: '2° Medio' },
    { cod: '3M', nombre: '3° Medio' },
    { cod: '4M', nombre: '4° Medio' },
]

// === CARGA INICIAL ===
const cargarDatosGlobales = async () => {
    try {
        const resAlumnos = await api.get('mis-alumnos/')
        alumnos.value = resAlumnos.data
        const resConceptos = await api.get('conceptos/')
        conceptos.value = resConceptos.data
    } catch (error) {
        console.error("Error cargando datos:", error)
    }
}

onMounted(() => {
    cargarDatosGlobales()
})

// === UTILIDAD: RECARGAR SOLO AL ALUMNO ACTUAL ===
// Esto evita tener que recargar toda la página (F5) cada vez que hacemos algo
const recargarAlumnoActual = async () => {
    if (!alumnoSeleccionado.value) return
    try {
        // Volvemos a pedir la lista (lo ideal sería pedir solo 1 alumno, pero esto funciona rápido)
        const res = await api.get('mis-alumnos/')
        alumnos.value = res.data

        // Buscamos al alumno que teníamos seleccionado para actualizar sus datos
        const actualizado = alumnos.value.find(a => a.id === alumnoSeleccionado.value.id)
        alumnoSeleccionado.value = actualizado

        // Limpiamos selecciones para evitar errores
        abonoSeleccionado.value = null
        cargoSeleccionado.value = null
        montoAImputar.value = 0
    } catch (e) {
        console.error(e)
    }
}

// === 1. FUNCIÓN: GENERAR COBRO MASIVO ===
const ejecutarCobroMasivo = async () => {
    if (!conceptoSeleccionado.value || !cursoObjetivo.value) {
        return alert("Por favor selecciona un Concepto y un Curso.")
    }
    if (!confirm(`¿Generar deuda a TODO el curso ${cursoObjetivo.value}?`)) return

    procesandoMasivo.value = true
    try {
        const url = `conceptos/${conceptoSeleccionado.value}/generar_masivo/`
        const respuesta = await api.post(url, { curso: cursoObjetivo.value })

        alert(`Reporte:\n✅ Creados: ${respuesta.data.cargos_creados}\n⏭️ Omitidos: ${respuesta.data.cargos_ya_existian}`)
        cargarDatosGlobales() // Recargar todo

    } catch (error) {
        console.error(error)
        alert("Error al generar los cobros.")
    } finally {
        procesandoMasivo.value = false
    }
}

// === 2. FUNCIÓN: NUEVO ABONO (INGRESO DE PLATA) ===
const guardarAbono = async () => {
    if (!alumnoSeleccionado.value) return alert("Selecciona un alumno")
    if (!nuevoAbono.value.monto || nuevoAbono.value.monto <= 0) return alert("Monto inválido")

    try {
        await api.post('pagos/', {
            alumno: alumnoSeleccionado.value.id,
            monto_recibido: nuevoAbono.value.monto,
            saldo_disponible: nuevoAbono.value.monto,
            fecha_pago: nuevoAbono.value.fecha,
            comprobante: nuevoAbono.value.comprobante
        })

        alert("¡Dinero ingresado! 💰")

        // Limpiar y recargar
        nuevoAbono.value = { monto: '', fecha: new Date().toISOString().split('T')[0], comprobante: '' }
        mostrandoFormularioAbono.value = false
        await recargarAlumnoActual()

    } catch (error) {
        console.error(error)
        alert("Error al guardar abono")
    }
}

// === 3. FUNCIÓN: ELIMINAR CARGO (BORRAR DEUDA) ===
const eliminarCargo = async (cargoId) => {
    if (!confirm("¿Borrar esta deuda? No se puede deshacer.")) return

    try {
        await api.delete(`cargos/${cargoId}/`) // Usamos la nueva vista CargoViewSet
        alert("Deuda eliminada 🗑️")
        await recargarAlumnoActual()
    } catch (error) {
        console.error(error)
        alert("No se puede borrar. Probablemente ya tiene pagos asociados.")
    }
}

// === 4. FUNCIÓN: IMPUTAR PAGO (ASIGNAR) ===
const calcularMaximoPosible = () => {
    if (abonoSeleccionado.value && cargoSeleccionado.value) {
        const saldoAbono = abonoSeleccionado.value.saldo_disponible
        const faltaDeuda = cargoSeleccionado.value.monto_total - cargoSeleccionado.value.monto_pagado
        montoAImputar.value = Math.min(saldoAbono, faltaDeuda)
    }
}

const procesarAsignacion = async () => {
    if (montoAImputar.value <= 0) return alert("El monto debe ser mayor a 0")
    try {
        await api.post('asignaciones/', {
            abono: abonoSeleccionado.value.id,
            cargo: cargoSeleccionado.value.id,
            monto_asignado: montoAImputar.value
        })
        alert("¡Asignación Exitosa! ✅")
        await recargarAlumnoActual()
    } catch (error) {
        console.error(error)
        alert("Error al asignar")
    }
}
</script>

<template>
    <div class="panel-tesorero">
        <h1>🛡️ Panel de Tesorería</h1>

        <div class="panel-masivo">
            <h3>⚡ Generar Cobros Masivos</h3>
            <div class="controles-masivos">
                <div class="campo">
                    <label>¿Qué cobrar?</label>
                    <select v-model="conceptoSeleccionado">
                        <option :value="null">-- Seleccionar Concepto --</option>
                        <option v-for="c in conceptos" :key="c.id" :value="c.id">
                            {{ c.nombre }} (${{ c.monto_estandar }})
                        </option>
                    </select>
                </div>

                <div class="campo">
                    <label>¿A quiénes?</label>
                    <select v-model="cursoObjetivo">
                        <option value="">-- Seleccionar Curso --</option>
                        <option v-for="curso in listaCursos" :key="curso.cod" :value="curso.cod">
                            {{ curso.nombre }}
                        </option>
                    </select>
                </div>

                <button @click="ejecutarCobroMasivo" class="btn-masivo" :disabled="procesandoMasivo">
                    {{ procesandoMasivo ? 'Procesando...' : '🚀 Generar Deuda' }}
                </button>
            </div>
        </div>

        <div class="selector">
            <label>Seleccionar Alumno para trabajar:</label>
            <select v-model="alumnoSeleccionado">
                <option :value="null">-- Elegir Alumno --</option>
                <option v-for="al in alumnos" :key="al.id" :value="al">
                    {{ al.nombre_completo }} (Saldo a favor: ${{ al.saldo_a_favor }})
                </option>
            </select>
        </div>

        <div v-if="alumnoSeleccionado" class="mesa-trabajo">

            <div class="columna fondos">
                <div class="titulo-con-accion">
                    <h3>💰 Fondos</h3>
                    <button @click="mostrandoFormularioAbono = !mostrandoFormularioAbono" class="btn-mini">
                        {{ mostrandoFormularioAbono ? '❌' : '➕ Ingreso' }}
                    </button>
                </div>

                <div v-if="mostrandoFormularioAbono" class="form-rapido">
                    <input type="number" v-model="nuevoAbono.monto" placeholder="Monto $" />
                    <input type="text" v-model="nuevoAbono.comprobante" placeholder="N° Comprobante" />
                    <input type="date" v-model="nuevoAbono.fecha" />
                    <button @click="guardarAbono" class="btn-guardar-mini">Guardar Ingreso</button>
                </div>

                <p class="hint" v-if="!mostrandoFormularioAbono">Selecciona billete disponible:</p>

                <div v-for="abono in alumnoSeleccionado.abonos" :key="abono.id" class="item-lista"
                    :class="{ 'activo': abonoSeleccionado === abono, 'disabled': abono.saldo_disponible === 0 }"
                    @click="abono.saldo_disponible > 0 ? (abonoSeleccionado = abono, calcularMaximoPosible()) : null">
                    <div class="flex-row">
                        <span>📅 {{ abono.fecha_pago }}</span>
                        <strong style="color: green">${{ abono.saldo_disponible }}</strong>
                    </div>
                    <small>Original: ${{ abono.monto_recibido }} | {{ abono.comprobante }}</small>
                </div>
            </div>

            <div class="columna accion">
                <div v-if="abonoSeleccionado && cargoSeleccionado" class="caja-imputar">
                    <h4>🔗 Asignar Pago</h4>
                    <p style="font-size: 0.9em;">
                        De: <strong>${{ abonoSeleccionado.saldo_disponible }}</strong> (Disponible)<br>
                        A: <strong>{{ cargoSeleccionado.concepto_nombre }}</strong>
                    </p>

                    <label>Monto a usar:</label>
                    <input type="number" v-model="montoAImputar">

                    <button @click="procesarAsignacion" class="btn-guardar">CONFIRMAR</button>
                </div>
                <div v-else class="esperando">
                    <p>👈 1. Selecciona un Abono</p>
                    <p>👉 2. Selecciona una Deuda</p>
                </div>
            </div>

            <div class="columna deudas">
                <h3>📋 Deudas del Alumno</h3>

                <div v-if="alumnoSeleccionado.cargos && alumnoSeleccionado.cargos.length > 0">
                    <table class="tabla-deudas">
                        <thead>
                            <tr>
                                <th>Concepto</th>
                                <th>Monto</th>
                                <th>Acción</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr v-for="cargo in alumnoSeleccionado.cargos" :key="cargo.id"
                                :class="{ 'fila-activa': cargoSeleccionado === cargo }"
                                @click="cargo.estado !== 'PAGADO' ? (cargoSeleccionado = cargo, calcularMaximoPosible()) : null"
                                style="cursor: pointer;">

                                <td>
                                    {{ cargo.concepto_nombre }}<br>
                                    <small style="color: #777;">Vence: {{ cargo.fecha_vencimiento || '-' }}</small>
                                </td>

                                <td :class="cargo.estado === 'PAGADO' ? 'texto-verde' : 'texto-rojo'">
                                    ${{ cargo.monto_total }}
                                    <div v-if="cargo.monto_pagado > 0" style="font-size:0.8em; color:orange">
                                        (Abo: ${{ cargo.monto_pagado }})
                                    </div>
                                    <span class="badge-estado" :class="cargo.estado">{{ cargo.estado }}</span>
                                </td>

                                <td style="text-align: center;">
                                    <button v-if="cargo.estado !== 'PAGADO'" @click.stop="eliminarCargo(cargo.id)"
                                        class="btn-eliminar" title="Borrar Deuda">
                                        🗑️
                                    </button>
                                    <span v-else>✅</span>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
                <p v-else class="hint">No tiene deudas registradas.</p>
            </div>

        </div>
    </div>
</template>

<style scoped>
/* ESTRUCTURA GENERAL */
.panel-tesorero {
    padding: 20px;
    background-color: #fff;
    border-radius: 8px;
    color: #333;
    max-width: 1200px;
    margin: 0 auto;
}

/* GENERADOR MASIVO */
.panel-masivo {
    background-color: #fff8e1;
    /* Amarillo muy suave */
    border: 1px solid #ffe082;
    padding: 20px;
    border-radius: 8px;
    margin-bottom: 30px;
}

.panel-masivo h3 {
    margin-top: 0;
    color: #f57c00;
}

.controles-masivos {
    display: flex;
    gap: 20px;
    align-items: flex-end;
    flex-wrap: wrap;
}

.campo {
    display: flex;
    flex-direction: column;
}

.campo label {
    font-weight: bold;
    margin-bottom: 5px;
    font-size: 0.9em;
}

.campo select {
    padding: 8px;
    border: 1px solid #ccc;
    border-radius: 4px;
    min-width: 200px;
}

.btn-masivo {
    background-color: #e65100;
    color: white;
    border: none;
    padding: 0 20px;
    height: 38px;
    /* Altura fija para alinear con inputs */
    border-radius: 4px;
    font-weight: bold;
    cursor: pointer;
    white-space: nowrap;
}

.btn-masivo:hover {
    background-color: #ff6d00;
}

.btn-masivo:disabled {
    background-color: #bdbdbd;
    cursor: not-allowed;
}


/* SELECCIÓN DE ALUMNO */
.selector {
    margin-bottom: 20px;
    padding: 10px;
    background: #f5f5f5;
    border-radius: 8px;
}

.selector select {
    padding: 8px;
    width: 100%;
    max-width: 400px;
    font-size: 1em;
}


/* MESA DE TRABAJO (3 COLUMNAS) */
.mesa-trabajo {
    display: flex;
    gap: 20px;
    flex-wrap: wrap;
}

.columna {
    padding: 15px;
    border-radius: 8px;
    background: #f9f9f9;
    border: 1px solid #eee;
}

.columna.fondos {
    flex: 1;
    min-width: 250px;
}

.columna.accion {
    flex: 0.5;
    min-width: 200px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: transparent;
    border: none;
}

.columna.deudas {
    flex: 1.2;
    min-width: 300px;
}

/* Un poco más ancha para la tabla */


/* COLUMNA IZQUIERDA (FONDOS) */
.titulo-con-accion {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;
}

.btn-mini {
    background: #3498db;
    color: white;
    border: none;
    padding: 5px 10px;
    border-radius: 4px;
    cursor: pointer;
    font-size: 0.8em;
}

.form-rapido {
    background: #e3f2fd;
    padding: 10px;
    border-radius: 4px;
    margin-bottom: 15px;
    display: flex;
    flex-direction: column;
    gap: 8px;
    border: 1px solid #90caf9;
}

.form-rapido input {
    padding: 6px;
    border: 1px solid #ccc;
    border-radius: 3px;
}

.btn-guardar-mini {
    background: #27ae60;
    color: white;
    border: none;
    padding: 8px;
    border-radius: 3px;
    cursor: pointer;
    font-weight: bold;
}

.item-lista {
    background: white;
    padding: 10px;
    margin-bottom: 8px;
    border-radius: 6px;
    cursor: pointer;
    border: 2px solid transparent;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.item-lista:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.item-lista.activo {
    border-color: #3498db;
    background-color: #f0faff;
}

.item-lista.disabled {
    opacity: 0.5;
    cursor: default;
    background: #eee;
}

.flex-row {
    display: flex;
    justify-content: space-between;
}


/* COLUMNA CENTRAL (ACCIÓN) */
.caja-imputar {
    background: #2c3e50;
    color: white;
    padding: 20px;
    border-radius: 8px;
    text-align: center;
    width: 100%;
    box-shadow: 0 4px 10px rgba(0, 0, 0, 0.2);
}

.caja-imputar input {
    padding: 10px;
    width: 80%;
    margin: 15px 0;
    border: none;
    border-radius: 4px;
    font-size: 1.2em;
    text-align: center;
    font-weight: bold;
    color: #333;
}

.btn-guardar {
    background: #27ae60;
    color: white;
    border: none;
    padding: 12px;
    border-radius: 4px;
    font-weight: bold;
    cursor: pointer;
    width: 100%;
    font-size: 1.1em;
}

.btn-guardar:hover {
    background: #219150;
}

.esperando {
    text-align: center;
    color: #aaa;
    font-style: italic;
}


/* COLUMNA DERECHA (TABLA DEUDAS) */
.tabla-deudas {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.9em;
    background: white;
}

.tabla-deudas th {
    background: #e0e0e0;
    padding: 8px;
    text-align: left;
    color: #555;
}

.tabla-deudas td {
    padding: 8px;
    border-bottom: 1px solid #eee;
    vertical-align: middle;
}

.tabla-deudas tr:hover {
    background-color: #f5f5f5;
}

.fila-activa {
    background-color: #fff3e0 !important;
    border-left: 4px solid #f39c12;
}

.texto-rojo {
    color: #c0392b;
    font-weight: bold;
}

.texto-verde {
    color: #27ae60;
    font-weight: bold;
}

.badge-estado {
    display: inline-block;
    padding: 2px 6px;
    border-radius: 4px;
    font-size: 0.7em;
    margin-top: 2px;
    color: white;
}

.badge-estado.PENDIENTE {
    background: #e74c3c;
}

.badge-estado.PARCIAL {
    background: #f39c12;
}

.badge-estado.PAGADO {
    background: #2ecc71;
}

.btn-eliminar {
    background: #ffebee;
    border: 1px solid #ffcdd2;
    color: #c62828;
    border-radius: 4px;
    cursor: pointer;
    padding: 4px 8px;
    transition: 0.2s;
}

.btn-eliminar:hover {
    background: #d32f2f;
    color: white;
}
</style>