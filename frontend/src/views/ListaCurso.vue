<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '../axios'

const alumnos = ref([])
const cargando = ref(true)
const error = ref('')

// 1. OBTENER LOS DATOS
const cargarAlumnos = async () => {
    try {
        // Como tu backend ya sabe si el que pide es Staff o no, 
        // si eres de la Directiva, te enviará la lista completa automáticamente.
        const response = await api.get('alumnos/')
        alumnos.value = response.data
    } catch (err) {
        console.error('Error cargando la lista de alumnos:', err)
        error.value = 'No se pudo cargar la lista del curso.'
    } finally {
        cargando.value = false
    }
}

// 2. ORDENAR CON VUE (Magia Frontend ✨)
// Computed está vigilando: Si 'alumnos' cambia, reordena automáticamente.
const alumnosOrdenados = computed(() => {
    // Usamos .slice() para no mutar el array original y .localeCompare para ordenar alfabéticamente
    return alumnos.value.slice().sort((a, b) => {
        return a.nombre_lista.localeCompare(b.nombre_lista)
    })
})

onMounted(() => {
    cargarAlumnos()
})
</script>

<template>
    <div class="lista-container">
        <header class="encabezado">
            <h1>📋 Libro de Clases (8°B)</h1>
            <p>Listado oficial de alumnos y apoderados</p>
        </header>

        <div v-if="cargando" class="estado">Cargando lista oficial... ⏳</div>
        <div v-else-if="error" class="estado error">{{ error }}</div>

        <div v-else class="tabla-wrapper">
            <table class="tabla-curso">
                <thead>
                    <tr>
                        <th>#</th>
                        <th>Alumno</th>
                        <th>Apoderado</th>
                        <th>Email Contacto</th>
                    </tr>
                </thead>
                <tbody>
                    <tr v-for="(alumno, index) in alumnosOrdenados" :key="alumno.id">
                        <td class="col-numero">{{ index + 1 }}</td>
                        <td class="col-destacada">{{ alumno.nombre_lista }}</td>
                        <td>{{ alumno.apoderado_nombre }}</td>
                        <td class="col-email">{{ alumno.apoderado_email }}</td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>
</template>

<style scoped>
.lista-container {
    max-width: 1000px;
    margin: 0 auto;
    padding: 20px;
}

.encabezado {
    margin-bottom: 25px;
    border-bottom: 2px solid #ecf0f1;
    padding-bottom: 10px;
}

.encabezado h1 {
    color: #2c3e50;
    margin-bottom: 5px;
}

.encabezado p {
    color: #7f8c8d;
}

.estado {
    text-align: center;
    padding: 40px;
    font-size: 1.2rem;
    color: #7f8c8d;
    background: #f8f9fa;
    border-radius: 8px;
}

.error {
    color: #e74c3c;
}

.tabla-wrapper {
    overflow-x: auto;
    background: white;
    border-radius: 8px;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
}

.tabla-curso {
    width: 100%;
    border-collapse: collapse;
    text-align: left;
}

.tabla-curso th,
.tabla-curso td {
    padding: 15px;
    border-bottom: 1px solid #ecf0f1;
}

.tabla-curso th {
    background-color: #f8f9fa;
    color: #34495e;
    font-weight: bold;
    text-transform: uppercase;
    font-size: 0.9rem;
}

.tabla-curso tr:hover {
    background-color: #fdfefe;
}

.col-numero {
    font-weight: bold;
    color: #95a5a6;
    width: 50px;
    text-align: center;
}

.col-destacada {
    font-weight: 600;
    color: #2c3e50;
}

.col-email {
    color: #3498db;
    font-size: 0.95rem;
}
</style>