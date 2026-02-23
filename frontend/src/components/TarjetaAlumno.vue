<script setup>
// Recibimos los datos y las funciones desde el padre (MisFinanzas)
const props = defineProps(['alumno'])

// Definimos las funciones de formato AQUÍ MISMO para que el componente sea independiente
const formatoDinero = (valor) => {
    return new Intl.NumberFormat('es-CL', { style: 'currency', currency: 'CLP' }).format(valor)
}

const formatoFecha = (fecha) => {
    if (!fecha) return 'Sin fecha'
    return new Date(fecha).toLocaleDateString('es-CL', { day: 'numeric', month: 'short' })
}

const filtrarCargos = (listaCargos, tipo) => {
    if (!listaCargos) return []
    return listaCargos.filter(c => c.concepto_tipo === tipo).sort((a, b) => new Date(a.fecha_vencimiento) - new Date(b.fecha_vencimiento))
}
</script>

<template>
    <div class="tarjeta-contenido">
        <div class="card-header">
            <div class="header-info">
                <h2>{{ alumno.nombre_completo }}</h2>
                <span class="badge-curso">{{ alumno.curso }}</span>
            </div>
            <div class="caja-saldo" :class="{ 'negativo': alumno.saldo_a_favor < 0 }">
                <span class="label-saldo">Estado de cuenta:</span>
                <span class="monto-saldo">{{ formatoDinero(alumno.saldo_a_favor) }}</span>
            </div>
        </div>

        <div class="contenedor-dashboard">
            <div class="columna-lateral">
                <div class="seccion-lateral azul">
                    <h3>🏦 Últimas Transferencias</h3>
                    <div class="lista-pagos">
                        <div v-if="alumno.abonos.length === 0" class="texto-vacio">Sin registros recientes.</div>
                        <div v-else v-for="abono in alumno.abonos.slice(0, 3)" :key="abono.id" class="item-pago">
                            <div class="pago-icono">🧾</div>
                            <div class="pago-info">
                                <span class="pago-fecha">{{ formatoFecha(abono.fecha_pago) }}</span>
                                <small class="pago-id">ID: {{ abono.comprobante || '--' }}</small>
                            </div>
                            <div class="pago-monto">+{{ formatoDinero(abono.monto_recibido) }}</div>
                        </div>
                    </div>
                </div>

                <div class="seccion-lateral">
                    <h3>🎉 Eventos y Extras</h3>
                    <div v-if="filtrarCargos(alumno.cargos, 'EXTRA').length > 0" class="lista-extras">
                        <div v-for="cargo in filtrarCargos(alumno.cargos, 'EXTRA')" :key="cargo.id" class="item-extra"
                            :class="cargo.estado">
                            <div class="extra-info">
                                <strong>{{ cargo.concepto_nombre }}</strong>
                                <small>{{ formatoFecha(cargo.fecha_vencimiento) }}</small>
                            </div>
                            <div class="extra-monto-box">
                                <span class="extra-valor">{{ formatoDinero(cargo.monto_total) }}</span>
                                <span class="badge-estado" :class="cargo.estado">{{ cargo.estado }}</span>
                            </div>
                        </div>
                    </div>
                    <p v-else class="texto-vacio">Sin cobros extra.</p>
                </div>
            </div>

            <div class="columna-principal">
                <div class="seccion-interna">
                    <h3>📅 Cuotas Mensuales</h3>
                    <div v-if="filtrarCargos(alumno.cargos, 'MENSUALIDAD').length > 0" class="lista-mensualidades">
                        <div v-for="cargo in filtrarCargos(alumno.cargos, 'MENSUALIDAD')" :key="cargo.id"
                            class="renglon-cuota" :class="cargo.estado">
                            <div class="celda-concepto">
                                <span class="nombre-concepto">{{ cargo.concepto_nombre }}</span>
                                <small class="vence">Vence: {{ formatoFecha(cargo.fecha_vencimiento) }}</small>
                            </div>

                            <div class="celda-progreso">
                                <div class="barra-fondo">
                                    <div class="barra-relleno"
                                        :style="{ width: (cargo.monto_pagado / cargo.monto_total * 100) + '%' }"
                                        :class="cargo.estado"></div>
                                </div>
                            </div>

                            <div class="celda-estado">
                                <span class="badge-estado" :class="cargo.estado">{{ cargo.estado === 'PENDIENTE' ? 'Por Pagar' : cargo.estado }}</span>
                            </div>

                            <div class="celda-monto">
                                <strong>{{ formatoDinero(cargo.monto_total) }}</strong>
                                <small v-if="cargo.monto_pagado > 0 && cargo.estado !== 'PAGADO'"
                                    class="pagado-parcial">Abonado: {{ formatoDinero(cargo.monto_pagado) }}</small>
                            </div>
                        </div>
                    </div>
                    <p v-else class="texto-vacio">¡Todo al día! 🌟</p>
                </div>
            </div>
        </div>
    </div>
</template>

<style scoped>
/* === 1. HEADER FIJO (STICKY - VERSIÓN PC) === */
.card-header {
    background: #f8f9fa;
    padding: 20px 30px;
    border-bottom: 1px solid #eee;

    /* Bordes redondos solo arriba */
    border-radius: 12px 12px 0 0;

    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 15px;

    /* LA MAGIA STICKY */
    position: sticky;
    top: 60px;
    /* Altura del Navbar en PC */
    z-index: 20;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
}

/* === 2. AJUSTE PARA MÓVIL (SOBRESCRIBE LO DE ARRIBA) === */
@media (max-width: 900px) {
    .card-header {
        /* En móvil, el navbar suele ser un poco más chico o queremos que tope distinto */
        top: 55px;
        padding: 15px 20px;
    }

    .header-info h2 {
        font-size: 1.2em;
        /* Texto un poco más chico en móvil */
    }

    /* Ajuste de columnas para que no se rompa el layout */
    .contenedor-dashboard {
        flex-direction: column;
    }

    .columna-lateral,
    .columna-principal {
        flex: 100%;
        border-right: none;
    }

    /* Ajuste del Renglón de Cuotas en Móvil */
    .renglon-cuota {
        grid-template-columns: 1fr auto;
        /* 2 columnas: Info | Monto */
        grid-template-rows: auto auto;
        /* 2 filas */
        gap: 10px;
    }

    .celda-progreso {
        display: none;
    }

    /* Ocultar barra en móvil */

    .celda-monto {
        grid-column: 2;
        grid-row: 1;
    }

    .celda-estado {
        grid-column: 1 / span 2;
        text-align: left;
    }
}

/* === RESTO DE ESTILOS (IGUAL QUE ANTES) === */
.header-info h2 {
    margin: 0;
    font-size: 1.4em;
    color: #2c3e50;
}

.badge-curso {
    background: #3498db;
    color: white;
    padding: 4px 10px;
    border-radius: 12px;
    font-size: 0.8em;
    margin-left: 10px;
}

.caja-saldo {
    text-align: right;
    background: #e8f5e9;
    padding: 8px 20px;
    border-radius: 20px;
    border: 1px solid #c8e6c9;
    display: flex;
    align-items: center;
    gap: 10px;
}

.caja-saldo.negativo {
    background: #ffebee;
    border-color: #ffcdd2;
}

.caja-saldo.negativo .monto-saldo {
    color: #c62828;
}

.monto-saldo {
    font-size: 1.2em;
    font-weight: bold;
    color: #2e7d32;
}

/* Dashboard Interno */
.contenedor-dashboard {
    display: flex;
    flex-wrap: wrap;
}

.columna-lateral {
    flex: 35%;
    border-right: 1px solid #f0f0f0;
    min-width: 280px;
    background: #fafafa;
}

.columna-principal {
    flex: 65%;
    min-width: 320px;
    background: white;
}

.seccion-interna,
.seccion-lateral {
    padding: 25px;
}

.seccion-lateral.azul {
    background-color: #f4fcfd;
    border-bottom: 1px solid #e1f5fe;
}

h3 {
    margin-top: 0;
    font-size: 1em;
    color: #7f8c8d;
    text-transform: uppercase;
    border-bottom: 2px solid #eee;
    padding-bottom: 10px;
    margin-bottom: 20px;
}

/* Listas */
.texto-vacio {
    color: #bdc3c7;
    font-style: italic;
    font-size: 0.9em;
    text-align: center;
    padding: 10px;
}

.lista-pagos {
    display: flex;
    flex-direction: column;
    gap: 10px;
}

.item-pago {
    display: flex;
    align-items: center;
    gap: 10px;
    background: white;
    padding: 10px;
    border-radius: 8px;
    border: 1px solid #eee;
}

.pago-icono {
    font-size: 1.2rem;
    background: #e1f5fe;
    width: 35px;
    height: 35px;
    display: flex;
    justify-content: center;
    align-items: center;
    border-radius: 50%;
}

.pago-info {
    display: flex;
    flex-direction: column;
    flex-grow: 1;
}

.pago-fecha {
    font-weight: bold;
    font-size: 0.9rem;
    color: #2c3e50;
}

.pago-monto {
    font-weight: bold;
    color: #2980b9;
}

/* Renglones Cuotas (PC) */
.lista-mensualidades {
    display: flex;
    flex-direction: column;
    gap: 10px;
}

.renglon-cuota {
    display: grid;
    grid-template-columns: 2fr 1.5fr 1fr 1fr;
    align-items: center;
    background: white;
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    padding: 12px 20px;
    border-left: 5px solid #ccc;
    transition: all 0.2s;
    column-gap: 20px;
}

.renglon-cuota:hover {
    transform: translateX(5px);
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
}

.renglon-cuota.PENDIENTE {
    border-left-color: #e74c3c;
}

.renglon-cuota.PARCIAL {
    border-left-color: #f39c12;
}

.renglon-cuota.PAGADO {
    border-left-color: #2ecc71;
    opacity: 0.9;
    background: #f9fff9;
}

.nombre-concepto {
    font-weight: bold;
    color: #2c3e50;
    font-size: 1rem;
}

.vence {
    font-size: 0.75rem;
    color: #95a5a6;
    display: block;
}

.barra-fondo {
    height: 6px;
    background: #ecf0f1;
    border-radius: 3px;
    overflow: hidden;
    width: 100%;
}

.barra-relleno {
    height: 100%;
    background: #2ecc71;
}

.barra-relleno.PENDIENTE {
    background: #e74c3c;
    width: 5px;
}

.barra-relleno.PARCIAL {
    background: #f39c12;
}

.badge-estado {
    font-size: 0.75rem;
    padding: 4px 8px;
    border-radius: 4px;
    font-weight: bold;
    color: white;
    display: inline-block;
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

.celda-monto {
    text-align: right;
}

.celda-monto strong {
    font-size: 1.1rem;
    color: #34495e;
}

.pagado-parcial {
    font-size: 0.7rem;
    color: #27ae60;
    display: block;
}

/* Extras */
.lista-extras {
    display: flex;
    flex-direction: column;
    gap: 10px;
}

.item-extra {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px;
    border: 1px dashed #bdc3c7;
    border-radius: 8px;
    background: white;
}

.extra-monto-box {
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    gap: 5px;
}

.extra-valor {
    font-weight: bold;
    color: #34495e;
}
</style>