<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '../axios'
import Swal from 'sweetalert2'

// === ESTADO PRINCIPAL ===
const noticias = ref([])
const eventos = ref([])
const cargando = ref(true)
const busqueda = ref('')
const esAdmin = ref(false)
const noticiaSeleccionada = ref(null)
const fotoAmpliada = ref(null)

const vistaActiva = ref('noticias')
const menuMovilAbierto = ref(false)

const seleccionarVista = (vista) => {
    vistaActiva.value = vista
    menuMovilAbierto.value = false
    window.scrollTo({ top: 0, behavior: 'smooth' })
}

// === DATOS DEL HORARIO 2025 ===
const horarioSemana = ref([
    { dia: 'Lunes', bloques: [{ tipo: 'clase', tiempo: '08:00 - 09:30', materia: 'Biología CN' }, { tipo: 'recreo' }, { tipo: 'clase', tiempo: '09:45 - 11:15', materia: 'Lengua y Literatura' }, { tipo: 'recreo' }, { tipo: 'clase', tiempo: '11:30 - 12:55', materia: 'Música' }, { tipo: 'recreo' }, { tipo: 'clase', tiempo: '13:05 - 14:30', materia: 'Matemática' }] },
    { dia: 'Martes', bloques: [{ tipo: 'clase', tiempo: '08:00 - 09:30', materia: 'Biología CN' }, { tipo: 'recreo' }, { tipo: 'clase', tiempo: '09:45 - 11:15', materia: 'Física CN' }, { tipo: 'recreo' }, { tipo: 'clase', tiempo: '11:30 - 12:55', materia: 'Historia, Geografía y CS' }, { tipo: 'almuerzo', tiempo: '13:00 - 13:45', materia: '🍽️ Almuerzo' }, { tipo: 'clase', tiempo: '13:45 - 14:25', materia: 'Orientación' }, { tipo: 'clase', tiempo: '14:35 - 16:00', materia: 'Inglés' }] },
    { dia: 'Miércoles', bloques: [{ tipo: 'clase', tiempo: '08:00 - 09:30', materia: 'Lengua y Literatura' }, { tipo: 'recreo' }, { tipo: 'clase', tiempo: '09:45 - 11:15', materia: 'Ed. Física y Salud' }, { tipo: 'recreo' }, { tipo: 'clase', tiempo: '11:30 - 12:55', materia: 'Matemática' }, { tipo: 'recreo' }, { tipo: 'clase', tiempo: '13:05 - 14:30', materia: 'Historia, Geografía y CS' }] },
    { dia: 'Jueves', bloques: [{ tipo: 'clase', tiempo: '08:00 - 09:30', materia: 'Inglés' }, { tipo: 'recreo' }, { tipo: 'clase', tiempo: '09:45 - 11:15', materia: 'Lengua y Literatura' }, { tipo: 'recreo' }, { tipo: 'clase', tiempo: '11:30 - 12:55', materia: 'Tecnología' }, { tipo: 'recreo' }, { tipo: 'clase', tiempo: '13:05 - 14:30', materia: 'Matemática' }] },
    { dia: 'Viernes', bloques: [{ tipo: 'clase', tiempo: '08:00 - 09:30', materia: 'Química CN' }, { tipo: 'recreo' }, { tipo: 'clase', tiempo: '09:45 - 11:15', materia: 'Artes Visuales' }, { tipo: 'recreo' }, { tipo: 'clase', tiempo: '11:30 - 12:55', materia: 'Lengua y Literatura' }, { tipo: 'recreo' }, { tipo: 'clase', tiempo: '13:05 - 14:30', materia: 'Matemática' }] }
])

// === VARIABLES PARA CREAR/EDITAR NOTICIAS ===
const mostrarModalForm = ref(false)
const modoEdicion = ref(false)
const idEdicion = ref(null)

const formulario = ref({
    titulo: '',
    contenido: '',
    etiqueta: 'GENERAL',
    archivo: null,
    galeria: []
})

const archivoPreviewNombre = ref('')
const galeriaPreview = ref([])

// === PERMISOS Y CARGA DE DATOS ===
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

// === LÓGICA DEL FORMULARIO ===
const abrirModalCrear = () => {
    modoEdicion.value = false
    idEdicion.value = null
    formulario.value = { titulo: '', contenido: '', etiqueta: 'GENERAL', archivo: null, galeria: [] }
    archivoPreviewNombre.value = ''
    galeriaPreview.value = []
    mostrarModalForm.value = true
    document.body.style.overflow = 'hidden'
}

const abrirModalEditar = (noticia) => {
    modoEdicion.value = true
    idEdicion.value = noticia.id
    formulario.value = {
        titulo: noticia.titulo,
        contenido: noticia.contenido,
        etiqueta: noticia.etiqueta,
        archivo: null,
        galeria: []
    }
    archivoPreviewNombre.value = noticia.archivo ? 'Documento actual ya subido' : ''
    galeriaPreview.value = []
    mostrarModalForm.value = true
    document.body.style.overflow = 'hidden'
}

const cerrarModalForm = () => {
    mostrarModalForm.value = false
    document.body.style.overflow = 'auto'
}

const procesarArchivo = (event) => {
    const file = event.target.files[0]
    if (file) {
        formulario.value.archivo = file
        archivoPreviewNombre.value = file.name
    }
}

const procesarGaleria = (event) => {
    const files = Array.from(event.target.files)
    if (files.length > 6) {
        Swal.fire('Límite excedido', 'Solo puedes subir hasta 6 fotos a la vez.', 'warning')
        event.target.value = ''
        return
    }
    formulario.value.galeria = files
    galeriaPreview.value = files.map(file => URL.createObjectURL(file))
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

    if (formulario.value.archivo) {
        formData.append('archivo', formulario.value.archivo)
    }

    if (!modoEdicion.value && formulario.value.galeria.length > 0) {
        formulario.value.galeria.forEach(img => {
            formData.append('galeria_imagenes', img)
        })
    }

    try {
        Swal.showLoading()

        if (modoEdicion.value) {
            const response = await api.patch(`noticias/${idEdicion.value}/`, formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            })
            const index = noticias.value.findIndex(n => n.id === idEdicion.value)
            if (index !== -1) noticias.value[index] = response.data
            Swal.fire('¡Actualizado!', 'La noticia fue corregida', 'success')
        } else {
            const response = await api.post('noticias/', formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            })
            noticias.value.unshift(response.data)
            Swal.fire('¡Publicado!', 'Noticia y archivos subidos con éxito', 'success')
        }

        cerrarModalForm()

    } catch (error) {
        console.error(error)
        Swal.fire('Error', 'No se pudo guardar', 'error')
    }
}

const borrarNoticia = async (id) => {
    const result = await Swal.fire({
        title: '¿Borrar noticia?', text: "Se borrará la noticia, el documento y sus fotos asociadas.", icon: 'warning',
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

// === UTILIDADES VISUALES ===
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
    fotoAmpliada.value = null
    document.body.style.overflow = 'auto'
}

const estilosEtiqueta = (tag) => {
    const config = {
        'GENERAL': { color: '#3498db', icono: '📢' },
        'URGENTE': { color: '#e74c3c', icono: '🚨' },
        'REUNION': { color: '#9b59b6', icono: '👥' },
        'SOCIAL': { color: '#2ecc71', icono: '🎉' },
        'COBRANZA': { color: '#f1c40f', icono: '💰' },
        'ACADEMICO': { color: '#e67e22', icono: '📚' },
        'FINANZAS': { color: '#34495e', icono: '💵' }
    }
    return config[tag] || { color: '#95a5a6', icono: '📌' }
}

const obtenerColorEtiqueta = (tag) => estilosEtiqueta(tag).color
const obtenerIconoEtiqueta = (tag) => estilosEtiqueta(tag).icono

const fixMediaUrl = (url) => {
    if (!url) return ''
    if (url.startsWith('http')) return url
    return `http://127.0.0.1:8000${url}`
}

const obtenerNombreArchivo = (url) => {
    if (!url) return 'Documento Adjunto';
    const nombre = url.split('/').pop();
    return nombre.split('?')[0];
}

onMounted(() => {
    cargarDatos()
    verificarPermisos()
})

// === EVENTOS ===
const mostrarModalEvento = ref(false)
const formEvento = ref({ titulo: '', fecha: '' })

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
        eventos.value.sort((a, b) => new Date(a.fecha) - new Date(b.fecha))
        Swal.fire('¡Agendado!', 'El evento se programó con éxito', 'success')
        cerrarModalEvento()
    } catch (error) {
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
                    <li :class="{ activo: vistaActiva === 'noticias' }" @click="vistaActiva = 'noticias'">📰 Noticias
                    </li>
                    <li :class="{ activo: vistaActiva === 'horario' }" @click="vistaActiva = 'horario'">📅 Horario</li>
                    <li class="inactivo">📊 Encuestas <small>(Pronto)</small></li>
                    <li class="inactivo">📁 Documentos <small>(Pronto)</small></li>
                </ul>
            </div>
        </aside>

        <main class="feed-central">
            <div v-if="vistaActiva === 'noticias'" class="vista-animada">

                <div class="mensaje-bienvenida">
                    <h2>👋 ¡Bienvenidos al Portal de Apoderados 8°B!</h2>
                    <p>
                        Este espacio fue diseñado para mantenerte informado y brindarte transparencia total.
                        Aquí podrás leer los comunicados oficiales, revisar el calendario y hacer seguimiento de tus
                        finanzas.
                    </p>
                </div>

                <div class="widget tarjeta-widget eventos-movil-solo">
                    <div class="widget-header header-con-boton">
                        <h3>📅 Próximos Eventos</h3>
                        <button v-if="esAdmin" class="btn-crear-mini" @click="abrirModalEvento"
                            title="Nuevo Evento">+</button>
                    </div>
                    <ul class="lista-eventos">
                        <li v-if="eventos.length === 0" class="sin-eventos"><small>No hay eventos próximos</small></li>
                        <li v-for="evento in eventos" :key="evento.id" class="item-evento-relativo">
                            <span class="dia">{{ new Date(evento.fecha).getDate() }}</span>
                            <div class="evento-info">
                                <strong>{{ evento.titulo }}</strong>
                                <small>{{ new Date(evento.fecha).toLocaleDateString('es-CL', { month: 'short' }) }} - {{
                                    new Date(evento.fecha).toLocaleTimeString('es-CL', {
                                        hour: '2-digit', minute:
                                    '2-digit', hour12: false }) }} hrs</small>
                            </div>
                            <button v-if="esAdmin" class="btn-borrar-evento" @click.stop="borrarEvento(evento.id)"
                                title="Borrar Evento">✖</button>
                        </li>
                    </ul>
                </div>
                <div class="feed-header">
                    <div class="titulo-row">
                        <h2>📢 Muro Informativo</h2>
                        <button v-if="esAdmin" class="btn-crear" @click="abrirModalCrear">+ Nueva</button>
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
                    <div v-for="noticia in noticiasFiltradas" :key="noticia.id" class="tarjeta-compacta"
                        @click="abrirNoticia(noticia)"
                        :style="{ borderLeftColor: obtenerColorEtiqueta(noticia.etiqueta) }">

                        <div v-if="esAdmin" class="acciones-admin">
                            <button class="btn-accion btn-editar" @click.stop="abrirModalEditar(noticia)"
                                title="Editar">✏️</button>
                            <button class="btn-accion btn-borrar" @click.stop="borrarNoticia(noticia.id)"
                                title="Borrar">🗑️</button>
                        </div>

                        <div class="header-compacto">
                            <div class="icono-cuadro"
                                :style="{ backgroundColor: obtenerColorEtiqueta(noticia.etiqueta) + '1A', color: obtenerColorEtiqueta(noticia.etiqueta) }">
                                {{ obtenerIconoEtiqueta(noticia.etiqueta) }}
                            </div>

                            <div class="info-principal">
                                <h3>{{ noticia.titulo }}</h3>
                                <div class="meta-compacto">
                                    <span class="badge-texto"
                                        :style="{ color: obtenerColorEtiqueta(noticia.etiqueta) }">{{ noticia.etiqueta
                                        }}</span>
                                    <span class="separador">•</span>
                                    <span>{{ new Date(noticia.fecha_creacion).toLocaleDateString() }}</span>
                                    <span v-if="noticia.archivo" class="badge-mini">📎 Adjunto</span>
                                    <span v-if="noticia.galeria && noticia.galeria.length > 0" class="badge-mini">🖼️
                                        Fotos</span>
                                </div>
                            </div>
                        </div>

                        <p class="preview-texto">{{ noticia.contenido }}</p>
                    </div>
                </div>
            </div>

            <div v-else-if="vistaActiva === 'horario'" class="vista-animada">
                <div class="feed-header">
                    <h2>📅 Horario Octavo Básico 2025</h2>
                    <p style="color: #7f8c8d; font-size: 0.95rem; margin-top: 5px;">Desliza hacia abajo en celulares
                        para ver todos los días.</p>
                </div>
                <div class="horario-falsa-tabla">
                    <div v-for="dia in horarioSemana" :key="dia.dia" class="dia-columna">
                        <div class="dia-titulo">{{ dia.dia }}</div>
                        <div class="bloques-container">
                            <div v-for="(bloque, index) in dia.bloques" :key="index">
                                <div v-if="bloque.tipo === 'clase'" class="bloque-clase">
                                    <span class="tiempo">{{ bloque.tiempo }}</span>
                                    <span class="materia">{{ bloque.materia }}</span>
                                </div>
                                <div v-else-if="bloque.tipo === 'recreo'" class="bloque-recreo"></div>
                                <div v-else-if="bloque.tipo === 'almuerzo'" class="bloque-almuerzo">
                                    <span class="tiempo">{{ bloque.tiempo }}</span>
                                    <span class="materia">{{ bloque.materia }}</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </main>

        <aside class="sidebar-right">
            <div class="widget tarjeta-widget">
                <div class="widget-header header-con-boton">
                    <h3>📅 Próximos Eventos</h3>
                    <button v-if="esAdmin" class="btn-crear-mini" @click="abrirModalEvento"
                        title="Nuevo Evento">+</button>
                </div>
                <ul class="lista-eventos">
                    <li v-if="eventos.length === 0" class="sin-eventos"><small>No hay eventos próximos</small></li>
                    <li v-for="evento in eventos" :key="evento.id" class="item-evento-relativo">
                        <span class="dia">{{ new Date(evento.fecha).getDate() }}</span>
                        <div class="evento-info">
                            <strong>{{ evento.titulo }}</strong>
                            <small>{{ new Date(evento.fecha).toLocaleDateString('es-CL', { month: 'short' }) }} - {{ new
                                Date(evento.fecha).toLocaleTimeString('es-CL', {
                                    hour: '2-digit', minute: '2-digit',
                                hour12: false }) }} hrs</small>
                        </div>
                        <button v-if="esAdmin" class="btn-borrar-evento" @click.stop="borrarEvento(evento.id)"
                            title="Borrar Evento">✖</button>
                    </li>
                </ul>
            </div>
        </aside>

        <div v-if="noticiaSeleccionada" class="modal-overlay" @click.self="cerrarModalLectura">
            <div class="modal-contenido">
                <button class="btn-cerrar-modal" @click="cerrarModalLectura">✖</button>

                <div class="banner-icono"
                    :style="{ backgroundColor: obtenerColorEtiqueta(noticiaSeleccionada.etiqueta), height: '150px' }">
                    <span class="icono-gigante" style="font-size: 5rem;">{{
                        obtenerIconoEtiqueta(noticiaSeleccionada.etiqueta) }}</span>
                </div>

                <div class="modal-cuerpo">
                    <span class="etiqueta"
                        :style="{ backgroundColor: obtenerColorEtiqueta(noticiaSeleccionada.etiqueta) }">{{
                        noticiaSeleccionada.etiqueta }}</span>
                    <span class="fecha-modal">{{ new Date(noticiaSeleccionada.fecha_creacion).toLocaleDateString()
                        }}</span>

                    <h2>{{ noticiaSeleccionada.titulo }}</h2>
                    <p class="texto-completo">{{ noticiaSeleccionada.contenido }}</p>

                    <div v-if="noticiaSeleccionada.archivo" class="seccion-adjunto">
                        <h4>📄 Documento Adjunto</h4>
                        <a :href="fixMediaUrl(noticiaSeleccionada.archivo)" target="_blank" class="btn-descargar"
                            :title="'Descargar ' + obtenerNombreArchivo(noticiaSeleccionada.archivo)">
                            📎 {{ obtenerNombreArchivo(noticiaSeleccionada.archivo) }}
                        </a>
                    </div>

                    <div v-if="noticiaSeleccionada.galeria && noticiaSeleccionada.galeria.length > 0"
                        class="seccion-galeria">
                        <h4>📸 Galería de Imágenes</h4>
                        <div class="grilla-fotos">
                            <img v-for="foto in noticiaSeleccionada.galeria" :key="foto.id"
                                :src="fixMediaUrl(foto.imagen)" alt="Foto"
                                @click="fotoAmpliada = fixMediaUrl(foto.imagen)">
                        </div>
                    </div>

                    <div class="modal-footer">
                        <small>Publicado por: <strong>{{ noticiaSeleccionada.autor_nombre }}</strong></small>
                    </div>
                </div>
            </div>

            <div v-if="fotoAmpliada" class="visor-pantalla-completa" @click="fotoAmpliada = null">
                <span class="btn-cerrar-visor">✖</span>
                <img :src="fotoAmpliada" alt="Ampliación">
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
                        <label>Etiqueta / Categoría:</label>
                        <select v-model="formulario.etiqueta">
                            <option value="GENERAL">General 📢</option>
                            <option value="ACADEMICO">Académico 📚</option>
                            <option value="REUNION">Reunión 👥</option>
                            <option value="URGENTE">Urgente 🚨</option>
                            <option value="SOCIAL">Social 🎉</option>
                            <option value="FINANZAS">Finanzas 💵</option>
                            <option value="COBRANZA">Cobranza 💰</option>
                        </select>
                    </div>

                    <div class="campo">
                        <label>Contenido:</label>
                        <textarea v-model="formulario.contenido" rows="6"
                            placeholder="Escribe aquí el cuerpo del mensaje..."></textarea>
                    </div>

                    <hr class="divisor-form">

                    <div class="campo">
                        <label>📄 Subir Documento Adjunto (PDF, Word, etc) [Opcional]:</label>
                        <input type="file" @change="procesarArchivo" accept=".pdf,.doc,.docx,.xls,.xlsx" />
                        <small v-if="archivoPreviewNombre" class="texto-verde">✔️ Seleccionado: {{ archivoPreviewNombre
                            }}</small>
                    </div>

                    <div v-if="!modoEdicion" class="campo">
                        <label>📸 Subir Fotos para la Galería (Máx. 6) [Opcional]:</label>
                        <input type="file" @change="procesarGaleria" accept="image/*" multiple />

                        <div v-if="galeriaPreview.length > 0" class="mini-grilla-preview">
                            <img v-for="(src, idx) in galeriaPreview" :key="idx" :src="src" alt="Preview">
                        </div>
                    </div>

                    <div v-if="modoEdicion" class="alerta-edicion">
                        <small>ℹ️ Las fotos de la galería no se pueden editar aquí. Si te equivocaste de fotos, borra la
                            noticia y vuelve a crearla.</small>
                    </div>

                    <button class="btn-guardar" @click="guardarNoticia">
                        {{ modoEdicion ? 'Guardar Cambios 💾' : 'Publicar Muro 🚀' }}
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
                    <div class="campo"><label>Título del Evento:</label><input v-model="formEvento.titulo" type="text"
                            placeholder="Ej: Bingo Solidario" /></div>
                    <div class="campo"><label>Fecha y Hora:</label><input v-model="formEvento.fecha"
                            type="datetime-local" /></div>
                    <button class="btn-guardar" @click="guardarEvento">Guardar Evento 🚀</button>
                </div>
            </div>
        </div>

        <div class="contenedor-menu-flotante">
            <div v-if="menuMovilAbierto" class="overlay-menu-movil" @click="menuMovilAbierto = false"></div>
            <div :class="['opciones-flotantes', { 'abierto': menuMovilAbierto }]">
                <ul>
                    <li :class="{ activo: vistaActiva === 'noticias' }" @click="seleccionarVista('noticias')">📰
                        Noticias</li>
                    <li :class="{ activo: vistaActiva === 'horario' }" @click="seleccionarVista('horario')">📅 Horario
                    </li>
                    <li class="inactivo">📊 Encuestas <small>(Pronto)</small></li>
                    <li class="inactivo">📁 Documentos <small>(Pronto)</small></li>
                </ul>
            </div>
            <button class="btn-fab" @click="menuMovilAbierto = !menuMovilAbierto">{{ menuMovilAbierto ? '✖ Cerrar' : '☰ Menú' }}</button>
        </div>

    </div>
</template>

<style scoped>
.muro-layout {
    display: grid;
    grid-template-columns: 240px 1fr 280px;
    gap: 30px;
    max-width: 1200px;
    margin: 30px auto;
    padding: 0 20px;
}

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

.mensaje-bienvenida {
    background: linear-gradient(135deg, #f0f7fa 0%, #e3f2fd 100%);
    border-left: 5px solid #3498db;
    padding: 20px;
    border-radius: 12px;
    margin-bottom: 25px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.03);
}

.mensaje-bienvenida h2 {
    margin: 0 0 8px 0;
    color: #2980b9;
    font-size: 1.3rem;
}

.mensaje-bienvenida p {
    margin: 0;
    color: #34495e;
    font-size: 0.95rem;
    line-height: 1.5;
}

/* FEED CENTRAL */
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

.vista-animada {
    animation: fadeIn 0.3s ease;
}

.tarjeta-compacta {
    background: white;
    border-radius: 10px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
    padding: 20px;
    margin-bottom: 15px;
    position: relative;
    cursor: pointer;
    border-left: 5px solid #ccc;
    transition: transform 0.2s, box-shadow 0.2s;
}

.tarjeta-compacta:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 15px rgba(0, 0, 0, 0.08);
}

.header-compacto {
    display: flex;
    align-items: center;
    gap: 15px;
    margin-bottom: 10px;
}

.icono-cuadro {
    width: 45px;
    height: 45px;
    border-radius: 10px;
    display: flex;
    justify-content: center;
    align-items: center;
    font-size: 1.5rem;
    flex-shrink: 0;
}

.info-principal h3 {
    margin: 0 0 5px 0;
    font-size: 1.15rem;
    color: #2c3e50;
    padding-right: 70px;
}

.meta-compacto {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 0.8rem;
    color: #7f8c8d;
    flex-wrap: wrap;
}

.badge-texto {
    font-weight: bold;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.separador {
    opacity: 0.5;
}

.badge-mini {
    background: #f1f2f6;
    padding: 2px 6px;
    border-radius: 4px;
    font-weight: bold;
    color: #2c3e50;
    border: 1px solid #dfe6e9;
}

.preview-texto {
    color: #555;
    font-size: 0.95rem;
    line-height: 1.4;
    margin: 0;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
}

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

.acciones-admin {
    position: absolute;
    top: 15px;
    right: 15px;
    display: flex;
    gap: 8px;
    z-index: 10;
}

.btn-accion {
    background: rgba(255, 255, 255, 0.9);
    border: 1px solid #eee;
    border-radius: 50%;
    width: 32px;
    height: 32px;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.2s;
    font-size: 0.9rem;
}

.btn-editar:hover {
    background: #f1c40f;
    color: white;
    border-color: #f1c40f;
}

.btn-borrar:hover {
    background: #e74c3c;
    color: white;
    border-color: #e74c3c;
}

/* MODALES */
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
    margin-bottom: 20px;
}

.banner-icono {
    width: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    opacity: 0.85;
}

.etiqueta {
    font-size: 0.75rem;
    color: white;
    padding: 4px 10px;
    border-radius: 20px;
    font-weight: bold;
    text-transform: uppercase;
}

.modal-footer {
    margin-top: 20px;
    border-top: 1px solid #f0f0f0;
    padding-top: 15px;
    text-align: right;
    color: #bdc3c7;
}

.seccion-adjunto,
.seccion-galeria {
    margin-top: 25px;
    padding: 20px;
    background: #f8f9fa;
    border-radius: 8px;
    border: 1px solid #ecf0f1;
}

.seccion-adjunto h4,
.seccion-galeria h4 {
    margin: 0 0 15px 0;
    color: #2c3e50;
    font-size: 1.1rem;
}

.btn-descargar {
    display: inline-block;
    background: #e3f2fd;
    color: #2980b9;
    padding: 12px 20px;
    border-radius: 8px;
    text-decoration: none;
    font-weight: bold;
    border: 1px solid #90caf9;
    transition: all 0.2s;
}

.btn-descargar:hover {
    background: #bbdefb;
}

.grilla-fotos {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
    gap: 15px;
}

.grilla-fotos img {
    width: 100%;
    height: 120px;
    object-fit: cover;
    border-radius: 8px;
    cursor: pointer;
    box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
    transition: transform 0.2s;
    border: 2px solid white;
}

.grilla-fotos img:hover {
    transform: scale(1.05);
    border-color: #3498db;
}

.visor-pantalla-completa {
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    background: rgba(0, 0, 0, 0.9);
    z-index: 3000;
    display: flex;
    justify-content: center;
    align-items: center;
    cursor: zoom-out;
}

.visor-pantalla-completa img {
    max-width: 90%;
    max-height: 90%;
    border-radius: 8px;
    box-shadow: 0 5px 25px rgba(0, 0, 0, 0.5);
    animation: zoomIn 0.3s ease;
}

.btn-cerrar-visor {
    position: absolute;
    top: 20px;
    right: 30px;
    color: white;
    font-size: 2rem;
    font-weight: bold;
    cursor: pointer;
}

.modal-header-crear {
    padding: 20px 30px;
    border-bottom: 1px solid #eee;
    background: #f9f9f9;
    border-radius: 16px 16px 0 0;
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

.campo input,
.campo select,
.campo textarea {
    width: 100%;
    padding: 12px;
    border: 2px solid #ecf0f1;
    border-radius: 8px;
    font-size: 1rem;
    box-sizing: border-box;
    font-family: inherit;
}

.divisor-form {
    border: 0;
    border-top: 1px dashed #bdc3c7;
    margin: 5px 0;
}

.texto-verde {
    color: #27ae60;
    font-weight: bold;
    font-size: 0.85rem;
    display: block;
    margin-top: 5px;
}

.mini-grilla-preview {
    display: flex;
    gap: 10px;
    margin-top: 10px;
    flex-wrap: wrap;
}

.mini-grilla-preview img {
    width: 60px;
    height: 60px;
    object-fit: cover;
    border-radius: 4px;
    border: 1px solid #ccc;
}

.alerta-edicion {
    background: #fff3e0;
    padding: 10px;
    border-radius: 6px;
    color: #d35400;
    border-left: 4px solid #f39c12;
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
    width: 100%;
    margin-top: 10px;
}

/* EVENTOS */
.eventos-movil-solo {
    display: none;
    /* Por defecto (PC) está oculto */
}

.tarjeta-widget {
    background: white;
    padding: 20px;
    border-radius: 12px;
    margin-bottom: 20px;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
}

.header-con-boton {
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 2px solid #f4f6f9;
    padding-bottom: 10px;
    margin-bottom: 15px;
}

.header-con-boton h3 {
    margin: 0;
    font-size: 1rem;
    color: #7f8c8d;
    text-transform: uppercase;
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
    cursor: pointer;
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
    position: relative;
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

.evento-info strong {
    font-size: 0.95rem;
    color: #2c3e50;
    display: block;
}

.evento-info small {
    color: #95a5a6;
    font-size: 0.8rem;
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
    font-size: 0.8rem;
    padding: 5px;
}

.item-evento-relativo:hover .btn-borrar-evento {
    opacity: 1;
}

/* HORARIO */
.horario-falsa-tabla {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    background: white;
    border: 1px solid #bdc3c7;
    border-radius: 8px;
    overflow: hidden;
}

.dia-columna {
    display: flex;
    flex-direction: column;
    border-right: 1px solid #ecf0f1;
}

.dia-titulo {
    background: #2c3e50;
    color: white;
    text-align: center;
    padding: 12px;
    font-weight: bold;
    text-transform: uppercase;
    font-size: 0.95rem;
    border-bottom: 2px solid #bdc3c7;
}

.bloque-clase {
    padding: 6px 4px;
    text-align: center;
    height: 60px;
    display: flex;
    flex-direction: column;
    justify-content: center;
}

.bloque-clase .tiempo {
    font-size: 0.7rem;
    color: #7f8c8d;
    margin-bottom: 2px;
}

.bloque-clase .materia {
    font-size: 0.85rem;
    color: #2c3e50;
    font-weight: bold;
    line-height: 1.1;
}

.bloque-recreo {
    height: 3px;
    background-color: #f1c40f;
    opacity: 0.7;
}

.bloque-almuerzo {
    background: #a9dfbf;
    padding: 4px;
    text-align: center;
    border-top: 1px solid #7dcea0;
    border-bottom: 1px solid #7dcea0;
    height: 50px;
    display: flex;
    flex-direction: column;
    justify-content: center;
}

.bloque-almuerzo .tiempo,
.bloque-almuerzo .materia {
    color: #145a32;
    font-size: 0.75rem;
    font-weight: bold;
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

@keyframes zoomIn {
    from {
        transform: scale(0.8);
        opacity: 0;
    }

    to {
        transform: scale(1);
        opacity: 1;
    }
}

.contenedor-menu-flotante {
    display: none;
    position: fixed;
    bottom: 20px;
    right: 20px;
    z-index: 2000;
}

.btn-fab {
    background: #2c3e50;
    color: white;
    border: none;
    padding: 15px 25px;
    border-radius: 30px;
    font-size: 1.1rem;
    font-weight: bold;
    cursor: pointer;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
    display: flex;
    align-items: center;
    gap: 8px;
    position: relative;
    z-index: 2002;
}

.overlay-menu-movil {
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    background: rgba(0, 0, 0, 0.5);
    backdrop-filter: blur(2px);
    z-index: 2000;
    animation: fadeIn 0.3s ease;
}

.opciones-flotantes {
    position: absolute;
    bottom: 70px;
    right: 0;
    background: white;
    border-radius: 16px;
    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
    width: 200px;
    overflow: hidden;
    z-index: 2001;
    opacity: 0;
    transform: translateY(20px);
    pointer-events: none;
    transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}

.opciones-flotantes.abierto {
    opacity: 1;
    transform: translateY(0);
    pointer-events: auto;
}

.opciones-flotantes ul {
    list-style: none;
    padding: 10px;
    margin: 0;
    display: flex;
    flex-direction: column;
    gap: 5px;
}

.opciones-flotantes li {
    padding: 15px;
    border-radius: 12px;
    font-size: 1rem;
    font-weight: bold;
    color: #34495e;
    cursor: pointer;
}

.opciones-flotantes li.activo {
    background: #e3f2fd;
    color: #3498db;
}

/* RESPONSIVE MÓVIL */
@media (max-width: 900px) {
    .muro-layout {
        grid-template-columns: 1fr;
    }

    .sidebar-left,
    .sidebar-right {
        display: none;
        /* Oculta barras laterales */
    }

    .eventos-movil-solo {
        display: block;
        /* Muestra eventos arriba de las noticias */
    }

    .contenedor-menu-flotante {
        display: block;
    }

    .horario-falsa-tabla {
        grid-template-columns: 1fr;
        border: none;
        box-shadow: none;
        background: transparent;
        gap: 15px;
    }

    .dia-columna {
        border: 1px solid #bdc3c7;
        border-radius: 8px;
        background: white;
        overflow: hidden;
    }

    .bloque-clase {
        border-bottom: 1px dashed #ecf0f1;
    }
}
</style>