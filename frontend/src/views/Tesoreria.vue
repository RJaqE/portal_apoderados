<script setup>
import { ref, onMounted, computed } from 'vue'
import api from '../axios'

// === ESTADO DE DATOS ===
const alumnos = ref([])
const conceptos = ref([])
const egresos = ref([])
const movimientosRaw = ref([]) // <--- NUEVO: Para agrupar prorrateos
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
            api.get('movimientos/') // <--- NUEVO
        ])
        alumnos.value = resAlumnos.data
        conceptos.value = resConceptos.data
        egresos.value = resEgresos.data
        movimientosRaw.value = resMovimientos.data.results || resMovimientos.data

        if (resDeposito.data && resDeposito.data.monto) {
            deposito.value = resDeposito.data
        }
    } catch (error) {
        console.error("Error cargando el dashboard", error)
    } finally {
        cargando.value = false
    }
}

onMounted(() => { cargarTodo() })

// === MATEMÁTICAS Y AGRUPACIONES ===

const totalFlotante = computed(() => {
    return alumnos.value.reduce((sum, al) => sum + (al.cuenta?.saldo_disponible || 0), 0)
})
const alumnosConFlotante = computed(() => {
    return alumnos.value.filter(al => (al.cuenta?.saldo_disponible || 0) > 0)
})

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

const conceptosCuenta = computed(() => conceptos.value.filter(c => c.destino === 'CUENTA'))
const conceptosExternos = computed(() => conceptos.value.filter(c => c.destino === 'EXTERNO'))

const totalRecaudadoCuenta = computed(() => {
    return conceptosCuenta.value.reduce((sum, c) => sum + calcularRecaudacionConcepto(c.id), 0)
})
const totalRecaudadoExterno = computed(() => {
    return conceptosExternos.value.reduce((sum, c) => sum + calcularRecaudacionConcepto(c.id), 0)
})

const totalEgresos = computed(() => {
    return egresos.value.reduce((sum, e) => sum + e.monto, 0)
})

// 👇 LA MAGIA: RECONSTRUIR PRORRATEOS GLOBALES
const historialProrrateos = computed(() => {
    const grupos = {}

    movimientosRaw.value.forEach(mov => {
        // Ignoramos movimientos sin fecha o descripción
        if (!mov.fecha || !mov.descripcion) return

        const fechaCorta = mov.fecha.split('T')[0]
        // Creamos una "llave" única basada en Fecha + Descripción + Tipo
        const key = `${fechaCorta}_${mov.descripcion}_${mov.tipo}`

        if (!grupos[key]) {
            grupos[key] = {
                id: key,
                fecha: fechaCorta,
                descripcion: mov.descripcion,
                tipo: mov.tipo,
                monto_total: 0,
                alumnos_count: 0
            }
        }
        grupos[key].monto_total += parseFloat(mov.monto)
        grupos[key].alumnos_count += 1
    })

    // Convertimos a array, filtramos solo los que afectaron a > 1 alumno (Prorrateos reales) 
    // y ordenamos por fecha descendente
    return Object.values(grupos)
        .filter(g => g.alumnos_count > 1)
        .sort((a, b) => new Date(b.fecha) - new Date(a.fecha))
})

const granTotalIngresos = computed(() => totalRecaudadoCuenta.value + totalRecaudadoExterno.value + totalFlotante.value)
const saldoBancoReal = computed(() => granTotalIngresos.value - totalEgresos.value)

const formatearDinero = (valor) => new Intl.NumberFormat('es-CL', { style: 'currency', currency: 'CLP' }).format(valor || 0)

const montoPagadoPorAlumno = (alumno, conceptoId) => {
    if (!alumno.cargos) return 0
    const cargo = alumno.cargos.find(c => c.concepto === conceptoId && c.estado === 'PAGADO')
    return cargo ? cargo.monto_total : 0
}
</script>

<template>
    <div class="dashboard-contenedor">
        <h1 class="titulo-main">📊 Flujo de Caja y Resumen Bancario</h1>
        <p class="subtitulo">Auditoría en tiempo real del dinero físico en la cuenta del curso.</p>

        <div v-if="cargando" class="loading">Auditando bóvedas... 🏦</div>

        <div v-else class="auditoria-grid">

            <div class="columna ingresos">
                <div class="header-seccion verde">
                    <h2>🟢 INGRESOS RECAUDADOS</h2>
                    <h3>{{ formatearDinero(granTotalIngresos) }}</h3>
                </div>

                <div class="categoria-bloque">
                    <h4 class="titulo-cat">📁 Fondos del Curso (Cuotas, Salidas)</h4>
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
                                            :class="montoPagadoPorAlumno(al, concepto.id) > 0 ? 'texto-verde' : 'texto-rojo'">
                                            {{ formatearDinero(montoPagadoPorAlumno(al, concepto.id)) }}
                                        </td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </details>
                    <div v-if="conceptosCuenta.length === 0" class="hint">No hay cobros de esta categoría.</div>
                </div>

                <div class="categoria-bloque">
                    <h4 class="titulo-cat">📁 Aportes Extra (Solidario, Rifas)</h4>
                    <details class="acordeon-excel" v-for="concepto in conceptosExternos" :key="concepto.id">
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
                                            :class="montoPagadoPorAlumno(al, concepto.id) > 0 ? 'texto-verde' : 'texto-rojo'">
                                            {{ formatearDinero(montoPagadoPorAlumno(al, concepto.id)) }}
                                        </td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </details>
                    <div v-if="conceptosExternos.length === 0" class="hint">No hay cobros de esta categoría.</div>
                </div>

                <div class="categoria-bloque">
                    <h4 class="titulo-cat">👛 Dinero Flotante (Saldos a favor)</h4>
                    <details class="acordeon-excel">
                        <summary class="fila-resumen flotante">
                            <span>Saldos en Billeteras</span>
                            <strong class="texto-verde">{{ formatearDinero(totalFlotante) }}</strong>
                        </summary>
                        <div class="detalle-excel">
                            <table v-if="alumnosConFlotante.length > 0">
                                <tbody>
                                    <tr v-for="al in alumnosConFlotante" :key="al.id">
                                        <td>{{ al.numero_lista }}. {{ al.nombre_completo }}</td>
                                        <td style="text-align: right; font-weight: bold;" class="texto-verde">
                                            {{ formatearDinero(al.cuenta?.saldo_disponible) }}
                                        </td>
                                    </tr>
                                </tbody>
                            </table>
                            <p v-else class="hint" style="text-align:center; padding: 10px;">Todas las billeteras están
                                en $0.</p>
                        </div>
                    </details>
                </div>
            </div>

            <div class="columna-derecha-grid">

                <div class="columna prorrateos">
                    <div class="header-seccion gris">
                        <h2>🔄 PRORRATEOS Y FONDOS COMPARTIDOS</h2>
                    </div>
                    <div class="info-prorrateo-banner">
                        <small>Estos movimientos ya están sumados/restados en las Billeteras.</small>
                    </div>

                    <div class="lista-gastos">
                        <div v-for="pro in historialProrrateos" :key="pro.id" class="item-gasto">
                            <div class="gasto-info">
                                <strong>{{ pro.descripcion }}</strong>
                                <small>📅 {{ pro.fecha }} | 👥 Dividido en {{ pro.alumnos_count }} alumnos</small>
                            </div>
                            <strong :class="pro.tipo === 'INGRESO' ? 'texto-verde' : 'texto-rojo'">
                                {{ pro.tipo === 'INGRESO' ? '+' : '-' }}{{ formatearDinero(pro.monto_total) }}
                            </strong>
                        </div>
                        <div v-if="historialProrrateos.length === 0" class="hint"
                            style="text-align:center; padding: 20px;">
                            No se han realizado repartos de dinero masivos.
                        </div>
                    </div>
                </div>

                <div class="columna egresos">
                    <div class="header-seccion rojo">
                        <h2>🔴 GASTOS DIRECTOS (SIN PRORRATEO)</h2>
                        <h3>-{{ formatearDinero(totalEgresos) }}</h3>
                    </div>

                    <div class="lista-gastos">
                        <div v-for="gasto in egresos" :key="gasto.id" class="item-gasto">
                            <div class="gasto-info">
                                <strong>{{ gasto.descripcion }}</strong>
                                <small>📅 {{ gasto.fecha_gasto }} | Ref: {{ gasto.comprobante || 'S/R' }}</small>
                            </div>
                            <strong class="texto-rojo">-{{ formatearDinero(gasto.monto) }}</strong>
                        </div>
                        <div v-if="egresos.length === 0" class="hint" style="text-align:center; padding: 20px;">
                            No se han registrado salidas de dinero directas.
                        </div>
                    </div>
                </div>

                <div class="columna resumen-final">
                    <div class="header-seccion azul">
                        <h2>🏦 RESUMEN BANCO REAL</h2>
                    </div>

                    <div class="matematica-final">
                        <div class="linea-math">
                            <span>Ingresos Recaudados</span>
                            <span>{{ formatearDinero(granTotalIngresos) }}</span>
                        </div>
                        <div class="linea-math">
                            <span>Gastos Directos</span>
                            <span class="texto-rojo">-{{ formatearDinero(totalEgresos) }}</span>
                        </div>
                        <hr class="linea-suma" />
                        <div class="linea-math total-banco">
                            <span>SALDO EXACTO EN BANCO:</span>
                            <span :class="saldoBancoReal >= 0 ? 'texto-azul' : 'texto-rojo'">
                                {{ formatearDinero(saldoBancoReal) }}
                            </span>
                        </div>
                    </div>

                    <div v-if="deposito.monto > 0" class="tarjeta-deposito">
                        <span class="icono-deposito">🔒</span>
                        <div>
                            <small>Plata en Depósito a Plazo (Aparte)</small>
                            <h4>{{ formatearDinero(deposito.monto) }}</h4>
                        </div>
                    </div>
                </div>

            </div>
        </div>
    </div>
</template>

<style scoped>
/* TODO ESTILO SE MANTIENE EXACTAMENTE IGUAL, SOLO AGREGAMOS EL BANNER GRIS */
.dashboard-contenedor {
    max-width: 1400px;
    margin: 0 auto;
    padding: 20px;
    font-family: 'Segoe UI', sans-serif;
    color: #333;
}

.titulo-main {
    text-align: center;
    color: #2c3e50;
    margin-bottom: 5px;
    font-size: 2.2rem;
}

.subtitulo {
    text-align: center;
    color: #7f8c8d;
    margin-bottom: 30px;
    font-size: 1.1rem;
}

.loading {
    text-align: center;
    padding: 50px;
    font-size: 1.2rem;
    color: #7f8c8d;
}

.auditoria-grid {
    display: grid;
    grid-template-columns: 1.2fr 1fr;
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

.columna-derecha-grid {
    display: flex;
    flex-direction: column;
    gap: 30px;
}

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

.azul {
    background: linear-gradient(135deg, #2c3e50, #34495e);
    justify-content: center;
}

.gris {
    background: linear-gradient(135deg, #7f8c8d, #95a5a6);
    justify-content: center;
}

/* NUEVO */
.info-prorrateo-banner {
    background: #fdfdfd;
    padding: 10px;
    text-align: center;
    border-bottom: 1px solid #eee;
    color: #7f8c8d;
}

/* NUEVO */
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
}

.fila-resumen:hover {
    background: #f1f3f5;
}

.fila-resumen.flotante {
    background: #e3f2fd;
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

.texto-verde {
    color: #27ae60;
}

.texto-rojo {
    color: #e74c3c;
}

.texto-azul {
    color: #2980b9;
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

.resumen-final {
    background: #f8fbff;
    border: 2px solid #b8daff;
}

.matematica-final {
    padding: 30px 40px;
    font-size: 1.2rem;
}

.linea-math {
    display: flex;
    justify-content: space-between;
    margin-bottom: 15px;
    color: #34495e;
}

.linea-suma {
    border: 0;
    height: 2px;
    background: #34495e;
    margin: 20px 0;
}

.total-banco {
    font-size: 1.6rem;
    font-weight: 900;
}

.tarjeta-deposito {
    background: #e8f4f8;
    margin: 0 20px 20px 20px;
    padding: 15px;
    border-radius: 8px;
    border-left: 5px solid #3498db;
    display: flex;
    align-items: center;
    gap: 15px;
}

.icono-deposito {
    font-size: 2rem;
}

.tarjeta-deposito h4 {
    margin: 5px 0 0 0;
    color: #2c3e50;
    font-size: 1.3rem;
}

.hint {
    color: #95a5a6;
    font-style: italic;
    font-size: 0.9em;
    padding: 5px 0;
}
</style>