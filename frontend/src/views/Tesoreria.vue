<script setup>
import { ref, onMounted, computed } from 'vue'
import api from '../axios'

// === ESTADO DE DATOS ===
const alumnos = ref([])
const conceptos = ref([])
const egresos = ref([])
const movimientosRaw = ref([])
const deposito = ref({ monto: 0 })
const cargando = ref(true)

// === CARGA DE DATOS ===
const cargarTodo = async () => {
    cargando.value = true
    try {
        const [resAlumnos, resConceptos, resEgresos, resDeposito, resMovimientos] = await Promise.all([
            api.get('mis-alumnos/'),
            api.get('conceptos/'),
            api.get('egresos/'),
            api.get('deposito/'),
            api.get('movimientos/')
        ])
        alumnos.value = resAlumnos.data
        conceptos.value = resConceptos.data
        egresos.value = resEgresos.data
        movimientosRaw.value = resMovimientos.data.results || resMovimientos.data
        if (resDeposito.data && resDeposito.data.monto) deposito.value = resDeposito.data
    } catch (error) {
        console.error("Error cargando la auditoría", error)
    } finally {
        cargando.value = false
    }
}

onMounted(() => { cargarTodo() })

// === MATEMÁTICAS EXACTAS DE LOS 3 BALDES ===

const calcularRecaudacionConcepto = (conceptoId) => {
    let total = 0
    alumnos.value.forEach(al => {
        if (al.cargos) {
            const cargo = al.cargos.find(c => c.concepto === conceptoId && c.estado === 'PAGADO')
            if (cargo) total += cargo.monto_total
        }
    })
    return total
}

// 🪣 BALDE 1: Billeteras (Sin asignar)
const totalBalde1 = computed(() => alumnos.value.reduce((sum, al) => sum + (al.cuenta?.saldo_disponible || 0), 0))
const alumnosConBilletera = computed(() => alumnos.value.filter(al => (al.cuenta?.saldo_disponible || 0) > 0))

// 🪣 BALDE 2: Fondo del Curso (Cuenta)
const conceptosCuenta = computed(() => conceptos.value.filter(c => c.destino === 'CUENTA'))
const totalAhorroBase = computed(() => alumnos.value.reduce((sum, al) => sum + (al.cuenta?.cuenta_ahorro || 0), 0))
const totalBalde2 = computed(() => {
    const recaudadoCuotas = conceptosCuenta.value.reduce((sum, c) => sum + calcularRecaudacionConcepto(c.id), 0)
    return recaudadoCuotas + totalAhorroBase.value
})

// 🪣 BALDE 3: Externos (Vivos y Rendidos)
const conceptosExternosVivos = computed(() => conceptos.value.filter(c => c.destino === 'EXTERNO' && c.estado_fondo !== 'RENDIDO'))
const conceptosExternosRendidos = computed(() => conceptos.value.filter(c => c.destino === 'EXTERNO' && c.estado_fondo === 'RENDIDO'))

const totalBalde3Vivos = computed(() => conceptosExternosVivos.value.reduce((sum, c) => sum + calcularRecaudacionConcepto(c.id), 0))

// 🏦 BANCO REAL (La suma exacta de los fondos vivos)
const saldoBancoReal = computed(() => totalBalde1.value + totalBalde2.value + totalBalde3Vivos.value)

// === AGRUPACIÓN DE PRORRATEOS ===
const prorrateos = computed(() => {
    const grupos = {}
    movimientosRaw.value.forEach(mov => {
        if (!mov.fecha || !mov.descripcion) return
        const fechaCorta = mov.fecha.split('T')[0]
        const key = `${fechaCorta}_${mov.descripcion}_${mov.tipo}`
        if (!grupos[key]) {
            grupos[key] = { id: key, fecha: fechaCorta, descripcion: mov.descripcion, tipo: mov.tipo, monto_total: 0, alumnos_count: 0 }
        }
        grupos[key].monto_total += parseFloat(mov.monto)
        grupos[key].alumnos_count += 1
    })
    return Object.values(grupos).filter(g => g.alumnos_count > 1).sort((a, b) => new Date(b.fecha) - new Date(a.fecha))
})

const prorrateosIngreso = computed(() => prorrateos.value.filter(p => p.tipo === 'INGRESO'))
const prorrateosEgreso = computed(() => prorrateos.value.filter(p => p.tipo === 'EGRESO'))

const formatearDinero = (valor) => new Intl.NumberFormat('es-CL', { style: 'currency', currency: 'CLP' }).format(valor || 0)

const montoPagadoPorAlumno = (alumno, conceptoId) => {
    if (!alumno.cargos) return 0
    const cargo = alumno.cargos.find(c => c.concepto === conceptoId && c.estado === 'PAGADO')
    return cargo ? cargo.monto_total : 0
}
</script>

<template>
    <div class="dashboard-contenedor">

        <div class="header-titulos">
            <h1 class="titulo-main">📊 Auditoría General del Curso</h1>
            <p class="subtitulo">Transparencia financiera en tiempo real.</p>
        </div>

        <div v-if="cargando" class="loading">Auditando bóvedas... 🏦</div>

        <div v-else>
            <div class="fila-banco-vip">
                <div class="tarjeta-banco">
                    <div class="icono-banco">🏛️</div>
                    <div class="info-banco">
                        <span>SALDO FÍSICO EN BANCO</span>
                        <h2>{{ formatearDinero(saldoBancoReal) }}</h2>
                        <small>Suma exacta de Billeteras + Cuenta + Externos sin rendir.</small>
                    </div>
                </div>
                <div v-if="deposito.monto > 0" class="tarjeta-deposito">
                    <div class="icono-banco">🔒</div>
                    <div class="info-banco">
                        <span>DEPÓSITO A PLAZO</span>
                        <h2>{{ formatearDinero(deposito.monto) }}</h2>
                        <small>Fondo de ahorro protegido (Aparte).</small>
                    </div>
                </div>
            </div>

            <div class="auditoria-grid">

                <div class="columna columna-ingresos">
                    <div class="header-seccion verde">
                        <h2>🟢 FONDOS Y PATRIMONIO</h2>
                        <h3>{{ formatearDinero(saldoBancoReal) }}</h3>
                    </div>

                    <div class="categoria-bloque">
                        <h4 class="titulo-cat">📁 Fondo del Curso (Cuenta)</h4>
                        <details class="acordeon-excel" v-for="concepto in conceptosCuenta" :key="concepto.id">
                            <summary class="fila-resumen">
                                <span>{{ concepto.nombre }}</span>
                                <strong class="texto-verde">{{ formatearDinero(calcularRecaudacionConcepto(concepto.id))
                                    }}</strong>
                            </summary>
                            <div class="detalle-excel">
                                <table>
                                    <tbody>
                                        <tr v-for="al in alumnos" :key="al.id">
                                            <td>{{ al.numero_lista }}. {{ al.nombre_completo }}</td>
                                            <td style="text-align: right; font-weight: bold;"
                                                :class="montoPagadoPorAlumno(al, concepto.id) > 0 ? 'texto-verde' : 'texto-gris'">
                                                {{ formatearDinero(montoPagadoPorAlumno(al, concepto.id)) }}
                                            </td>
                                        </tr>
                                    </tbody>
                                </table>
                            </div>
                        </details>
                        <div class="fila-resumen flotante" style="margin-top: 5px;"
                            title="Es la suma de los premios ganados menos los gastos compartidos.">
                            <span>Ajustes y Prorrateos Históricos</span>
                            <strong :class="totalAhorroBase >= 0 ? 'texto-verde' : 'texto-rojo'">{{
                                formatearDinero(totalAhorroBase) }}</strong>
                        </div>
                    </div>

                    <div class="categoria-bloque">
                        <h4 class="titulo-cat">🎟️ Fondos Externos (En Recaudación)</h4>
                        <details class="acordeon-excel" v-for="concepto in conceptosExternosVivos" :key="concepto.id">
                            <summary class="fila-resumen">
                                <span>{{ concepto.nombre }}</span>
                                <strong class="texto-verde">{{ formatearDinero(calcularRecaudacionConcepto(concepto.id))
                                    }}</strong>
                            </summary>
                            <div class="detalle-excel">
                                <table>
                                    <tbody>
                                        <tr v-for="al in alumnos" :key="al.id">
                                            <td>{{ al.numero_lista }}. {{ al.nombre_completo }}</td>
                                            <td style="text-align: right; font-weight: bold;"
                                                :class="montoPagadoPorAlumno(al, concepto.id) > 0 ? 'texto-verde' : 'texto-gris'">
                                                {{ formatearDinero(montoPagadoPorAlumno(al, concepto.id)) }}
                                            </td>
                                        </tr>
                                    </tbody>
                                </table>
                            </div>
                        </details>
                        <div v-if="conceptosExternosVivos.length === 0" class="hint">No hay fondos externos
                            recaudándose.</div>
                    </div>

                    <div class="categoria-bloque">
                        <h4 class="titulo-cat">👛 Billeteras (Saldos sin asignar)</h4>
                        <details class="acordeon-excel">
                            <summary class="fila-resumen flotante">
                                <span>Saldos a favor disponibles</span>
                                <strong class="texto-verde">{{ formatearDinero(totalBalde1) }}</strong>
                            </summary>
                            <div class="detalle-excel">
                                <table v-if="alumnosConBilletera.length > 0">
                                    <tbody>
                                        <tr v-for="al in alumnosConBilletera" :key="al.id">
                                            <td>{{ al.numero_lista }}. {{ al.nombre_completo }}</td>
                                            <td style="text-align: right; font-weight: bold;" class="texto-verde">
                                                {{ formatearDinero(al.cuenta?.saldo_disponible) }}
                                            </td>
                                        </tr>
                                    </tbody>
                                </table>
                                <p v-else class="hint" style="text-align:center; padding: 10px;">Todas las billeteras
                                    están en $0.</p>
                            </div>
                        </details>
                    </div>

                    <div class="separador-prorrateo verde">
                        <h4>📈 INGRESOS COMPARTIDOS</h4>
                        <small>Premios o ganancias que ya se sumaron a las Billeteras o la Cuenta.</small>
                    </div>
                    <div class="lista-gastos">
                        <div v-for="pro in prorrateosIngreso" :key="pro.id" class="item-gasto">
                            <div class="gasto-info">
                                <strong>{{ pro.descripcion }}</strong>
                                <small>📅 {{ pro.fecha }} | 👥 Repartido a {{ pro.alumnos_count }} alum.</small>
                            </div>
                            <strong class="texto-verde">+{{ formatearDinero(pro.monto_total) }}</strong>
                        </div>
                        <div v-if="prorrateosIngreso.length === 0" class="hint"
                            style="text-align:center; padding: 20px;">Sin ingresos extra registrados.</div>
                    </div>
                </div>

                <div class="columna columna-egresos">
                    <div class="header-seccion rojo">
                        <h2>🔴 SALIDAS Y RENDICIONES</h2>
                    </div>

                    <div class="categoria-bloque">
                        <h4 class="titulo-cat rojo">📉 Libro Oficial de Egresos</h4>
                        <div class="lista-gastos">
                            <div v-for="gasto in egresos" :key="gasto.id" class="item-gasto">
                                <div class="gasto-info">
                                    <strong>{{ gasto.descripcion }}</strong>
                                    <small>📅 {{ gasto.fecha_gasto }} | Ref: {{ gasto.comprobante || 'S/R' }}</small>
                                </div>
                                <strong class="texto-rojo">-{{ formatearDinero(gasto.monto) }}</strong>
                            </div>
                            <div v-if="egresos.length === 0" class="hint" style="text-align:center; padding: 20px;">
                                No hay salidas de dinero en el banco real.
                            </div>
                        </div>
                    </div>

                    <div class="categoria-bloque">
                        <h4 class="titulo-cat rojo">📤 Externos ya Transferidos</h4>
                        <div class="lista-gastos">
                            <div v-for="concepto in conceptosExternosRendidos" :key="concepto.id" class="item-gasto"
                                style="background: #fdfdfd;">
                                <div class="gasto-info">
                                    <strong style="color: #7f8c8d; text-decoration: line-through;">{{ concepto.nombre
                                        }}</strong>
                                    <small>Monto recaudado de los apoderados</small>
                                </div>
                                <strong class="texto-gris">{{ formatearDinero(calcularRecaudacionConcepto(concepto.id))
                                    }}</strong>
                            </div>
                            <div v-if="conceptosExternosRendidos.length === 0" class="hint"
                                style="text-align:center; padding: 20px;">
                                No hay fondos externos rendidos históricamente.
                            </div>
                        </div>
                    </div>

                    <div class="separador-prorrateo rojo">
                        <h4>📉 GASTOS COMPARTIDOS</h4>
                        <small>Gastos (Regalos, eventos) que ya se descontaron de los alumnos.</small>
                    </div>
                    <div class="lista-gastos">
                        <div v-for="pro in prorrateosEgreso" :key="pro.id" class="item-gasto">
                            <div class="gasto-info">
                                <strong>{{ pro.descripcion }}</strong>
                                <small>📅 {{ pro.fecha }} | 👥 Dividido en {{ pro.alumnos_count }} alum.</small>
                            </div>
                            <strong class="texto-rojo">-{{ formatearDinero(pro.monto_total) }}</strong>
                        </div>
                        <div v-if="prorrateosEgreso.length === 0" class="hint"
                            style="text-align:center; padding: 20px;">Sin gastos compartidos registrados.</div>
                    </div>
                </div>

            </div>
        </div>
    </div>
</template>

<style scoped>
.dashboard-contenedor {
    max-width: 1400px;
    margin: 0 auto;
    padding: 20px;
    font-family: 'Segoe UI', sans-serif;
    color: #333;
}

.header-titulos {
    text-align: center;
    margin-bottom: 30px;
}

.titulo-main {
    color: #2c3e50;
    margin-bottom: 5px;
    font-size: 2.2rem;
}

.subtitulo {
    color: #7f8c8d;
    font-size: 1.1rem;
}

.loading {
    text-align: center;
    padding: 50px;
    font-size: 1.2rem;
    color: #7f8c8d;
}

/* FILA VIP BANCO */
.fila-banco-vip {
    display: flex;
    gap: 20px;
    margin-bottom: 30px;
    justify-content: center;
    flex-wrap: wrap;
}

.tarjeta-banco,
.tarjeta-deposito {
    background: #2c3e50;
    color: white;
    border-radius: 12px;
    padding: 20px 30px;
    display: flex;
    align-items: center;
    gap: 20px;
    box-shadow: 0 8px 20px rgba(0, 0, 0, 0.15);
    min-width: 350px;
}

.tarjeta-deposito {
    background: #e8f4f8;
    color: #2c3e50;
    border: 2px solid #3498db;
}

.icono-banco {
    font-size: 3rem;
}

.info-banco span {
    font-size: 0.9rem;
    font-weight: bold;
    letter-spacing: 1px;
    opacity: 0.8;
}

.info-banco h2 {
    margin: 5px 0;
    font-size: 2.5rem;
}

.info-banco small {
    font-size: 0.8rem;
    opacity: 0.7;
}

/* GRID COLUMNAS */
.auditoria-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 30px;
    align-items: start;
}

@media (max-width: 1000px) {
    .auditoria-grid {
        grid-template-columns: 1fr;
    }
}

.columna {
    background: white;
    border-radius: 12px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
    overflow: hidden;
    border: 1px solid #eaeaea;
}

.columna-ingresos {
    border-top: 5px solid #27ae60;
}

.columna-egresos {
    border-top: 5px solid #e74c3c;
}

/* HEADERS Y BLOQUES */
.header-seccion {
    padding: 20px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    color: white;
}

.header-seccion h2 {
    margin: 0;
    font-size: 1.2rem;
    letter-spacing: 1px;
}

.header-seccion h3 {
    margin: 0;
    font-size: 1.5rem;
}

.verde {
    background: linear-gradient(135deg, #27ae60, #2ecc71);
}

.rojo {
    background: linear-gradient(135deg, #c0392b, #e74c3c);
}

.categoria-bloque {
    padding: 15px 20px;
    border-bottom: 2px dashed #f0f0f0;
}

.titulo-cat {
    color: #34495e;
    font-size: 1.1rem;
    margin: 0 0 10px 0;
    border-left: 4px solid #3498db;
    padding-left: 10px;
}

.titulo-cat.rojo {
    border-left-color: #e74c3c;
}

/* ACORDEONES */
.acordeon-excel {
    background: #fdfdfd;
    border: 1px solid #eee;
    border-radius: 6px;
    margin-bottom: 8px;
}

.fila-resumen {
    padding: 12px 15px;
    display: flex;
    justify-content: space-between;
    cursor: pointer;
    background: #f8f9fa;
    font-weight: 500;
    font-size: 1.05rem;
    list-style: none;
    transition: background 0.2s;
    border-radius: 6px;
}

.fila-resumen:hover {
    background: #f1f3f5;
}

.fila-resumen.flotante {
    background: #e3f2fd;
    cursor: default;
}

.detalle-excel {
    border-top: 1px solid #eee;
    background: white;
    max-height: 300px;
    overflow-y: auto;
}

.detalle-excel table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.9rem;
}

.detalle-excel td {
    padding: 8px 15px;
    border-bottom: 1px solid #f5f5f5;
}

.detalle-excel tr:hover {
    background: #fdfae3;
}

/* LISTAS Y SEPARADORES */
.separador-prorrateo {
    padding: 15px 20px;
    text-align: center;
    color: white;
}

.separador-prorrateo h4 {
    margin: 0;
    font-size: 1rem;
}

.separador-prorrateo small {
    opacity: 0.9;
}

.separador-prorrateo.verde {
    background: #78c292;
}

.separador-prorrateo.rojo {
    background: #e08b84;
}

.lista-gastos {
    max-height: 400px;
    overflow-y: auto;
}

.item-gasto {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 15px 20px;
    border-bottom: 1px solid #eee;
    transition: background 0.2s;
}

.item-gasto:hover {
    background: #fffafa;
}

.gasto-info {
    display: flex;
    flex-direction: column;
}

.gasto-info small {
    color: #7f8c8d;
    font-size: 0.8rem;
    margin-top: 3px;
}

/* UTILIDADES */
.texto-verde {
    color: #27ae60;
}

.texto-rojo {
    color: #e74c3c;
}

.texto-gris {
    color: #bdc3c7;
}

.hint {
    color: #95a5a6;
    font-style: italic;
    font-size: 0.9em;
    padding: 5px 0;
}
</style>