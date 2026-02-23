<script setup>
import { ref, onMounted } from 'vue'
import api from '../axios'

const stats = ref({ recaudado: 0, por_cobrar: 0, morosos: 0 })
const cargando = ref(true)

const cargarResumen = async () => {
    try {
        const response = await api.get('resumen-tesoreria/')
        stats.value = response.data
    } catch (error) {
        console.error("Error cargando tesorería", error)
    } finally {
        cargando.value = false
    }
}

const formatoDinero = (val) => new Intl.NumberFormat('es-CL', { style: 'currency', currency: 'CLP' }).format(val)

onMounted(() => {
    cargarResumen()
})
</script>

<template>
    <div class="dashboard-tesoreria">
        <h1>📊 Panel de Tesorería</h1>
        <p class="bajada">Resumen financiero del curso 8°B</p>

        <div v-if="cargando" class="loading">Calculando finanzas...</div>

        <div v-else class="grid-stats">
            <div class="card-stat verde">
                <div class="icono">💰</div>
                <div class="datos">
                    <h3>Recaudado</h3>
                    <p>{{ formatoDinero(stats.recaudado) }}</p>
                </div>
            </div>

            <div class="card-stat rojo">
                <div class="icono">📉</div>
                <div class="datos">
                    <h3>Por Cobrar</h3>
                    <p>{{ formatoDinero(stats.por_cobrar) }}</p>
                </div>
            </div>

            <div class="card-stat azul">
                <div class="icono">⚠️</div>
                <div class="datos">
                    <h3>Cargos Pendientes</h3>
                    <p>{{ stats.morosos }} boletas</p>
                </div>
            </div>
        </div>

        <div class="alert-info">
            💡 Próximamente: Lista detallada de alumnos y exportación a Excel.
        </div>
    </div>
</template>

<style scoped>
.dashboard-tesoreria {
    max-width: 1000px;
    margin: 0 auto;
    padding: 30px 20px;
}

h1 {
    color: #2c3e50;
    margin-bottom: 5px;
}

.bajada {
    color: #7f8c8d;
    margin-bottom: 30px;
}

.grid-stats {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 20px;
    margin-bottom: 40px;
}

.card-stat {
    background: white;
    padding: 25px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    gap: 20px;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
    transition: transform 0.2s;
}

.card-stat:hover {
    transform: translateY(-5px);
}

.icono {
    font-size: 2.5rem;
}

.datos h3 {
    margin: 0;
    font-size: 0.9rem;
    color: #7f8c8d;
    text-transform: uppercase;
}

.datos p {
    margin: 5px 0 0;
    font-size: 1.8rem;
    font-weight: bold;
    color: #2c3e50;
}

.card-stat.verde {
    border-bottom: 5px solid #2ecc71;
}

.card-stat.verde .datos p {
    color: #27ae60;
}

.card-stat.rojo {
    border-bottom: 5px solid #e74c3c;
}

.card-stat.rojo .datos p {
    color: #c0392b;
}

.card-stat.azul {
    border-bottom: 5px solid #3498db;
}

.alert-info {
    background: #e1f5fe;
    color: #0277bd;
    padding: 15px;
    border-radius: 8px;
    text-align: center;
}
</style>