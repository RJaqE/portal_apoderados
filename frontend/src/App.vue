<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import Navbar from './components/Navbar.vue'

const route = useRoute()

// Lógica: Ocultar la barra si estamos en el Login ('/')
const mostrarNavbar = computed(() => {
  return route.path !== '/' && route.name !== 'Login'
})
</script>

<template>
  <div class="app-container">
    <Navbar v-if="mostrarNavbar" />

    <router-view />
  </div>
</template>

<style>
/* --- ESTILOS GLOBALES --- */

/* 1. Reset básico del cuerpo */
body {
  margin: 0;
  padding: 0;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  background-color: #f4f6f9;

  /* EL MARTILLO: ¡Obliga a que siempre se pueda hacer scroll! */
  overflow-y: auto !important;
}

/* 2. ROMPE-CORTINAS (SweetAlert) */
.swal2-container:empty {
  display: none !important;
  pointer-events: none !important;
}

/* 3. ROMPE-CORTINAS (Bootstrap) */
.modal-backdrop {
  display: none !important;
  z-index: -1 !important;
  opacity: 0 !important;
}
</style>