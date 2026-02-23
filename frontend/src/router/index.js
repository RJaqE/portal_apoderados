import { createRouter, createWebHistory } from "vue-router";
import Login from "../views/Login.vue";
import Muro from "../views/Muro.vue";
import MisFinanzas from "../views/MisFinanzas.vue";

// === IMPORTS DE LAS VISTAS DE PODER ===
// 1. El Nuevo Dashboard (Gráficos y Tarjetas)
import TesoreriaDashboard from "../views/Tesoreria.vue";
// 2. La Antigua Vista (Tabla de Gestión detallada / "La Magia")
import PanelGestion from "../views/PanelTesoreroView.vue";

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: "/",
      name: "login",
      component: Login,
      meta: { requiresAuth: false }, // Público
    },
    {
      path: "/muro",
      name: "Muro",
      component: Muro,
      meta: { requiresAuth: true }, // 🔒 Privado
    },
    {
      path: "/mis-finanzas",
      name: "mis-finanzas",
      component: MisFinanzas,
      meta: { requiresAuth: true }, // 🔒 Privado
    },

    // === RUTA PARA DIRECTIVA Y TESORERO (El Resumen) ===
    // Conecta con el botón "📊 Resumen" del Navbar
    {
      path: "/tesoreria-resumen",
      name: "TesoreriaDashboard",
      component: TesoreriaDashboard,
      meta: { requiresAuth: true }, // 🔒 Privado
    },

    // === 🚑 CORRECCIÓN DE ERRORES (REDIRECCIÓN) ===
    // Esto arregla el error "No match found for /tesoreria".
    // Si algo intenta entrar a la ruta vieja, lo mandamos a la nueva.
    {
      path: "/tesoreria",
      redirect: "/tesoreria-resumen",
    },

    // === RUTA SOLO PARA EL TESORERO (Gestión Total) ===
    // Conecta con el botón "⚡ Gestión" del Navbar
    // Aquí cargamos la vista antigua 'PanelTesoreroView'
    {
      path: "/gestion-total",
      name: "PanelGestion",
      component: PanelGestion,
      meta: { requiresAuth: true }, // 🔒 Privado
    },
  ],
});

// === EL PORTERO (Guardia de Navegación) ===
router.beforeEach((to, from, next) => {
  // Verificamos en consola a dónde intenta ir el usuario
  console.log(`Intentando ir a: ${to.path}`);

  // Revisamos si la ruta necesita "Pase Especial" (Auth)
  const rutaProtegida = to.matched.some((record) => record.meta.requiresAuth);

  // Buscamos el token en el bolsillo
  const token = localStorage.getItem("token");

  if (rutaProtegida && !token) {
    // Si es protegida y NO tiene token -> ¡FUERA! Al Login.
    console.log("⛔ Acceso denegado. Redirigiendo al Login.");
    next("/");
  } else {
    // Si tiene token O la ruta es pública -> Pase.
    next();
  }
});

export default router;
