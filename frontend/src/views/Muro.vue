<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '../axios'
import Swal from 'sweetalert2'

// === ESTADO ===
const noticias = ref([])
const eventos = ref([])
const cargando = ref(true)
const busqueda = ref('')
const esAdmin = ref(false)
const noticiaSeleccionada = ref(null)

// === VARIABLES PARA CREAR/EDITAR ===
const mostrarModalForm = ref(false)
const modoEdicion = ref(false) // 🚩 True = Editando, False = Creando
const idEdicion = ref(null)

const formulario = ref({
    titulo: '',
    contenido: '',
    etiqueta: 'GENERAL',
    imagen: null
})
const imagenPreview = ref(null)

// === PERMISOS Y CARGA ===
const verificarPermisos = async () => {
    try {
        const response = await api.get('quien-soy/')
        esAdmin.value = response.data.es_admin || response.data.es_staff
    } catch (e) { console.error(e) }
}

const cargarDatos = async () => {
    cargando.value = true
    try {
        const [resNoticias, resEventos] = await Promise.all([
            api.get('noticias/'),
            api.get('eventos/')
        ])
        noticias.value = resNoticias.data
        eventos.value = resEventos.data
    } catch (error) {
        console.error("Error cargando datos", error)
    } finally {
        cargando.value = false
    }
}

// === LÓGICA DEL FORMULARIO (CREAR Y EDITAR) ===
const abrirModalCrear = () => {
    modoEdicion.value = false
    idEdicion.value = null
    // Limpiamos el formulario para empezar de cero
    formulario.value = { titulo: '', contenido: '', etiqueta: 'GENERAL', imagen: null }
    imagenPreview.value = null
    mostrarModalForm.value = true
    document.body.style.overflow = 'hidden'
}

const abrirModalEditar = (noticia) => {
    modoEdicion.value = true
    idEdicion.value = noticia.id
    // Copiamos los datos existentes al formulario
    formulario.value = {
        titulo: noticia.titulo,
        contenido: noticia.contenido,
        etiqueta: noticia.etiqueta,
        imagen: null // Null porque si no sube nada nuevo, mantenemos la vieja en el backend
    }
    // Mostramos la imagen actual (si tiene)
    if (noticia.imagen) {
        imagenPreview.value = fixImagenUrl(noticia.imagen)
    } else {
        imagenPreview.value = null
    }
    mostrarModalForm.value = true
    document.body.style.overflow = 'hidden'
}

const cerrarModalForm = () => {
    mostrarModalForm.value = false
    document.body.style.overflow = 'auto'
}

const procesarImagen = (event) => {
    const archivo = event.target.files[0]
    if (archivo) {
        formulario.value.imagen = archivo
        imagenPreview.value = URL.createObjectURL(archivo)
    }
}

const guardarNoticia = async () => {
    if (!formulario.value.titulo || !formulario.value.contenido) {
        Swal.fire('Falta info', 'Título y contenido son obligatorios', 'warning')
        return
    }

    const formData = new FormData()
    formData.append('titulo', formulario.value.titulo)
    formData.append('contenido', formulario.value.contenido)
    formData.append('etiqueta', formulario.value.etiqueta)

    if (formulario.value.imagen) {
        formData.append('imagen', formulario.value.imagen)
    }

    try {
        Swal.showLoading()

        if (modoEdicion.value) {
            // === MODO EDITAR (PATCH) ===
            const response = await api.patch(`noticias/${idEdicion.value}/`, formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            })
            // Buscamos la noticia antigua en la lista y la reemplazamos por la nueva
            const index = noticias.value.findIndex(n => n.id === idEdicion.value)
            if (index !== -1) noticias.value[index] = response.data
            Swal.fire('¡Actualizado!', 'La noticia fue corregida', 'success')

        } else {
            // === MODO CREAR (POST) ===
            const response = await api.post('noticias/', formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            })
            // La ponemos al principio de la lista
            noticias.value.unshift(response.data)
            Swal.fire('¡Publicado!', 'Noticia creada con éxito', 'success')
        }

        cerrarModalForm()

    } catch (error) {
        console.error(error)
        Swal.fire('Error', 'No se pudo guardar', 'error')
    }
}

const borrarNoticia = async (id) => {
    const result = await Swal.fire({
        title: '¿Borrar noticia?', text: "No se puede deshacer", icon: 'warning',
        showCancelButton: true, confirmButtonText: 'Sí, borrar', cancelButtonText: 'Cancelar'
    })
    if (result.isConfirmed) {
        try {
            await api.delete(`noticias/${id}/`)
            noticias.value = noticias.value.filter(n => n.id !== id)
            Swal.fire('¡Borrado!', '', 'success')
        } catch (e) { Swal.fire('Error', 'No se pudo borrar', 'error') }
    }
}

// === UTILIDADES ===
const noticiasFiltradas = computed(() => {
    if (!busqueda.value) return noticias.value
    return noticias.value.filter(n =>
        n.titulo.toLowerCase().includes(busqueda.value.toLowerCase()) ||
        n.contenido.toLowerCase().includes(busqueda.value.toLowerCase())
    )
})

const abrirNoticia = (noticia) => {
    noticiaSeleccionada.value = noticia
    document.body.style.overflow = 'hidden'
}
const cerrarModalLectura = () => {
    noticiaSeleccionada.value = null
    document.body.style.overflow = 'auto'
}

const obtenerColorEtiqueta = (tag) => {
    const map = { 'GENERAL': '#3498db', 'URGENTE': '#e74c3c', 'REUNION': '#9b59b6', 'SOCIAL': '#2ecc71', 'COBRANZA': '#f1c40f' }
    return map[tag] || '#95a5a6'
}
const fixImagenUrl = (url) => {
    if (!url) return ''
    if (url.startsWith('http')) return url
    return `http://127.0.0.1:8000${url}`
}

onMounted(() => {
    cargarDatos()
    verificarPermisos()
})

// === VARIABLES PARA EVENTOS (NUEVO) ===
const mostrarModalEvento = ref(false)
const formEvento = ref({
    titulo: '',
    fecha: '' // Formato datetime-local
})

const abrirModalEvento = () => {
    formEvento.value = { titulo: '', fecha: '' }
    mostrarModalEvento.value = true
    document.body.style.overflow = 'hidden'
}

const cerrarModalEvento = () => {
    mostrarModalEvento.value = false
    document.body.style.overflow = 'auto'
}

const guardarEvento = async () => {
    if (!formEvento.value.titulo || !formEvento.value.fecha) {
        Swal.fire('Falta info', 'Título y Fecha son obligatorios', 'warning')
        return
    }
    try {
        Swal.showLoading()
        const response = await api.post('eventos/', formEvento.value)
        eventos.value.push(response.data)
        // Reordenar eventos por fecha ascendente
        eventos.value.sort((a, b) => new Date(a.fecha) - new Date(b.fecha))

        Swal.fire('¡Agendado!', 'El evento se programó con éxito', 'success')
        cerrarModalEvento()
    } catch (error) {
        console.error(error)
        Swal.fire('Error', 'No se pudo guardar el evento', 'error')
    }
}

const borrarEvento = async (id) => {
    const result = await Swal.fire({
        title: '¿Borrar evento?', text: "Se eliminará de la agenda", icon: 'warning',
        showCancelButton: true, confirmButtonText: 'Sí, borrar', cancelButtonText: 'Cancelar'
    })
    if (result.isConfirmed) {
        try {
            await api.delete(`eventos/${id}/`)
            eventos.value = eventos.value.filter(e => e.id !== id)
            Swal.fire('¡Borrado!', '', 'success')
        } catch (e) { Swal.fire('Error', 'No se pudo borrar', 'error') }
    }
}
</script>

<template>
    <div class="muro-layout">

        <aside class="sidebar-left">
            <div class="menu-muro">
                <h3>📌 Menú</h3>
                <ul>
                    <li class="activo">📰 Noticias</li>
                    <li class="inactivo">📅 Calendario <small>(Pronto)</small></li>
                    <li class="inactivo">📊 Encuestas <small>(Pronto)</small></li>
                    <li class="inactivo">📁 Documentos <small>(Pronto)</small></li>
                </ul>
            </div>
        </aside>

        <main class="feed-central">

            <div class="feed-header">
                <div class="titulo-row">
                    <h2>📢 Muro Informativo</h2>
                    <button v-if="esAdmin" class="btn-crear" @click="abrirModalCrear">
                        + Nueva
                    </button>
                </div>
                <div class="buscador-row">
                    <input v-model="busqueda" type="text" placeholder="🔍 Buscar noticias..." />
                </div>
            </div>

            <div v-if="cargando" class="loading">Cargando...</div>

            <div v-else-if="noticiasFiltradas.length === 0" class="sin-noticias">
                <p>No se encontraron noticias. 🦗</p>
            </div>

            <div v-else class="lista-noticias">
                <div v-for="noticia in noticiasFiltradas" :key="noticia.id" class="tarjeta-noticia"
                    @click="abrirNoticia(noticia)">

                    <div v-if="esAdmin" class="acciones-admin">
                        <button class="btn-accion btn-editar" @click.stop="abrirModalEditar(noticia)" title="Editar">
                            ✏️
                        </button>
                        <button class="btn-accion btn-borrar" @click.stop="borrarNoticia(noticia.id)" title="Borrar">
                            🗑️
                        </button>
                    </div>

                    <div v-if="noticia.imagen" class="imagen-banner">
                        <img :src="fixImagenUrl(noticia.imagen)" alt="Imagen noticia" />
                    </div>

                    <div class="contenido-tarjeta">
                        <div class="meta-data">
                            <span class="etiqueta" :style="{ backgroundColor: obtenerColorEtiqueta(noticia.etiqueta) }">
                                {{ noticia.etiqueta }}
                            </span>
                            <span class="fecha">{{ new Date(noticia.fecha_creacion).toLocaleDateString() }}</span>
                        </div>

                        <h3 class="titulo-noticia">{{ noticia.titulo }}</h3>

                        <p class="texto-preview">{{ noticia.contenido }}</p>

                        <button class="btn-leer-mas" @click.stop="abrirNoticia(noticia)">Leer más...</button>

                        <div class="autor">
                            <small>Por: {{ noticia.autor_nombre }}</small>
                        </div>
                    </div>
                </div>
            </div>
        </main>

        <aside class="sidebar-right">
            <div class="widget tarjeta-widget">
                <div class="widget-header header-con-boton">
                    <h3>📅 Próximos Eventos</h3>
                    <button v-if="esAdmin" class="btn-crear-mini" @click="abrirModalEvento" title="Nuevo Evento">
                        +
                    </button>
                </div>

                <ul class="lista-eventos">
                    <li v-if="eventos.length === 0" class="sin-eventos">
                        <small>No hay eventos próximos</small>
                    </li>

                    <li v-for="evento in eventos" :key="evento.id" class="item-evento-relativo">
                        <span class="dia">
                            {{ new Date(evento.fecha).getDate() }}
                        </span>

                        <div class="evento-info">
                            <strong>{{ evento.titulo }}</strong>
                            <small>
                                {{ new Date(evento.fecha).toLocaleDateString('es-CL', { month: 'short' }) }} -
                                {{ new Date(evento.fecha).toLocaleTimeString('es-CL', {
                                    hour: '2-digit',
                                    minute: '2-digit', hour12: false }) }} hrs
                            </small>
                        </div>

                        <button v-if="esAdmin" class="btn-borrar-evento" @click.stop="borrarEvento(evento.id)"
                            title="Borrar Evento">
                            ✖
                        </button>
                    </li>
                </ul>
            </div>
        </aside>

        <div v-if="noticiaSeleccionada" class="modal-overlay" @click.self="cerrarModalLectura">
            <div class="modal-contenido">
                <button class="btn-cerrar-modal" @click="cerrarModalLectura">✖</button>

                <div v-if="noticiaSeleccionada.imagen" class="modal-imagen">
                    <img :src="fixImagenUrl(noticiaSeleccionada.imagen)" alt="Detalle" />
                </div>

                <div class="modal-cuerpo">
                    <span class="etiqueta"
                        :style="{ backgroundColor: obtenerColorEtiqueta(noticiaSeleccionada.etiqueta) }">
                        {{ noticiaSeleccionada.etiqueta }}
                    </span>
                    <span class="fecha-modal">{{ new Date(noticiaSeleccionada.fecha_creacion).toLocaleDateString()
                    }}</span>

                    <h2>{{ noticiaSeleccionada.titulo }}</h2>

                    <p class="texto-completo">{{ noticiaSeleccionada.contenido }}</p>

                    <div class="modal-footer">
                        <small>Publicado por: <strong>{{ noticiaSeleccionada.autor_nombre }}</strong></small>
                    </div>
                </div>
            </div>
        </div>

        <div v-if="mostrarModalForm" class="modal-overlay" @click.self="cerrarModalForm">
            <div class="modal-contenido">
                <button class="btn-cerrar-modal" @click="cerrarModalForm">✖</button>

                <div class="modal-header-crear">
                    <h2>{{ modoEdicion ? '✏️ Editar Noticia' : '📝 Nueva Publicación' }}</h2>
                </div>

                <div class="modal-cuerpo form-crear">

                    <div class="campo">
                        <label>Título:</label>
                        <input v-model="formulario.titulo" type="text" placeholder="Ej: Reunión de Apoderados..." />
                    </div>

                    <div class="campo">
                        <label>Etiqueta:</label>
                        <select v-model="formulario.etiqueta">
                            <option value="GENERAL">General 🔵</option>
                            <option value="URGENTE">Urgente 🔴</option>
                            <option value="REUNION">Reunión 🟣</option>
                            <option value="SOCIAL">Social 🟢</option>
                            <option value="COBRANZA">Cobranza 🟡</option>
                        </select>
                    </div>

                    <div class="campo">
                        <label>Imagen {{ modoEdicion ? '(Subir nueva para reemplazar)' : '(Opcional)' }}:</label>
                        <input type="file" @change="procesarImagen" accept="image/*" />

                        <div v-if="imagenPreview" class="preview-box">
                            <img :src="imagenPreview" alt="Preview" />
                        </div>
                    </div>

                    <div class="campo">
                        <label>Contenido:</label>
                        <textarea v-model="formulario.contenido" rows="5"
                            placeholder="Escribe aquí los detalles..."></textarea>
                    </div>

                    <button class="btn-guardar" @click="guardarNoticia">
                        {{ modoEdicion ? 'Guardar Cambios 💾' : 'Publicar Noticia 🚀' }}
                    </button>

                </div>
            </div>
        </div>

        <div v-if="mostrarModalEvento" class="modal-overlay" @click.self="cerrarModalEvento">
            <div class="modal-contenido modal-sm">
                <button class="btn-cerrar-modal" @click="cerrarModalEvento">✖</button>

                <div class="modal-header-crear">
                    <h2>📅 Agendar Evento</h2>
                </div>

                <div class="modal-cuerpo form-crear">
                    <div class="campo">
                        <label>Título del Evento:</label>
                        <input v-model="formEvento.titulo" type="text" placeholder="Ej: Bingo Solidario" />
                    </div>

                    <div class="campo">
                        <label>Fecha y Hora:</label>
                        <input v-model="formEvento.fecha" type="datetime-local" />
                    </div>

                    <button class="btn-guardar" @click="guardarEvento">Guardar Evento 🚀</button>
                </div>
            </div>
        </div>

    </div>
</template>

<style scoped>
/* === LAYOUT Y ESTRUCTURA === */
.muro-layout {
    display: grid;
    grid-template-columns: 240px 1fr 280px;
    gap: 30px;
    max-width: 1200px;
    margin: 30px auto;
    padding: 0 20px;
}

/* === MENU IZQUIERDO === */
.menu-muro {
    background: white;
    padding: 20px;
    border-radius: 12px;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
    position: sticky;
    top: 80px;
    z-index: 10;
}

.menu-muro h3 {
    margin-top: 0;
    color: #2c3e50;
    font-size: 1.1rem;
    border-bottom: 2px solid #f4f6f9;
    padding-bottom: 10px;
}

.menu-muro ul {
    list-style: none;
    padding: 0;
}

.menu-muro li {
    padding: 12px 10px;
    border-radius: 8px;
    cursor: pointer;
    color: #7f8c8d;
    font-weight: 500;
    transition: all 0.2s;
}

.menu-muro li:hover {
    background: #f4f6f9;
    color: #3498db;
}

.menu-muro li.activo {
    background: #e3f2fd;
    color: #3498db;
    font-weight: bold;
}

.menu-muro li.inactivo {
    opacity: 0.6;
    cursor: not-allowed;
}

/* === FEED CENTRAL === */
.feed-header {
    background: white;
    padding: 20px;
    border-radius: 12px;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
    margin-bottom: 20px;
}

.titulo-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 15px;
}

.titulo-row h2 {
    margin: 0;
    font-size: 1.5rem;
    color: #2c3e50;
}

.buscador-row input {
    width: 100%;
    padding: 12px;
    border: 2px solid #ecf0f1;
    border-radius: 8px;
    font-size: 1rem;
    box-sizing: border-box;
}

.buscador-row input:focus {
    border-color: #3498db;
    outline: none;
}

/* === TARJETAS DE NOTICIAS === */
.tarjeta-noticia {
    background: white;
    border-radius: 12px;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
    overflow: hidden;
    margin-bottom: 25px;
    position: relative;
    transition: transform 0.2s;
    cursor: pointer;
}

.tarjeta-noticia:hover {
    transform: translateY(-3px);
    box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
}

.imagen-banner {
    width: 100%;
    height: 180px;
    overflow: hidden;
}

.imagen-banner img {
    width: 100%;
    height: 100%;
    object-fit: cover;
}

.contenido-tarjeta {
    padding: 20px;
}

.meta-data {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 10px;
}

.etiqueta {
    font-size: 0.75rem;
    color: white;
    padding: 4px 10px;
    border-radius: 20px;
    font-weight: bold;
    text-transform: uppercase;
}

.fecha {
    font-size: 0.85rem;
    color: #95a5a6;
}

.titulo-noticia {
    margin: 0 0 10px 0;
    font-size: 1.2rem;
    color: #2c3e50;
}

.texto-preview {
    color: #34495e;
    font-size: 0.95rem;
    line-height: 1.5;
    margin-bottom: 15px;
    display: -webkit-box;
    -webkit-line-clamp: 3;
    line-clamp: 3;
    -webkit-box-orient: vertical;
    overflow: hidden;
}

.btn-leer-mas {
    background: none;
    border: none;
    color: #3498db;
    cursor: pointer;
    padding: 0;
    font-weight: bold;
}

.btn-leer-mas:hover {
    text-decoration: underline;
}

.autor {
    margin-top: 15px;
    border-top: 1px solid #f0f0f0;
    padding-top: 10px;
    text-align: right;
    color: #bdc3c7;
}

/* Botón Crear */
.btn-crear {
    background: #2ecc71;
    color: white;
    border: none;
    padding: 8px 16px;
    border-radius: 6px;
    font-weight: bold;
    cursor: pointer;
}

.btn-crear:hover {
    background: #27ae60;
}

/* 🚀 ESTILOS BOTONES ADMIN (NUEVO) */
.acciones-admin {
    position: absolute;
    top: 10px;
    right: 10px;
    display: flex;
    gap: 8px;
    z-index: 10;
}

.btn-accion {
    background: rgba(255, 255, 255, 0.95);
    border: none;
    border-radius: 50%;
    width: 34px;
    height: 34px;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2);
    transition: all 0.2s;
    font-size: 1rem;
}

.btn-editar:hover {
    background: #f1c40f;
    color: white;
    transform: scale(1.1);
}

.btn-borrar:hover {
    background: #e74c3c;
    color: white;
    transform: scale(1.1);
}

/* === WIDGETS === */
.tarjeta-widget {
    background: white;
    padding: 20px;
    border-radius: 12px;
    margin-bottom: 20px;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
}

.widget-header h3 {
    margin: 0 0 15px 0;
    font-size: 1rem;
    color: #7f8c8d;
    text-transform: uppercase;
    border-bottom: 2px solid #f4f6f9;
    padding-bottom: 10px;
}

.widget-body.compacto p {
    margin: 5px 0;
    font-size: 0.9rem;
    color: #2c3e50;
}

.btn-copiar-mini {
    width: 100%;
    margin-top: 10px;
    background: #ecf0f1;
    border: none;
    padding: 8px;
    border-radius: 6px;
    cursor: pointer;
    color: #7f8c8d;
    font-size: 0.85rem;
    font-weight: bold;
}

.btn-copiar-mini:hover {
    background: #bdc3c7;
    color: white;
}

.lista-eventos {
    list-style: none;
    padding: 0;
    margin: 0;
}

.lista-eventos li {
    display: flex;
    align-items: center;
    gap: 15px;
    padding: 10px 0;
    border-bottom: 1px solid #f9f9f9;
}

.lista-eventos li:last-child {
    border-bottom: none;
}

.dia {
    background: #e3f2fd;
    color: #3498db;
    width: 40px;
    height: 40px;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: bold;
    font-size: 1.1rem;
}

.evento-info {
    display: flex;
    flex-direction: column;
}

.evento-info strong {
    font-size: 0.95rem;
    color: #2c3e50;
}

.evento-info small {
    color: #95a5a6;
    font-size: 0.8rem;
}

/* === ESTILOS MODAL === */
.modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.7);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 1000;
    padding: 20px;
    animation: fadeIn 0.3s ease;
}

.modal-contenido {
    background: white;
    width: 100%;
    max-width: 700px;
    max-height: 90vh;
    border-radius: 16px;
    overflow-y: auto;
    position: relative;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
    animation: slideUp 0.3s ease;
}

.btn-cerrar-modal {
    position: absolute;
    top: 15px;
    right: 15px;
    background: rgba(0, 0, 0, 0.5);
    color: white;
    border: none;
    width: 35px;
    height: 35px;
    border-radius: 50%;
    cursor: pointer;
    font-size: 1.2rem;
    z-index: 10;
    transition: background 0.2s;
}

.btn-cerrar-modal:hover {
    background: rgba(0, 0, 0, 0.8);
}

.modal-imagen img {
    width: 100%;
    height: 300px;
    object-fit: cover;
    display: block;
}

.modal-cuerpo {
    padding: 30px;
}

.fecha-modal {
    margin-left: 10px;
    color: #7f8c8d;
    font-size: 0.9rem;
}

.modal-cuerpo h2 {
    margin-top: 15px;
    font-size: 1.8rem;
    color: #2c3e50;
}

.texto-completo {
    font-size: 1.1rem;
    line-height: 1.8;
    color: #34495e;
    white-space: pre-wrap;
}

/* === ESTILOS FORMULARIO (NUEVO) === */
.modal-header-crear {
    padding: 20px 30px;
    border-bottom: 1px solid #eee;
    background: #f9f9f9;
    border-radius: 16px 16px 0 0;
}

.modal-header-crear h2 {
    margin: 0;
    color: #2c3e50;
}

.form-crear {
    display: flex;
    flex-direction: column;
    gap: 20px;
}

.campo label {
    display: block;
    font-weight: bold;
    margin-bottom: 5px;
    color: #34495e;
}

.campo input[type="text"],
.campo select,
.campo textarea {
    width: 100%;
    padding: 12px;
    border: 2px solid #ecf0f1;
    border-radius: 8px;
    font-size: 1rem;
    box-sizing: border-box;
    transition: border 0.3s;
    font-family: inherit;
}

.campo input:focus,
.campo select:focus,
.campo textarea:focus {
    border-color: #3498db;
    outline: none;
}

.preview-box {
    margin-top: 10px;
    width: 100%;
    height: 200px;
    border-radius: 8px;
    overflow: hidden;
    border: 2px dashed #bdc3c7;
}

.preview-box img {
    width: 100%;
    height: 100%;
    object-fit: cover;
}

.btn-guardar {
    background: #2ecc71;
    color: white;
    border: none;
    padding: 15px;
    border-radius: 8px;
    font-size: 1.1rem;
    font-weight: bold;
    cursor: pointer;
    transition: background 0.3s;
    width: 100%;
    margin-top: 10px;
}

.btn-guardar:hover {
    background: #27ae60;
    transform: translateY(-2px);
}

/* === ESTILOS NUEVOS PARA EVENTOS === */
.header-con-boton {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.btn-crear-mini {
    background: #3498db;
    color: white;
    border: none;
    border-radius: 50%;
    width: 28px;
    height: 28px;
    font-size: 1.2rem;
    font-weight: bold;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
    transition: background 0.2s;
}

.btn-crear-mini:hover {
    background: #2980b9;
    transform: scale(1.05);
}

.item-evento-relativo {
    position: relative;
    /* Para poder posicionar la X absoluta dentro del li */
}

.btn-borrar-evento {
    position: absolute;
    right: 0;
    top: 50%;
    transform: translateY(-50%);
    background: none;
    border: none;
    color: #e74c3c;
    cursor: pointer;
    opacity: 0.3;
    /* Semitransparente para no estorbar visualmente */
    transition: opacity 0.2s, transform 0.2s;
    font-size: 0.8rem;
    padding: 5px;
}

.item-evento-relativo:hover .btn-borrar-evento {
    opacity: 1;
    /* Aparece al pasar el mouse por encima del evento */
}

.btn-borrar-evento:hover {
    transform: translateY(-50%) scale(1.3);
}

.modal-sm {
    max-width: 400px;
    /* Hacemos el modal de evento un poco más angosto que el de noticias */
}

@keyframes fadeIn {
    from {
        opacity: 0;
    }

    to {
        opacity: 1;
    }
}

@keyframes slideUp {
    from {
        transform: translateY(50px);
        opacity: 0;
    }

    to {
        transform: translateY(0);
        opacity: 1;
    }
}

/* RESPONSIVE */
@media (max-width: 900px) {
    .muro-layout {
        grid-template-columns: 1fr;
    }

    .sidebar-left,
    .sidebar-right {
        display: none;
    }
}
</style>