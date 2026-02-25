import { createRouter, createWebHistory } from "vue-router";
import Login from "../views/Login.vue";
import Muro from "../views/Muro.vue";
import MisFinanzas from "../views/MisFinanzas.vue";

// === IMPORTS DE LAS VISTAS DE PODER ===
import TesoreriaDashboard from "../views/Tesoreria.vue";
import PanelGestion from "../views/PanelTesoreroView.vue";

// === IMPORTS DE SEGURIDAD ===
import PrimerIngreso from "../views/PrimerIngreso.vue";
import CambiarClave from "../views/CambiarClave.vue";
// (RecuperarClave la importaremos directamente abajo para optimizar la carga)

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: "/",
      name: "login",
      component: Login,
      meta: { requiresAuth: false }, // Público
    },

    // 👇 NUEVA RUTA: Olvidé mi contraseña
    {
      path: "/recuperar-clave",
      name: "RecuperarClave",
      // Carga perezosa: solo carga este archivo si el usuario hace clic en el enlace
      component: () => import("../views/RecuperarClave.vue"),
      meta: { requiresAuth: false }, // Público (no necesita token)
    },

    // La "Trampa" obligatoria para usuarios nuevos
    {
      path: "/primer-ingreso",
      name: "PrimerIngreso",
      component: PrimerIngreso,
      meta: { requiresAuth: true }, // Requiere estar logueado con la clave temporal
    },

    // La pantalla que se abre al hacer clic en el correo
    {
      path: "/cambiar-clave",
      name: "CambiarClave",
      component: CambiarClave,
      meta: { requiresAuth: false }, // Pública, porque llega desde su correo sin estar logueado
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
    {
      path: "/tesoreria-resumen",
      name: "TesoreriaDashboard",
      component: TesoreriaDashboard,
      meta: { requiresAuth: true }, // 🔒 Privado
    },
    {
      path: "/tesoreria",
      redirect: "/tesoreria-resumen",
    },
    {
      path: "/gestion-total",
      name: "PanelGestion",
      component: PanelGestion,
      meta: { requiresAuth: true }, // 🔒 Privado
    },
  ],
});

// === EL PORTERO (Guardia de Navegación Mejorado) ===
router.beforeEach((to, from, next) => {
  console.log(`Intentando ir a: ${to.path}`);

  const rutaProtegida = to.matched.some((record) => record.meta.requiresAuth);
  const token = localStorage.getItem("token");

  // Leemos si el usuario tiene la marca de novato en su navegador
  // (Esto lo guardaremos en el Login más adelante)
  const debeCambiarClave =
    localStorage.getItem("debe_cambiar_clave") === "true";

  if (rutaProtegida && !token) {
    // Sin token -> ¡FUERA! Al Login.
    console.log("⛔ Acceso denegado. Redirigiendo al Login.");
    next("/");
  } else if (rutaProtegida && token) {
    // === EL NUEVO FILTRO DE SEGURIDAD ===
    if (debeCambiarClave && to.path !== "/primer-ingreso") {
      // Si DEBE cambiar su clave, y está intentando ir a cualquier otra parte, lo atrapamos
      console.log("🔒 Usuario nuevo detectado. Redirigiendo a Primer Ingreso.");
      next("/primer-ingreso");
    } else if (!debeCambiarClave && to.path === "/primer-ingreso") {
      // Si NO DEBE cambiar clave, pero intenta entrar a /primer-ingreso por curiosidad, lo sacamos
      console.log("✅ El usuario ya es seguro. Redirigiendo al Muro.");
      next("/muro");
    } else {
      // Si todo está en orden -> Pase libre.
      next();
    }
  } else {
    // Si es una ruta pública (como /, /cambiar-clave o /recuperar-clave) -> Pase libre.
    next();
  }
});

export default router;
