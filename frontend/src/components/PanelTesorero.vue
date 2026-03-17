<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import api from '../axios'

// === ESTADO GLOBAL ===
const alumnos = ref([])
const alumnoSeleccionado = ref(null)
const cargoSeleccionado = ref(null)
const historialTransacciones = ref([])

// === 1. SELECCIÓN MASIVA DE ALUMNOS (Compartido) ===
const alumnosSeleccionados = ref([])
const mostrandoListaAlumnos = ref(false)

const seleccionarTodos = computed({
    get() { return alumnos.value.length > 0 && alumnosSeleccionados.value.length === alumnos.value.length; },
    set(valor) { alumnosSeleccionados.value = valor ? alumnos.value.map(a => a.id) : []; }
})

// === 2. GESTIÓN DE COBROS MASIVOS ===
const conceptos = ref([])
const conceptoSeleccionado = ref(null)
const procesandoMasivo = ref(false)
const mostrandoFormCobro = ref(false)
const nuevoConcepto = ref({
    nombre: '', monto_estandar: '', fecha_vencimiento: new Date().toISOString().split('T')[0], destino: 'CUENTA'
})

// === 3. GESTIÓN DE PRORRATEO (Repartir Dinero Billetera/Cuenta) ===
const mostrandoFormProrrateo = ref(false)
const procesandoProrrateo = ref(false)
const nuevoProrrateo = ref({
    monto_total: '',
    tipo: 'INGRESO',
    descripcion: '',
    balde: 'CUENTA', // Por defecto ataca el fondo del curso
    registrar_egreso: false,
    fecha_gasto: new Date().toISOString().split('T')[0]
})

// === 4. DEPÓSITO A PLAZO (CONECTADO A LA BD) ===
const editandoDeposito = ref(false)
const mostrandoBeneficiarios = ref(false) // 👈 NUEVO: Controla la visibilidad de la lista en modo lectura

const deposito = ref({
    monto: 0,
    fecha_inicio: '',
    fecha_fin: '',
    alumnos_beneficiarios: []
})

// Función auxiliar para traducir ID a Nombre en el modo lectura del depósito
const obtenerAlumnoPorId = (id) => {
    return alumnos.value.find(a => a.id === id) || { numero_lista: '?', nombre_completo: 'Desconocido' };
}

// Calculadora automática
const cuotaAhorro = computed(() => {
    const idsActivos = editandoDeposito.value ? alumnosSeleccionados.value : (deposito.value.alumnos_beneficiarios || []);
    if (idsActivos.length === 0 || !deposito.value.monto) return 0;
    return Math.floor(deposito.value.monto / idsActivos.length);
})

// Lista visual de los alumnos beneficiarios (solo para modo edición)
const listaAlumnosAhorro = computed(() => {
    const idsActivos = editandoDeposito.value ? alumnosSeleccionados.value : (deposito.value.alumnos_beneficiarios || []);
    return alumnos.value.filter(a => idsActivos.includes(a.id));
})

const guardarDeposito = async () => {
    if (!deposito.value.monto || deposito.value.monto <= 0) return alert("Ingresa un monto válido.");
    if (!deposito.value.fecha_inicio || !deposito.value.fecha_fin) return alert("Faltan las fechas.");
    if (alumnosSeleccionados.value.length === 0) return alert("Selecciona alumnos en la lista de abajo.");

    try {
        const payload = {
            monto: deposito.value.monto,
            fecha_inicio: deposito.value.fecha_inicio,
            fecha_fin: deposito.value.fecha_fin,
            alumnos_beneficiarios: alumnosSeleccionados.value
        };

        const res = await api.post('deposito/', payload);

        deposito.value = res.data;
        editandoDeposito.value = false;
        alert("🏦 ¡Depósito a Plazo guardado en la Base de Datos!");
    } catch (error) {
        console.error(error);
        alert("Error al guardar el depósito. Revisa los datos.");
    }
}

// === 5. INGRESO RÁPIDO DE ABONOS ===
const mostrandoFormularioAbono = ref(false)
const nuevoAbono = ref({
    monto: '', fecha_transferencia: new Date().toISOString().split('T')[0], comprobante: ''
})

// === 7. FONDOS EN RECAUDACIÓN (MONTONCITOS) ===
const conceptoARendir = ref(null)
const formRendicion = ref({ monto: 0, descripcion: '', fecha_gasto: '', comprobante: '' })

const fondosActivos = computed(() => {
    return conceptos.value
        .filter(c => c.estado_fondo !== 'RENDIDO' && c.destino === 'EXTERNO')
        .map(c => {
            let recaudado = 0;
            alumnos.value.forEach(al => {
                if (al.cargos) {
                    const cargo = al.cargos.find(cargo => cargo.concepto === c.id && cargo.estado === 'PAGADO')
                    if (cargo) recaudado += cargo.monto_total
                }
            })
            return { ...c, recaudado }
        })
})

const abrirRendicion = (concepto) => {
    conceptoARendir.value = concepto
    formRendicion.value = {
        monto: concepto.recaudado,
        descripcion: `Pago a proveedor: ${concepto.nombre}`,
        fecha_gasto: new Date().toISOString().split('T')[0],
        comprobante: ''
    }
}

const procesarRendicion = async () => {
    if (!formRendicion.value.monto || formRendicion.value.monto <= 0) return alert("El monto debe ser mayor a 0.")
    if (!formRendicion.value.fecha_gasto) return alert("Falta la fecha.")

    try {
        await api.post(`conceptos/${conceptoARendir.value.id}/rendir_fondo/`, formRendicion.value)
        alert("¡Fondo transferido y registrado como egreso en el banco! 💸")
        conceptoARendir.value = null
        cargarDatosGlobales()
    } catch (e) {
        alert(e.response?.data?.error || "Error al rendir el fondo.")
    }
}

// === CARGA INICIAL ===
const cargarDatosGlobales = async () => {
    try {
        const resAlumnos = await api.get('mis-alumnos/')
        alumnos.value = resAlumnos.data
        alumnosSeleccionados.value = []

        const resConceptos = await api.get('conceptos/')
        conceptos.value = resConceptos.data

        const resDeposito = await api.get('deposito/')
        if (resDeposito.data && Object.keys(resDeposito.data).length > 0) {
            deposito.value = resDeposito.data;
        } else {
            deposito.value = {
                monto: 0,
                fecha_inicio: new Date().toISOString().split('T')[0],
                fecha_fin: '',
                alumnos_beneficiarios: []
            }
        }
    } catch (error) { console.error("Error cargando datos:", error) }
}

onMounted(() => { cargarDatosGlobales() })

const formatearDinero = (valor) => {
    return new Intl.NumberFormat('es-CL', { style: 'currency', currency: 'CLP' }).format(valor || 0)
}

const recargarAlumnoActual = async () => {
    if (!alumnoSeleccionado.value) return
    try {
        const res = await api.get('mis-alumnos/')
        alumnos.value = res.data
        const actualizado = alumnos.value.find(a => a.id === alumnoSeleccionado.value.id)
        alumnoSeleccionado.value = actualizado
        cargoSeleccionado.value = null
        cargarHistorial()
    } catch (e) { console.error(e) }
}

watch(alumnoSeleccionado, (nuevoAlumno) => {
    if (nuevoAlumno) cargarHistorial()
    else historialTransacciones.value = []
})

const cargarHistorial = async () => {
    try {
        const res = await api.get('movimientos/')
        const listaMovimientos = res.data.results || res.data
        if (!alumnoSeleccionado.value.cuenta || !alumnoSeleccionado.value.cuenta.id) {
            historialTransacciones.value = []
            return
        }
        historialTransacciones.value = listaMovimientos.filter(
            mov => mov.cuenta === alumnoSeleccionado.value.cuenta.id
        ).reverse()
    } catch (e) { console.error("Error cargando historial", e) }
}

// === 6. REGISTRO DE EGRESOS REALES (BANCO) ===
const mostrandoFormGasto = ref(false)
const nuevoGasto = ref({
    monto: '', descripcion: '', fecha_gasto: new Date().toISOString().split('T')[0], comprobante: ''
})

const registrarGasto = async () => {
    if (!nuevoGasto.value.monto || nuevoGasto.value.monto <= 0) return alert("Monto inválido")
    if (!nuevoGasto.value.descripcion) return alert("Falta descripción")

    try {
        await api.post('egresos/', nuevoGasto.value)
        alert("¡Gasto registrado en el libro contable! 📉")
        nuevoGasto.value = { monto: '', descripcion: '', fecha_gasto: new Date().toISOString().split('T')[0], comprobante: '' }
        mostrandoFormGasto.value = false
    } catch (e) {
        alert("Error al registrar gasto")
    }
}

// === FUNCIONES DE COBROS MASIVOS ===
const crearConceptoCobro = async () => {
    if (!nuevoConcepto.value.nombre || !nuevoConcepto.value.monto_estandar) return alert("Faltan datos.")
    try {
        const res = await api.post('conceptos/', nuevoConcepto.value)
        conceptos.value.push(res.data)
        conceptoSeleccionado.value = res.data.id
        alert("¡Cobro creado exitosamente en la base de datos! ✅")
        nuevoConcepto.value = { nombre: '', monto_estandar: '', fecha_vencimiento: new Date().toISOString().split('T')[0], destino: 'CUENTA' }
        mostrandoFormCobro.value = false
    } catch (error) { alert("Error al crear el cobro.") }
}

const ejecutarCobroMasivo = async () => {
    if (!conceptoSeleccionado.value || alumnosSeleccionados.value.length === 0) return alert("Faltan datos o alumnos.")
    if (!confirm(`¿Generar deuda a ${alumnosSeleccionados.value.length} alumno(s)?`)) return

    procesandoMasivo.value = true
    try {
        const idsExcluidos = alumnos.value.filter(a => !alumnosSeleccionados.value.includes(a.id)).map(a => a.id)
        const cursoObj = alumnos.value[0]?.curso || '8B'

        const respuesta = await api.post(`conceptos/${conceptoSeleccionado.value}/generar_masivo/`, {
            curso: cursoObj, excluidos: idsExcluidos
        })
        alert(`Cobros Generados:\n✅ Creados: ${respuesta.data.cargos_creados}\n⏭️ Ya existían: ${respuesta.data.cargos_ya_existian}`)

        cargarDatosGlobales()
        recargarAlumnoActual()
        mostrandoListaAlumnos.value = false
    } catch (error) { alert("Error al generar las deudas.") }
    finally { procesandoMasivo.value = false }
}

// === FUNCIÓN DE PRORRATEO (BILLETERA) ===
const ejecutarProrrateo = async () => {
    if (!nuevoProrrateo.value.monto_total || nuevoProrrateo.value.monto_total <= 0) return alert("Ingresa un monto válido.")
    if (!nuevoProrrateo.value.descripcion) return alert("Ingresa una descripción.")
    if (alumnosSeleccionados.value.length === 0) return alert("Selecciona alumnos.")

    const accion = nuevoProrrateo.value.tipo === 'INGRESO' ? 'sumarán' : 'descontarán'
    const destino = nuevoProrrateo.value.balde === 'CUENTA' ? 'al Fondo del Curso (Cuenta)' : 'a los saldos sin asignar (Billeteras)'
    if (!confirm(`¿Seguro? Se ${accion} los fondos ${destino} de los ${alumnosSeleccionados.value.length} alumnos seleccionados.`)) return

    procesandoProrrateo.value = true
    try {
        const payload = {
            alumnos_ids: alumnosSeleccionados.value,
            monto_total: nuevoProrrateo.value.monto_total,
            tipo: nuevoProrrateo.value.tipo,
            descripcion: nuevoProrrateo.value.descripcion,
            balde: nuevoProrrateo.value.balde,
            registrar_egreso: nuevoProrrateo.value.tipo === 'EGRESO' ? nuevoProrrateo.value.registrar_egreso : false,
            fecha_gasto: nuevoProrrateo.value.fecha_gasto
        }

        const res = await api.post('prorrateo/', payload)
        alert(res.data.mensaje + " 🚀")

        nuevoProrrateo.value = { monto_total: '', tipo: 'INGRESO', descripcion: '', balde: 'CUENTA', registrar_egreso: false, fecha_gasto: new Date().toISOString().split('T')[0] }
        mostrandoFormProrrateo.value = false

        cargarDatosGlobales()
        if (alumnoSeleccionado.value) recargarAlumnoActual()
    } catch (error) {
        alert(error.response?.data?.error || "Error al procesar.")
    } finally {
        procesandoProrrateo.value = false
    }
}

// === CÁLCULO DE LOS 3 BALDES DEL ALUMNO ===
const baldeBilletera = computed(() => alumnoSeleccionado.value?.cuenta?.saldo_disponible || 0)

const baldeCuenta = computed(() => {
    if (!alumnoSeleccionado.value) return 0;
    const ahorroBase = alumnoSeleccionado.value.cuenta?.cuenta_ahorro || 0;
    const pagadoCuenta = alumnoSeleccionado.value.cargos?.filter(c => c.estado === 'PAGADO' && c.concepto_destino === 'CUENTA').reduce((sum, c) => sum + c.monto_total, 0) || 0;
    return ahorroBase + pagadoCuenta;
})

const baldeExterno = computed(() => {
    if (!alumnoSeleccionado.value) return 0;
    return alumnoSeleccionado.value.cargos?.filter(c => c.estado === 'PAGADO' && c.concepto_destino === 'EXTERNO').reduce((sum, c) => sum + c.monto_total, 0) || 0;
})

// === FUNCIONES DE LA BILLETERA ===
const guardarAbono = async () => {
    if (!alumnoSeleccionado.value) return alert("Selecciona un alumno")
    if (!nuevoAbono.value.monto || nuevoAbono.value.monto <= 0) return alert("Monto inválido")

    try {
        await api.post('pagos/', {
            alumno: alumnoSeleccionado.value.id,
            monto: nuevoAbono.value.monto,
            fecha_transferencia: nuevoAbono.value.fecha_transferencia,
            comprobante: nuevoAbono.value.comprobante || 'Ingreso Manual',
            estado: 'APROBADO'
        })

        alert("¡Dinero ingresado a la billetera! 💰")
        nuevoAbono.value = { monto: '', fecha_transferencia: new Date().toISOString().split('T')[0], comprobante: '' }
        mostrandoFormularioAbono.value = false
        await recargarAlumnoActual()
    } catch (error) { alert("Error al guardar abono.") }
}

const eliminarAbono = async (abonoId) => {
    if (!confirm("¿Estás seguro de eliminar este ingreso? Se descontará la plata de la billetera del alumno.")) return
    try {
        await api.delete(`pagos/${abonoId}/`)
        alert("Ingreso eliminado y plata descontada. 🗑️")
        await recargarAlumnoActual()
    } catch (error) { alert("No se pudo eliminar el ingreso.") }
}

const reversarPago = async (cargoId) => {
    if (!confirm("¿Anular este pago? La deuda volverá a PENDIENTE y la plata volverá a la billetera.")) return
    try {
        await api.post(`cargos/${cargoId}/reversar_pago/`)
        alert("¡Pago reversado! El dinero volvió a la billetera. ⏪")
        await recargarAlumnoActual()
    } catch (error) { alert("Error al reversar el pago.") }
}

const eliminarCargo = async (cargoId) => {
    if (!confirm("¿Borrar esta deuda? No se puede deshacer.")) return
    try {
        await api.delete(`cargos/${cargoId}/`)
        alert("Deuda eliminada 🗑️")
        await recargarAlumnoActual()
    } catch (error) { alert("No se puede borrar. Revisa si está pagada.") }
}

const procesarPagoConBilletera = async () => {
    if (alumnoSeleccionado.value.cuenta.saldo_disponible < cargoSeleccionado.value.monto_total) return alert("Saldo insuficiente.")
    try {
        await api.post(`cargos/${cargoSeleccionado.value.id}/pagar_con_billetera/`)
        alert("¡Cuota Pagada Exitosamente! ✅")
        await recargarAlumnoActual()
    } catch (error) { alert(error.response?.data?.error || "Error al procesar el pago") }
}
</script>

<template>
    <div class="panel-tesorero">
        <h1>🛡️ Centro de Mando: Tesorería</h1>

        <div class="zona-masiva-grid">

            <div class="panel-masivo">
                <div class="header-masivo">
                    <h3>⚡ Generar Deudas Masivas</h3>
                    <button @click="mostrandoFormCobro = !mostrandoFormCobro" class="btn-toggle-cobro">
                        {{ mostrandoFormCobro ? '❌ Cerrar' : '➕ Crear Cobro' }}
                    </button>
                </div>

                <div v-if="mostrandoFormCobro" class="form-crear-cobro">
                    <div class="grupo-inputs-cobro">
                        <div class="campo">
                            <label>Nombre del Cobro:</label>
                            <input type="text" v-model="nuevoConcepto.nombre" placeholder="Ej: Cuota Abril" />
                        </div>
                        <div class="campo">
                            <label>Monto ($):</label>
                            <input type="number" v-model="nuevoConcepto.monto_estandar" placeholder="Ej: 5000" />
                        </div>
                        <div class="campo">
                            <label>Vencimiento:</label>
                            <input type="date" v-model="nuevoConcepto.fecha_vencimiento" />
                        </div>
                        <div class="campo">
                            <label>Destino de la plata:</label>
                            <select v-model="nuevoConcepto.destino">
                                <option value="CUENTA">Fondo del Curso (Cuotas, Salidas, Regalos)</option>
                                <option value="EXTERNO">Aportes Extra / Voluntarios (Rifas, Solidario)</option>
                            </select>
                        </div>
                    </div>
                    <button @click="crearConceptoCobro" class="btn-guardar-cobro"
                        style="margin-top: 15px; width: 100%;">Guardar Concepto en Sistema</button>
                </div>

                <div class="controles-masivos" style="margin-top: 20px;">
                    <label>Cobro a aplicar:</label>
                    <select v-model="conceptoSeleccionado" class="select-grande"
                        style="width: 100%; margin-bottom: 10px;">
                        <option :value="null">-- Selecciona un cobro guardado --</option>
                        <option v-for="c in conceptos" :key="c.id" :value="c.id">
                            {{ c.nombre }} ({{ formatearDinero(c.monto_estandar) }})
                        </option>
                    </select>
                    <button @click="ejecutarCobroMasivo" class="btn-masivo"
                        :disabled="procesandoMasivo || alumnosSeleccionados.length === 0">
                        {{ procesandoMasivo ? 'Procesando...' : '🚀 Aplicar a los seleccionados' }}
                    </button>
                </div>
            </div>

            <div class="panel-masivo panel-prorrateo">
                <div class="header-masivo">
                    <h3>🍕 Repartir a Billeteras</h3>
                    <button @click="mostrandoFormProrrateo = !mostrandoFormProrrateo" class="btn-toggle-prorrateo">
                        {{ mostrandoFormProrrateo ? '❌ Cerrar' : '🧮 Abrir Calculadora' }}
                    </button>
                </div>

                <div v-if="mostrandoFormProrrateo" class="form-prorrateo" style="margin-top: 15px;">
                    <div class="grupo-inputs-cobro">
                        <div class="campo">
                            <label>Monto Total a Repartir ($):</label>
                            <input type="number" v-model="nuevoProrrateo.monto_total" placeholder="Ej: 20000" />
                        </div>
                        <div class="campo">
                            <label>Tipo de Movimiento:</label>
                            <select v-model="nuevoProrrateo.tipo">
                                <option value="INGRESO">Ganancia (+)</option>
                                <option value="EGRESO">Gasto (-)</option>
                            </select>
                        </div>
                        <div class="campo">
                            <label>¿A qué fondo afecta?</label>
                            <select v-model="nuevoProrrateo.balde">
                                <option value="CUENTA">Fondo del Curso (Patrimonio)</option>
                                <option value="BILLETERA">Billeteras (Saldos sin asignar)</option>
                            </select>
                        </div>
                    </div>
                    <div class="campo" style="margin-top: 10px;">
                        <label>Descripción para la cartola:</label>
                        <input type="text" v-model="nuevoProrrateo.descripcion"
                            placeholder="Ej: Regalo Día del Profesor" />
                    </div>

                    <div v-if="nuevoProrrateo.tipo === 'EGRESO'"
                        style="margin-top: 15px; padding: 10px; background: #ffebee; border-left: 4px solid #c62828; border-radius: 4px;">
                        <label
                            style="display: flex; align-items: center; gap: 10px; cursor: pointer; color: #c62828; font-weight: bold; font-size: 0.9em;">
                            <input type="checkbox" v-model="nuevoProrrateo.registrar_egreso"
                                style="width: 18px; height: 18px;" />
                            ¿Registrar automáticamente la salida del dinero del Banco Real?
                        </label>
                        <div v-if="nuevoProrrateo.registrar_egreso" style="margin-top: 10px; display: flex; gap: 10px;">
                            <div class="campo" style="flex: 1;">
                                <label>Fecha de la salida real:</label>
                                <input type="date" v-model="nuevoProrrateo.fecha_gasto" />
                            </div>
                        </div>
                    </div>

                    <button @click="ejecutarProrrateo" class="btn-masivo btn-prorratear"
                        :disabled="procesandoProrrateo || alumnosSeleccionados.length === 0"
                        style="margin-top: 15px; width: 100%;">
                        {{ procesandoProrrateo ? 'Calculando...' : '🧮 Aplicar Cálculo a Alumnos' }}
                    </button>
                    <p style="font-size: 0.8em; color: #7f8c8d; margin-top: 10px; text-align: center;">
                        El monto se dividirá entre los alumnos marcados abajo.
                    </p>
                </div>
            </div>

            <div class="panel-masivo panel-rendir">
                <div class="header-masivo">
                    <h3>📊 Fondos por Rendir</h3>
                </div>

                <p style="font-size: 0.85em; color: #7b1fa2; margin-top:10px;">Dinero agrupado de cobros que aún no
                    transfieres al proveedor final.</p>

                <div class="lista-gastos" style="margin-top: 15px;">
                    <div v-for="fondo in fondosActivos" :key="fondo.id" class="tarjeta-fondo-rendir">
                        <div class="gasto-info">
                            <strong style="color:#4a148c; display:block; margin-bottom: 5px; font-size:1.05em;">{{
                                fondo.nombre }}</strong>
                            <small style="color: #666;">Recaudado: <span class="texto-verde">{{
                                    formatearDinero(fondo.recaudado) }}</span></small>
                        </div>
                        <button v-if="conceptoARendir?.id !== fondo.id" @click="abrirRendicion(fondo)"
                            class="btn-mini btn-rendir">
                            📤 Rendir
                        </button>
                    </div>

                    <div v-if="fondosActivos.length === 0" class="hint" style="text-align:center;">
                        No hay fondos activos en recaudación.
                    </div>
                </div>

                <div v-if="conceptoARendir" class="form-crear-cobro"
                    style="border-color: #8e24aa; margin-top: 15px; background: white;">
                    <strong style="color: #8e24aa;">Rendir: {{ conceptoARendir.nombre }}</strong>
                    <hr style="border: 0; border-top: 1px solid #f3e5f5; margin: 8px 0;" />
                    <div class="grupo-inputs-cobro">
                        <div class="campo">
                            <label>Monto exacto a transferir:</label>
                            <input type="number" v-model="formRendicion.monto" />
                        </div>
                        <div class="campo">
                            <label>Descripción / Motivo:</label>
                            <input type="text" v-model="formRendicion.descripcion" />
                        </div>
                        <div class="campo">
                            <label>Fecha de pago:</label>
                            <input type="date" v-model="formRendicion.fecha_gasto" />
                        </div>
                        <div class="campo">
                            <label>Ref/Boleta (Opcional):</label>
                            <input type="text" v-model="formRendicion.comprobante" />
                        </div>
                    </div>
                    <div style="display: flex; gap: 10px; margin-top: 15px;">
                        <button @click="conceptoARendir = null"
                            style="flex:1; padding: 10px; border: 1px solid #ccc; background: white; border-radius:4px; cursor:pointer;">Cancelar</button>
                        <button @click="procesarRendicion"
                            style="flex:2; padding: 10px; border: none; background: #8e24aa; color:white; border-radius:4px; font-weight:bold; cursor:pointer;">Confirmar
                            Rendición</button>
                    </div>
                </div>
            </div>

            <div class="panel-masivo panel-deposito">
                <div class="header-masivo">
                    <h3>🏦 Depósito a Plazo</h3>
                    <button @click="editandoDeposito = !editandoDeposito" class="btn-toggle-deposito">
                        {{ editandoDeposito ? '❌ Cancelar' : '✏️ Editar' }}
                    </button>
                </div>

                <div v-if="!editandoDeposito" class="info-deposito" style="text-align: center; margin-top: 15px;">
                    <div v-if="deposito.monto > 0">
                        <h2 style="color: #2980b9; font-size: 2.2em; margin: 0;">{{ formatearDinero(deposito.monto) }}
                        </h2>
                        <p style="color: #7f8c8d; font-size: 0.9em; margin-top: 5px;">
                            📅 Desde: <strong>{{ deposito.fecha_inicio }}</strong><br>
                            ⏳ Vence: <strong>{{ deposito.fecha_fin }}</strong>
                        </p>

                        <div @click="mostrandoBeneficiarios = !mostrandoBeneficiarios" class="caja-clickeable-ahorro">
                            <strong style="color: #27ae60;">Saldo por alumno: {{
                                formatearDinero(Math.floor(deposito.monto / (deposito.alumnos_beneficiarios?.length ||
                                1))) }}</strong><br>
                            <small style="color: #3498db; text-decoration: underline;">
                                (Toca aquí para ver los {{ deposito.alumnos_beneficiarios?.length || 0 }} alumnos
                                beneficiarios)
                            </small>
                        </div>

                        <div v-show="mostrandoBeneficiarios" class="lista-nombres-ahorro" style="text-align: left;">
                            <div v-for="id_al in deposito.alumnos_beneficiarios" :key="id_al" class="nombre-mini">
                                {{ obtenerAlumnoPorId(id_al).numero_lista }}. {{
                                obtenerAlumnoPorId(id_al).nombre_completo }}
                            </div>
                            <div v-if="!deposito.alumnos_beneficiarios || deposito.alumnos_beneficiarios.length === 0"
                                class="hint" style="text-align:center;">
                                No hay alumnos registrados en este depósito.
                            </div>
                        </div>

                    </div>
                    <div v-else class="esperando" style="padding: 15px; margin-top:0;">
                        <p>No hay depósito a plazo registrado.</p>
                        <small>Haz clic en "Editar" para crearlo.</small>
                    </div>
                </div>

                <div v-else>
                    <div class="form-crear-cobro" style="border-color: #3498db; margin-top: 15px;">
                        <div class="campo" style="margin-bottom: 10px;">
                            <label>Monto Total ($):</label>
                            <input type="number" v-model="deposito.monto" />
                        </div>
                        <div class="grupo-inputs-cobro">
                            <div class="campo">
                                <label>Fecha Inicio:</label>
                                <input type="date" v-model="deposito.fecha_inicio" />
                            </div>
                            <div class="campo">
                                <label>Fecha Vencimiento:</label>
                                <input type="date" v-model="deposito.fecha_fin" />
                            </div>
                        </div>
                        <button @click="guardarDeposito" class="btn-guardar-cobro"
                            style="background-color: #3498db; margin-top: 15px; width: 100%;">💾 Guardar
                            Cambios</button>
                    </div>

                    <hr class="divisor-masivo" style="background: #bbdefb; margin: 15px 0;" />

                    <div class="calculadora-deposito">
                        <div
                            style="display: flex; justify-content: space-between; align-items: center; background: #fff; padding: 10px; border-radius: 8px; border: 1px solid #bbdefb;">
                            <span style="font-weight: bold; color: #2c3e50;">Saldo por alumno:</span>
                            <strong style="color: #27ae60; font-size: 1.3em;">{{ formatearDinero(cuotaAhorro)
                                }}</strong>
                        </div>
                        <p style="font-size: 0.8em; color: #555; text-align: center; margin-top: 10px;">
                            Prorrateado entre <strong>{{ alumnosSeleccionados.length }}</strong> alumnos marcados:
                        </p>
                        <div class="lista-nombres-ahorro" style="text-align: left;">
                            <div v-for="al in listaAlumnosAhorro" :key="al.id" class="nombre-mini">
                                {{ al.numero_lista }}. {{ al.nombre_completo }}
                            </div>
                            <div v-if="listaAlumnosAhorro.length === 0" class="hint" style="text-align:center;">
                                Marca alumnos en la lista de la derecha para ver el cálculo.
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <div class="panel-masivo span-2-cols panel-alumnos">
                <div class="header-masivo">
                    <h3 style="color: #2c3e50;">👥 Lista de Alumnos</h3>
                </div>
                <p style="font-size: 0.85em; color: #7f8c8d; margin-top:10px;">Selecciona los alumnos para aplicarles
                    cobros, prorrateos o sumarlos al Depósito a Plazo.</p>

                <div class="caja-checkboxes" style="margin-top: 15px;">
                    <div class="checkbox-item todos">
                        <input type="checkbox" id="chkTodos" v-model="seleccionarTodos">
                        <label for="chkTodos"><strong>SELECCIONAR TODO EL CURSO</strong> <small>({{
                                alumnosSeleccionados.length }}/{{ alumnos.length }})</small></label>
                    </div>

                    <div class="toggle-lista" @click="mostrandoListaAlumnos = !mostrandoListaAlumnos">
                        <span>{{ mostrandoListaAlumnos ? '🔽 Ocultar lista individual' : '▶️ Ver/Editar lista individual' }}</span>
                    </div>

                    <div v-show="mostrandoListaAlumnos" class="lista-alumnos-check">
                        <div v-for="al in alumnos" :key="al.id" class="checkbox-item individual">
                            <input type="checkbox" :id="'chk' + al.id" :value="al.id" v-model="alumnosSeleccionados">
                            <label :for="'chk' + al.id">{{ al.numero_lista }}. {{ al.nombre_completo }}</label>
                        </div>
                    </div>
                </div>
            </div>

        </div>
        <hr style="border: 0; height: 2px; background: #e0e0e0; margin: 40px 0;">

        <div class="selector">
            <label>🔍 Buscar Alumno individual:</label>
            <select v-model="alumnoSeleccionado" @change="cargoSeleccionado = null">
                <option :value="null">-- Elegir Alumno --</option>
                <option v-for="al in alumnos" :key="al.id" :value="al">
                    {{ al.numero_lista }}. {{ al.nombre_completo }} (Billetera: {{
                        formatearDinero(al.cuenta?.saldo_disponible) }})
                </option>
            </select>
        </div>

        <div v-if="alumnoSeleccionado" class="mesa-trabajo-contenedor">
            <div class="mesa-trabajo">
                <div class="columna fondos">
                    <div class="titulo-con-accion">
                        <h3>👛 Cuenta Operativa</h3>
                        <button @click="mostrandoFormularioAbono = !mostrandoFormularioAbono" class="btn-mini">
                            {{ mostrandoFormularioAbono ? '❌' : '➕ Ingreso' }}
                        </button>
                    </div>

                    <div style="display: flex; flex-direction: column; gap: 10px; margin-bottom: 20px;">
                        <div class="tarjeta-billetera" style="margin-bottom: 0;">
                            <small>👛 Balde 1: Billetera (Sin asignar)</small>
                            <h2>{{ formatearDinero(baldeBilletera) }}</h2>
                        </div>
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
                            <div
                                style="background: #27ae60; color: white; padding: 10px; border-radius: 8px; text-align: center;">
                                <small style="font-size: 0.7em; text-transform: uppercase;">📁 Balde 2:
                                    Cuenta</small><br>
                                <strong style="font-size: 1.2em;">{{ formatearDinero(baldeCuenta) }}</strong>
                            </div>
                            <div
                                style="background: #f39c12; color: white; padding: 10px; border-radius: 8px; text-align: center;">
                                <small style="font-size: 0.7em; text-transform: uppercase;">🎟️ Balde 3:
                                    Externos</small><br>
                                <strong style="font-size: 1.2em;">{{ formatearDinero(baldeExterno) }}</strong>
                            </div>
                        </div>
                    </div>

                    <div class="info-apoderado">
                        <small>👨‍👩‍👧 <strong>Apoderados:</strong></small><br>
                        <span>{{ alumnoSeleccionado.apoderado_nombre }}</span>
                    </div>

                    <div v-if="mostrandoFormularioAbono" class="form-rapido">
                        <input type="number" v-model="nuevoAbono.monto" placeholder="Monto $" />
                        <input type="text" v-model="nuevoAbono.comprobante" placeholder="N° Comprobante / Detalle" />
                        <input type="date" v-model="nuevoAbono.fecha_transferencia" />
                        <button @click="guardarAbono" class="btn-guardar-mini">Cargar a la Billetera</button>
                    </div>

                    <h4 style="margin-top: 20px; color:#7f8c8d; font-size: 0.9em;">Historial de Abonos Manuales:</h4>
                    <div v-if="alumnoSeleccionado.abonos.length === 0" class="hint">Sin ingresos manuales previos.</div>

                    <div v-for="abono in alumnoSeleccionado.abonos" :key="abono.id" class="item-lista">
                        <div class="flex-row">
                            <span>📅 {{ abono.fecha_transferencia }}</span>
                            <strong style="color: #27ae60;">+{{ formatearDinero(abono.monto) }}</strong>
                        </div>
                        <div class="flex-row align-center" style="margin-top: 5px;">
                            <small>Ref: {{ abono.comprobante || '---' }} <br> Estado: <span :class="abono.estado">{{
                                abono.estado }}</span></small>
                            <button @click.stop="eliminarAbono(abono.id)" class="btn-eliminar-abono"
                                title="Borrar Ingreso">🗑️</button>
                        </div>
                    </div>
                </div>

                <div class="columna accion">
                    <div v-if="cargoSeleccionado" class="caja-imputar">
                        <h4>🔗 Pagar Deuda</h4>
                        <div class="resumen-pago">
                            <p><strong>Deuda:</strong> {{ cargoSeleccionado.concepto_nombre }}</p>
                            <p><strong>Costo:</strong> <span class="texto-rojo">{{
                                formatearDinero(cargoSeleccionado.monto_total) }}</span></p>
                        </div>
                        <div class="resumen-pago mt-2">
                            <p><strong>En Billetera:</strong> <span class="texto-verde">{{
                                formatearDinero(alumnoSeleccionado.cuenta?.saldo_disponible) }}</span></p>
                        </div>
                        <button @click="procesarPagoConBilletera" class="btn-guardar"
                            :disabled="alumnoSeleccionado.cuenta?.saldo_disponible < cargoSeleccionado.monto_total"
                            :class="{ 'disabled-btn': alumnoSeleccionado.cuenta?.saldo_disponible < cargoSeleccionado.monto_total }">
                            PAGAR AHORA
                        </button>
                        <p v-if="alumnoSeleccionado.cuenta?.saldo_disponible < cargoSeleccionado.monto_total"
                            style="color:#ffcdd2; font-size:0.8em; margin-top:10px;">⚠️ Saldo insuficiente.</p>
                    </div>
                    <div v-else class="esperando">
                        <p>👈 La Billetera tiene fondos.</p>
                        <p>👉 Haz clic en una Deuda "Pendiente" para pagarla.</p>
                    </div>
                </div>

                <div class="columna deudas">
                    <h3>📋 Deudas del Alumno</h3>
                    <div v-if="alumnoSeleccionado.cargos && alumnoSeleccionado.cargos.length > 0">
                        <table class="tabla-deudas">
                            <thead>
                                <tr>
                                    <th>Concepto</th>
                                    <th>Monto & Estado</th>
                                    <th>Acción</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr v-for="cargo in alumnoSeleccionado.cargos" :key="cargo.id"
                                    :class="{ 'fila-activa': cargoSeleccionado === cargo }"
                                    @click="cargo.estado === 'PENDIENTE' ? (cargoSeleccionado = cargo) : null"
                                    style="cursor: pointer;">
                                    <td>
                                        <strong>{{ cargo.concepto_nombre }}</strong><br>
                                        <small style="color: #777;">Destino: {{ cargo.concepto_destino }}</small>
                                    </td>
                                    <td :class="cargo.estado === 'PAGADO' ? 'texto-verde' : 'texto-rojo'">
                                        {{ formatearDinero(cargo.monto_total) }}<br>
                                        <span class="badge-estado" :class="cargo.estado">{{ cargo.estado }}</span>
                                    </td>
                                    <td style="text-align: center;">
                                        <button v-if="cargo.estado === 'PENDIENTE'"
                                            @click.stop="eliminarCargo(cargo.id)" class="btn-eliminar"
                                            title="Borrar Deuda">🗑️</button>
                                        <button v-if="cargo.estado === 'PAGADO'" @click.stop="reversarPago(cargo.id)"
                                            class="btn-reversar" title="Anular Pago">⏪ Reversar</button>
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                    <p v-else class="hint">No tiene deudas registradas.</p>
                </div>
            </div>

            <div class="auditoria-contenedor">
                <h3>📖 Cartola Histórica</h3>
                <p class="hint">Registro inalterable de todos los movimientos de dinero (Abonos, Pagos y Prorrateos).
                </p>
                <table class="tabla-auditoria">
                    <thead>
                        <tr>
                            <th>Fecha</th>
                            <th>Tipo</th>
                            <th>Descripción</th>
                            <th style="text-align: right;">Monto</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr v-if="historialTransacciones.length === 0">
                            <td colspan="4" class="hint" style="text-align: center;">Sin transacciones.</td>
                        </tr>
                        <tr v-for="mov in historialTransacciones" :key="mov.id">
                            <td>{{ new Date(mov.fecha).toLocaleString('es-CL') }}</td>
                            <td><span class="badge-tipo" :class="mov.tipo">{{ mov.tipo }}</span></td>
                            <td>{{ mov.descripcion }}</td>
                            <td style="text-align: right; font-weight: bold;"
                                :class="mov.tipo === 'INGRESO' ? 'texto-verde' : 'texto-rojo'">
                                {{ mov.tipo === 'INGRESO' ? '+' : '-' }}{{ formatearDinero(mov.monto) }}
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>

        </div>
    </div>
</template>

<style scoped>
.panel-tesorero {
    padding: 20px;
    background-color: #fff;
    border-radius: 8px;
    color: #333;
    max-width: 1400px;
    margin: 0 auto;
    font-family: 'Segoe UI', sans-serif;
}

/* === 🚀 NUEVA ZONA MASIVA GRID === */
.zona-masiva-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 20px;
    margin-bottom: 20px;
}

.span-2-cols {
    grid-column: span 2;
}

.panel-masivo {
    background-color: #fff8e1;
    border: 1px solid #ffe082;
    padding: 20px;
    border-radius: 12px;
}

.panel-prorrateo {
    background-color: #e8f5e9;
    border: 1px solid #a5d6a7;
}

.panel-rendir {
    background-color: #f3e5f5;
    border: 1px solid #ce93d8;
}

.panel-deposito {
    background-color: #e3f2fd;
    border: 1px solid #90caf9;
}

.panel-alumnos {
    background-color: #f8f9fa;
    border: 1px solid #ddd;
}

.header-masivo {
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 2px dashed rgba(0, 0, 0, 0.1);
    padding-bottom: 10px;
}

.header-masivo h3 {
    margin: 0;
    color: #f57c00;
}

.panel-prorrateo .header-masivo h3 {
    color: #2e7d32;
}

.panel-deposito .header-masivo h3 {
    color: #1976d2;
}

.btn-toggle-cobro {
    background: white;
    border: 1px solid #f57c00;
    color: #f57c00;
    padding: 6px 12px;
    border-radius: 20px;
    cursor: pointer;
    font-weight: bold;
    font-size: 0.85em;
    transition: 0.2s;
}

.btn-toggle-cobro:hover {
    background: #f57c00;
    color: white;
}

.btn-toggle-prorrateo {
    background: white;
    border: 1px solid #2e7d32;
    color: #2e7d32;
    padding: 6px 12px;
    border-radius: 20px;
    cursor: pointer;
    font-weight: bold;
    font-size: 0.85em;
    transition: 0.2s;
}

.btn-toggle-prorrateo:hover {
    background: #2e7d32;
    color: white;
}

.btn-toggle-deposito {
    background: white;
    border: 1px solid #1976d2;
    color: #1976d2;
    padding: 6px 12px;
    border-radius: 20px;
    cursor: pointer;
    font-weight: bold;
    font-size: 0.85em;
    transition: 0.2s;
}

.btn-toggle-deposito:hover {
    background: #1976d2;
    color: white;
}

.form-crear-cobro {
    background: white;
    padding: 15px;
    border-radius: 8px;
    border: 1px dashed #f57c00;
    margin-top: 15px;
}

.form-prorrateo {
    background: white;
    padding: 15px;
    border-radius: 8px;
    border: 1px dashed #2e7d32;
}

/* 📊 TARJETAS FONDOS POR RENDIR */
.tarjeta-fondo-rendir {
    background: white;
    border: 2px solid #e1bee7;
    border-radius: 8px;
    padding: 15px;
    margin-bottom: 12px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    box-shadow: 0 2px 5px rgba(0, 0, 0, 0.03);
    transition: transform 0.2s, box-shadow 0.2s;
}

.tarjeta-fondo-rendir:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 10px rgba(0, 0, 0, 0.08);
    border-color: #ce93d8;
}

.btn-rendir {
    background-color: #8e24aa;
    font-size: 0.9em;
    padding: 8px 12px;
}

.btn-rendir:hover {
    background-color: #6a1b9a;
}

.grupo-inputs-cobro {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 10px;
}

.campo {
    display: flex;
    flex-direction: column;
}

.campo label {
    font-weight: bold;
    margin-bottom: 5px;
    font-size: 0.85em;
    color: #555;
}

.campo input,
.campo select {
    padding: 8px;
    border: 1px solid #ccc;
    border-radius: 4px;
    width: 100%;
    box-sizing: border-box;
}

.btn-guardar-cobro {
    background: #f57c00;
    color: white;
    border: none;
    padding: 10px 20px;
    border-radius: 4px;
    font-weight: bold;
    cursor: pointer;
}

.select-grande {
    padding: 10px;
    border: 2px solid #ffcc80;
    border-radius: 6px;
    font-size: 1em;
    background: white;
}

.btn-masivo {
    background-color: #e65100;
    color: white;
    border: none;
    padding: 12px 20px;
    border-radius: 6px;
    font-weight: bold;
    cursor: pointer;
    font-size: 1em;
    transition: 0.2s;
}

.btn-masivo:hover {
    background-color: #d84315;
    transform: translateY(-2px);
}

.btn-masivo:disabled {
    background-color: #bdbdbd;
    cursor: not-allowed;
    transform: none;
}

.btn-prorratear {
    background-color: #2e7d32;
}

.btn-prorratear:hover {
    background-color: #1b5e20;
}

/* 👇 ESTILO CLICK PARA MOSTRAR BENEFICIARIOS */
.caja-clickeable-ahorro {
    background: white;
    border: 1px solid #bbdefb;
    padding: 10px;
    border-radius: 6px;
    margin-top: 15px;
    cursor: pointer;
    transition: background 0.2s;
}

.caja-clickeable-ahorro:hover {
    background-color: #e3f2fd;
}

.lista-nombres-ahorro {
    background: white;
    border: 1px solid #bbdefb;
    border-radius: 6px;
    padding: 10px;
    max-height: 140px;
    overflow-y: auto;
    margin-top: 10px;
}

.nombre-mini {
    font-size: 0.85em;
    padding: 4px 0;
    border-bottom: 1px dashed #eee;
    color: #34495e;
}

.nombre-mini:last-child {
    border-bottom: none;
}

/* 👥 LISTA CHECKBOXES ALUMNOS */
.caja-checkboxes {
    background: white;
    border: 1px solid #ccc;
    border-radius: 8px;
    overflow: hidden;
    margin-top: 5px;
}

.checkbox-item {
    padding: 10px 15px;
    border-bottom: 1px solid #eee;
    display: flex;
    align-items: center;
    gap: 10px;
    cursor: pointer;
}

.checkbox-item.todos {
    background: #f0f4f8;
    border-bottom: none;
}

.checkbox-item.individual:hover {
    background: #f9f9f9;
}

.checkbox-item input {
    transform: scale(1.2);
    cursor: pointer;
}

.checkbox-item label {
    cursor: pointer;
    flex-grow: 1;
    user-select: none;
}

/* 👇 BOTÓN PARA OCULTAR/MOSTRAR */
.toggle-lista {
    background: #f8fbff;
    border-top: 1px solid #eee;
    border-bottom: 1px solid #eee;
    padding: 10px 15px;
    text-align: center;
    cursor: pointer;
    color: #3498db;
    transition: background 0.2s;
}

.toggle-lista:hover {
    background: #eef5fa;
}

.toggle-lista span {
    font-weight: bold;
    font-size: 0.9em;
}

/* 👇 LISTA EN 1 COLUMNA */
.lista-alumnos-check {
    max-height: 300px;
    overflow-y: auto;
    background: white;
    display: flex;
    flex-direction: column;
}

.selector {
    margin-bottom: 20px;
    padding: 15px;
    background: #f0f4f8;
    border-radius: 8px;
    border-left: 5px solid #3498db;
}

.selector label {
    font-weight: bold;
    margin-right: 15px;
}

.selector select {
    padding: 8px;
    width: 100%;
    max-width: 400px;
    font-size: 1em;
    border-radius: 5px;
    border: 1px solid #bdc3c7;
}

.mesa-trabajo-contenedor {
    display: flex;
    flex-direction: column;
    gap: 30px;
}

.mesa-trabajo {
    display: flex;
    gap: 20px;
    flex-wrap: wrap;
    align-items: flex-start;
}

.columna {
    padding: 20px;
    border-radius: 8px;
    background: #f9f9f9;
    border: 1px solid #eee;
}

.columna.fondos {
    flex: 1;
    min-width: 280px;
}

.columna.accion {
    flex: 1;
    min-width: 250px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: transparent;
    border: none;
}

.columna.deudas {
    flex: 1.5;
    min-width: 360px;
}

.titulo-con-accion {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 15px;
}

.titulo-con-accion h3 {
    margin: 0;
}

.tarjeta-billetera {
    background: #34495e;
    color: white;
    padding: 20px;
    border-radius: 12px;
    text-align: center;
    margin-bottom: 15px;
    box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
}

.tarjeta-billetera small {
    text-transform: uppercase;
    font-size: 0.8em;
    opacity: 0.8;
}

.tarjeta-billetera h2 {
    margin: 5px 0 0 0;
    font-size: 2.2em;
    color: #2ecc71;
}

.info-apoderado {
    background: #e8f4f8;
    border-left: 4px solid #3498db;
    padding: 10px 15px;
    border-radius: 0 8px 8px 0;
    margin-bottom: 20px;
    color: #2c3e50;
}

.info-apoderado span {
    font-size: 1.1em;
    display: block;
    margin-top: 3px;
}

.btn-mini {
    background: #3498db;
    color: white;
    border: none;
    padding: 6px 12px;
    border-radius: 4px;
    cursor: pointer;
    font-size: 0.8em;
    font-weight: bold;
}

.form-rapido {
    background: #e3f2fd;
    padding: 15px;
    border-radius: 8px;
    margin-bottom: 15px;
    display: flex;
    flex-direction: column;
    gap: 10px;
    border: 1px solid #90caf9;
}

.form-rapido input {
    padding: 8px;
    border: 1px solid #ccc;
    border-radius: 4px;
}

.btn-guardar-mini {
    background: #27ae60;
    color: white;
    border: none;
    padding: 10px;
    border-radius: 4px;
    cursor: pointer;
    font-weight: bold;
}

.item-lista {
    background: white;
    padding: 12px;
    margin-bottom: 8px;
    border-radius: 6px;
    border: 1px solid #e0e0e0;
}

.flex-row {
    display: flex;
    justify-content: space-between;
    margin-bottom: 5px;
}

.align-center {
    align-items: center;
}

.btn-eliminar-abono {
    background: none;
    border: none;
    color: #e74c3c;
    cursor: pointer;
    font-size: 1.1em;
    opacity: 0.7;
    transition: 0.2s;
}

.btn-eliminar-abono:hover {
    opacity: 1;
    transform: scale(1.1);
}

.caja-imputar {
    background: #2c3e50;
    color: white;
    padding: 25px;
    border-radius: 12px;
    text-align: center;
    width: 100%;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
}

.caja-imputar h4 {
    margin-top: 0;
}

.resumen-pago {
    background: rgba(255, 255, 255, 0.1);
    padding: 10px;
    border-radius: 8px;
    text-align: left;
}

.resumen-pago p {
    margin: 5px 0;
    display: flex;
    justify-content: space-between;
}

.mt-2 {
    margin-top: 10px;
}

.btn-guardar {
    background: #27ae60;
    color: white;
    border: none;
    padding: 15px;
    border-radius: 8px;
    font-weight: bold;
    cursor: pointer;
    width: 100%;
    font-size: 1.1em;
    margin-top: 20px;
    transition: 0.3s;
}

.btn-guardar:hover {
    background: #219150;
    transform: scale(1.02);
}

.disabled-btn {
    background: #95a5a6;
    cursor: not-allowed;
}

.esperando {
    text-align: center;
    color: #95a5a6;
    font-style: italic;
    background: #f8f9fa;
    padding: 30px;
    border-radius: 12px;
    border: 2px dashed #bdc3c7;
}

.columna.deudas h3 {
    margin-top: 0;
}

.tabla-deudas {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.9em;
    background: white;
    border-radius: 8px;
    overflow: hidden;
}

.tabla-deudas th {
    background: #34495e;
    color: white;
    padding: 12px;
    text-align: left;
}

.tabla-deudas td {
    padding: 12px;
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
    color: #e74c3c;
    font-weight: bold;
    font-size: 1.1em;
}

.texto-verde {
    color: #27ae60;
    font-weight: bold;
    font-size: 1.1em;
}

.badge-estado {
    display: inline-block;
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 0.75em;
    margin-top: 4px;
    color: white;
    font-weight: bold;
}

.badge-estado.PENDIENTE {
    background: #e74c3c;
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
    padding: 6px 10px;
    transition: 0.2s;
}

.btn-reversar {
    background: #fff3e0;
    border: 1px solid #ffb74d;
    color: #e65100;
    border-radius: 4px;
    cursor: pointer;
    padding: 6px 10px;
    font-size: 0.85em;
    font-weight: bold;
}

.hint {
    color: #95a5a6;
    font-style: italic;
    font-size: 0.9em;
}

.auditoria-contenedor {
    background: white;
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    padding: 25px;
    margin-top: 10px;
    box-shadow: 0 4px 10px rgba(0, 0, 0, 0.03);
}

.auditoria-contenedor h3 {
    margin: 0;
    color: #2c3e50;
    border-bottom: 2px solid #eee;
    padding-bottom: 10px;
}

.tabla-auditoria {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.95em;
    margin-top: 15px;
}

.tabla-auditoria th {
    background: #f8f9fa;
    padding: 12px;
    text-align: left;
    border-bottom: 2px solid #ddd;
    color: #555;
}

.tabla-auditoria td {
    padding: 12px;
    border-bottom: 1px solid #eee;
}

.badge-tipo {
    padding: 4px 8px;
    border-radius: 12px;
    font-size: 0.8em;
    font-weight: bold;
}

.badge-tipo.INGRESO {
    background: #e8f5e9;
    color: #2e7d32;
    border: 1px solid #c8e6c9;
}

.badge-tipo.EGRESO {
    background: #ffebee;
    color: #c62828;
    border: 1px solid #ffcdd2;
}

/* === RESPONSIVO PARA LA GRILLA === */
@media (max-width: 1100px) {
    .zona-masiva-grid {
        grid-template-columns: repeat(2, 1fr);
    }

    .span-2-cols {
        grid-column: span 2;
    }
}

@media (max-width: 768px) {
    .zona-masiva-grid {
        grid-template-columns: 1fr;
    }

    .span-2-cols {
        grid-column: span 1;
    }
}
</style>