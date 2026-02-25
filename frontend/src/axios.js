import axios from "axios";

const api = axios.create({
  // === MODO LOCAL (Desactivado) ===
  //baseURL: "http://127.0.0.1:8000/api/",

  // === MODO PRODUCCIÓN (Activado) ===
  baseURL: 'https://portalapoderados-production.up.railway.app/api/',

  timeout: 5000, // Si tarda más de 5 seg, cancela
  headers: {
    "Content-Type": "application/json",
  },
});

// 1. INTERCEPTOR DE SALIDA (Poner la pulsera)
// Antes de que salga el mensaje, le pegamos el token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error),
);

// 2. INTERCEPTOR DE LLEGADA (El Detector de 401 Inteligente) 🚨
// Si el servidor responde con error, revisamos qué pasó
api.interceptors.response.use(
  (response) => response, // Si todo bien, pasa
  (error) => {
    // Si el error es 401 (No autorizado / Token vencido)
    if (error.response && error.response.status === 401) {
      console.warn("🔒 Sesión caducada o petición sin token.");

      // Borramos los tokens viejos por seguridad
      localStorage.removeItem("token");
      localStorage.removeItem("refresh_token");

      // 👇 LA MAGIA: Lista de "Zonas Seguras" donde el interceptor NO debe echarnos
      const rutasPublicas = ["/", "/recuperar-clave", "/cambiar-clave"];
      const rutaActual = window.location.pathname;

      // Si NO estamos en una zona segura, forzamos la expulsión al Login
      if (!rutasPublicas.includes(rutaActual)) {
        window.location.href = "/";
      }
    }
    return Promise.reject(error);
  },
);

export default api;
