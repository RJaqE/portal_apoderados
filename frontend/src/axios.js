import axios from 'axios'

const api = axios.create({
    baseURL: 'http://127.0.0.1:8000/api/',
    timeout: 5000, // Si tarda más de 5 seg, cancela
    headers: {
        'Content-Type': 'application/json',
    }
})

// 1. INTERCEPTOR DE SALIDA (Poner la pulsera)
// Antes de que salga el mensaje, le pegamos el token
api.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('token')
        if (token) {
            config.headers.Authorization = `Bearer ${token}`
        }
        return config
    },
    (error) => Promise.reject(error)
)

// 2. INTERCEPTOR DE LLEGADA (El Detector de 401) 🚨
// Si el servidor responde con error, revisamos qué pasó
api.interceptors.response.use(
    (response) => response, // Si todo bien, pasa
    (error) => {
        // Si el error es 401 (No autorizado / Token vencido)
        if (error.response && error.response.status === 401) {
            console.warn("🔒 Sesión caducada o inválida. Cerrando sesión...")
            
            // Borramos los tokens viejos
            localStorage.removeItem('token')
            localStorage.removeItem('refresh_token')

            // Forzamos la recarga hacia el Login
            window.location.href = '/'
        }
        return Promise.reject(error)
    }
)

export default api