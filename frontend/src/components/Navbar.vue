<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '../axios'

const router = useRouter()
const nombreUsuario = ref('')
const menuAbierto = ref(false) // Estado para el menú móvil

// Variables de Permisos
const esDirectiva = ref(false) // Staff
const esTesorero = ref(false)  // Superuser

const verificarUsuario = async () => {
    try {
        const response = await api.get('quien-soy/')
        nombreUsuario.value = response.data.nombre_completo || response.data.username
        esDirectiva.value = response.data.es_staff
        esTesorero.value = response.data.es_admin
    } catch (error) {
        console.error("Error verificando usuario", error)
    }
}

const toggleMenu = () => {
    menuAbierto.value = !menuAbierto.value
}

const cerrarSesion = () => {
    localStorage.removeItem('token')
    window.location.href = '/'
}

onMounted(() => {
    verificarUsuario()
})
</script>

<template>
    <nav class="navbar">
        <div class="nav-container">
            <div class="nav-header">
                <div class="nav-brand">🎓 Portal 8°B</div>
                
                <button class="hamburger" @click="toggleMenu" :class="{ 'is-active': menuAbierto }">
                    <span></span>
                    <span></span>
                    <span></span>
                </button>
            </div>

            <div class="nav-links" :class="{ 'mobile-hidden': !menuAbierto }">
                
                <router-link to="/muro" class="nav-item" @click="menuAbierto = false">
                    🏠 Inicio
                </router-link>
                
                <router-link to="/mis-finanzas" class="nav-item" @click="menuAbierto = false">
                    💰 Mis Finanzas
                </router-link>

                <router-link v-if="esDirectiva || esTesorero" to="/tesoreria-resumen" class="nav-item-directiva" @click="menuAbierto = false">
                    📊 Tesorería
                </router-link>

                <router-link v-if="esTesorero" to="/gestion-total" class="nav-item-tesorero" @click="menuAbierto = false">
                    ⚡ Gestión Total
                </router-link>

                <div class="user-section">
                    <span class="saludo">Hola, <b>{{ nombreUsuario }}</b> 👋</span>
                    <button @click="cerrarSesion" class="btn-salir">Salir</button>
                </div>
            </div>
        </div>
    </nav>
</template>

<style scoped>
/* === ESTILOS GENERALES (PC) === */
.navbar {
    background: white;
    height: 60px; /* Altura fija para PC */
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
    position: sticky;
    top: 0;
    z-index: 1000;
}

.nav-container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 20px;
    height: 100%;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.nav-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    width: auto;
}

.nav-brand {
    font-weight: bold;
    font-size: 1.2rem;
    color: #2c3e50;
    margin-right: 30px;
}

.nav-links {
    display: flex;
    align-items: center;
    gap: 20px;
    flex-grow: 1;
    justify-content: space-between;
}

.nav-item {
    text-decoration: none;
    color: #7f8c8d;
    font-weight: 500;
    transition: color 0.3s;
    white-space: nowrap;
}
.nav-item:hover, .nav-item.router-link-active { color: #3498db; }

/* Botones Especiales */
.nav-item-directiva {
    text-decoration: none; color: #e67e22; font-weight: bold; background: #fff3e0;
    padding: 6px 12px; border-radius: 5px; transition: background 0.3s; white-space: nowrap;
}
.nav-item-directiva:hover { background: #ffe0b2; }

.nav-item-tesorero {
    text-decoration: none; color: #8e44ad; font-weight: bold; border: 1px dashed #8e44ad;
    padding: 5px 11px; border-radius: 5px; transition: background 0.3s; white-space: nowrap;
}
.nav-item-tesorero:hover { background: #f3e5f5; }

/* Sección Usuario */
.user-section {
    display: flex;
    align-items: center;
    gap: 15px;
    margin-left: auto; /* Empuja a la derecha en PC */
}

.saludo { color: #34495e; font-size: 0.9em; white-space: nowrap; }
.btn-salir {
    background: #e74c3c; color: white; border: none; padding: 6px 12px;
    border-radius: 4px; cursor: pointer; font-size: 0.9em;
}
.btn-salir:hover { background-color: #c0392b; }

/* Hamburguesa (Oculta en PC) */
.hamburger { display: none; }

/* === RESPONSIVE (MÓVIL) === */
@media (max-width: 900px) {
    .navbar { height: auto; padding: 10px 0; } /* Altura dinámica */
    
    .nav-container {
        flex-direction: column;
        align-items: stretch;
        padding: 0 15px;
    }

    .nav-header {
        width: 100%;
        height: 50px; /* Altura de la barra cerrada */
    }

    /* Botón Hamburguesa */
    .hamburger {
        display: block;
        background: none;
        border: none;
        cursor: pointer;
        padding: 10px;
    }
    .hamburger span {
        display: block;
        width: 25px;
        height: 3px;
        margin: 5px auto;
        background-color: #2c3e50;
        transition: all 0.3s ease-in-out;
    }
    /* Animación X */
    .hamburger.is-active span:nth-child(2) { opacity: 0; }
    .hamburger.is-active span:nth-child(1) { transform: translateY(8px) rotate(45deg); }
    .hamburger.is-active span:nth-child(3) { transform: translateY(-8px) rotate(-45deg); }

    /* Menú Desplegable */
    .nav-links {
        flex-direction: column;
        gap: 15px;
        background: white;
        border-top: 1px solid #f0f0f0;
        padding: 20px 0;
        margin-top: 10px;
        /* Animación suave */
        transition: max-height 0.3s ease-in-out, opacity 0.3s ease-in-out;
        max-height: 500px;
        opacity: 1;
    }

    .nav-links.mobile-hidden {
        display: none; /* Se oculta totalmente */
    }

    .user-section {
        margin-left: 0;
        flex-direction: column;
        width: 100%;
        border-top: 1px solid #eee;
        padding-top: 15px;
    }
    
    .btn-salir { width: 100%; padding: 10px; }
}
</style>