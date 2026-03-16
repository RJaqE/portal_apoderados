<script setup>
import { ref, onMounted } from 'vue'
import api from '../axios'

const deudas = ref([])
const abonos = ref([])
const saldoBilletera = ref(0) // <--- NUEVO ESTADO
const cargando = ref(true)
const datosBancarios = ref({})

const cargarDatosFinancieros = async () => {
    cargando.value = true
    try {
        const resAlumnos = await api.get('mis-alumnos/')
        if (resAlumnos.data && resAlumnos.data.length > 0) {
            const miAlumno = resAlumnos.data[0]
            deudas.value = miAlumno.cargos || []
            abonos.value = miAlumno.abonos || []
            // 👇 NUEVO: Sacar el saldo disponible de la cuenta asociada
            saldoBilletera.value = miAlumno.cuenta?.saldo_disponible || 0
        }

        // Cargar datos bancarios para la transferencia
        const resSettings = await api.get('settings/') // Asumiendo que tenemos una API para esto
        datosBancarios.value = resSettings.data
    } catch (error) {
        console.error("Error cargando finanzas", error)
    } finally {
        cargando.value = false
    }
}

onMounted(() => { cargarDatosFinancieros() })

const formatearDinero = (val) => {
    return new Intl.NumberFormat('es-CL', { style: 'currency', currency: 'CLP' }).format(val || 0)
}
</script>

<template>
    <div class="mis-finanzas">
        <h1 class="titulo-pagina">🎓 Estado de Cuenta Individual (8°B)</h1>
        <p class="bajada">Visualiza tus deudas, pagos y el dinero disponible en tu billetera virtual.</p>

        <div v-if="cargando" class="loading">Sincronizando con tesorería... ⏳</div>

        <div v-else class="grid-finanzas">

            <div class="columna-info">
                <div class="card-blanca banco-info">
                    <div class="card-header">
                        <span class="icono-banco">🏦</span>
                        <h2>Datos para transferir a Tesorería</h2>
                    </div>
                    <div class="datos-banco-grid">
                        <div class="item-banco"><strong>Banco:</strong> {{ datosBancarios.banco || 'BancoEstado' }}
                        </div>
                        <div class="item-banco"><strong>Tipo de Cuenta:</strong> {{ datosBancarios.tipo_cuenta ||
                            'Cuenta RUT' }}</div>
                        <div class="item-banco"><strong>N° Cuenta:</strong> {{ datosBancarios.numero_cuenta ||
                            '12.345.678-9' }}</div>
                        <div class="item-banco"><strong>Nombre:</strong> {{ datosBancarios.nombre_titular || 'Tesorería Curso 8B' }}</div>
                        <div class="item-banco"><strong>RUT:</strong> {{ datosBancarios.rut || '12.345.678-9' }}</div>
                        <div class="item-banco"><strong>Correo comprobante:</strong> {{ datosBancarios.correo ||
                            'tesoreria8b@colegio.cl' }}</div>
                    </div>
                    <p class="hint-banco">Recuerda enviar el comprobante para cargar tu billetera virtual.</p>
                </div>
            </div>

            <div class="columna-movimientos">

                <div class="tarjeta-billetera">
                    <div class="billetera-header">
                        <span class="icono-billetera">👛</span>
                        <h3>Billetera Virtual Disponible</h3>
                    </div>
                    <div class="billetera-saldo">
                        <h2>{{ formatearDinero(saldoBilletera) }}</h2>
                        <p>Dinero cargado y validado por tesorería.</p>
                    </div>
                </div>

                <div class="card-blanca mov-container">
                    <h3>📄 Movimientos de Cuenta</h3>
                    <div class="tabs-movimientos">
                        <details class="acordeon-pago" open>
                            <summary>Deudas y Cargos del Curso ({{ deudas.length }})</summary>
                            <table class="tabla-movimientos">
                                <thead>
                                    <tr>
                                        <th>Concepto</th>
                                        <th>Vence</th>
                                        <th>Monto & Estado</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr v-if="deudas.length === 0">
                                        <td colspan="3" class="hint">Sin cobros registrados aún.</td>
                                    </tr>
                                    <tr v-for="deuda in deudas" :key="deuda.id">
                                        <td><strong>{{ deuda.concepto_nombre }}</strong></td>
                                        <td>{{ deuda.fecha_vencimiento }}</td>
                                        <td :class="deuda.estado === 'PAGADO' ? 'pagado' : 'pendiente'">
                                            {{ formatearDinero(deuda.monto_total) }}
                                            <span class="badge-estado">{{ deuda.estado }}</span>
                                        </td>
                                    </tr>
                                </tbody>
                            </table>
                        </details>

                        <details class="acordeon-pago">
                            <summary>Cargas de Dinero Manuales (Billetera) ({{ abonos.length }})</summary>
                            <table class="tabla-movimientos">
                                <thead>
                                    <tr>
                                        <th>Fecha</th>
                                        <th>Ref / Boleta</th>
                                        <th>Monto</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr v-if="abonos.length === 0">
                                        <td colspan="3" class="hint">No has realizado abonos manuales.</td>
                                    </tr>
                                    <tr v-for="abono in abonos" :key="abono.id">
                                        <td>{{ abono.fecha_transferencia }}</td>
                                        <td><small>{{ abono.comprobante || 'Sin Referencia' }}</small></td>
                                        <td class="monto-abono">{{ formatearDinero(abono.monto) }}</td>
                                    </tr>
                                </tbody>
                            </table>
                        </details>
                    </div>
                </div>
            </div>

        </div>
    </div>
</template>

<style scoped>
.mis-finanzas {
    max-width: 1400px;
    margin: 0 auto;
    padding: 20px;
    font-family: 'Segoe UI', sans-serif;
    color: #333;
}

.titulo-pagina {
    color: #2c3e50;
    text-align: center;
    margin-bottom: 5px;
}

.bajada {
    color: #7f8c8d;
    text-align: center;
    margin-bottom: 40px;
}

.loading {
    text-align: center;
    padding: 50px;
    font-size: 1.2rem;
    color: #7f8c8d;
}

.grid-finanzas {
    display: grid;
    grid-template-columns: 1fr 1.5fr;
    gap: 30px;
    align-items: start;
}

@media (max-width: 900px) {
    .grid-finanzas {
        grid-template-columns: 1fr;
    }
}

.card-blanca {
    background: white;
    border-radius: 12px;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
    padding: 20px;
}

/* BANCO INFO */
.card-header {
    display: flex;
    align-items: center;
    gap: 15px;
    border-bottom: 1px solid #eee;
    padding-bottom: 15px;
    margin-bottom: 15px;
}

.icono-banco {
    font-size: 2rem;
}

.card-header h2 {
    margin: 0;
    font-size: 1.3rem;
    color: #2c3e50;
}

.datos-banco-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 10px;
}

.item-banco strong {
    color: #555;
    font-size: 0.9em;
}

.item-banco {
    font-size: 0.95em;
    color: #333;
}

.hint-banco {
    margin-top: 20px;
    font-size: 0.85em;
    color: #7f8c8d;
    background: #fbfbfb;
    padding: 10px;
    border-radius: 6px;
    border: 1px solid #f0f0f0;
    text-align: center;
}

/* COLUMNA DERECHA */
.columna-movimientos {
    display: flex;
    flex-direction: column;
    gap: 30px;
}

/* BILLETERA (NUEVO ESTILO) */
.tarjeta-billetera {
    background: linear-gradient(135deg, #2c3e50, #34495e);
    color: white;
    border-radius: 12px;
    padding: 25px;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
}

.billetera-header {
    display: flex;
    align-items: center;
    gap: 15px;
    margin-bottom: 15px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    padding-bottom: 10px;
}

.billetera-header h3 {
    margin: 0;
    font-size: 1.1rem;
    text-transform: uppercase;
    letter-spacing: 1px;
}

.icono-billetera {
    font-size: 1.8rem;
}

.billetera-saldo h2 {
    font-size: 2.8rem;
    color: #2ecc71;
    margin: 0 0 5px 0;
}

.billetera-saldo p {
    margin: 0;
    opacity: 0.8;
    font-size: 0.9rem;
}

/* TABLAS Y ACORDEONES */
.mov-container h3 {
    margin-top: 0;
}

.acordeon-pago {
    border-bottom: 1px solid #eee;
    margin-bottom: 15px;
}

.acordeon-pago summary {
    font-weight: bold;
    padding: 10px;
    cursor: pointer;
    color: #3498db;
}

.acordeon-pago table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.9em;
    margin-top: 10px;
    margin-bottom: 20px;
}

.acordeon-pago th {
    text-align: left;
    padding: 8px;
    color: #7f8c8d;
    border-bottom: 2px solid #ddd;
}

.acordeon-pago td {
    padding: 10px 8px;
    border-bottom: 1px solid #f1f1f1;
}

.pendiente {
    color: #c0392b;
    font-weight: bold;
}

.pagado {
    color: #27ae60;
    font-weight: bold;
}

.badge-estado {
    display: inline-block;
    padding: 2px 6px;
    font-size: 0.7em;
    background: #ccc;
    color: white;
    border-radius: 4px;
    vertical-align: middle;
    margin-left: 5px;
}

.pagado .badge-estado {
    background: #2ecc71;
}

.pendiente .badge-estado {
    background: #e74c3c;
}

.monto-abono {
    color: #27ae60;
    font-weight: bold;
}

.hint {
    text-align: center;
    color: #95a5a6;
    padding: 20px;
    font-style: italic;
}
</style>