<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router' // ✨ NUEVO: Importamos el enrutador para una navegación ultra rápida
import api from '../axios' // Tu archivo maestro con la URL de Railway

const router = useRouter() // Instanciamos el enrutador

// Variables reactivas para el formulario
const username = ref('')
const password = ref('')
const error = ref('')
const cargando = ref(false)

const iniciarSesion = async () => {
    error.value = ''
    cargando.value = true

    try {
        // 1. Pedir la "Pulsera" (Tokens) a Django
        const response = await api.post('token/', {
            username: username.value,
            password: password.value
        })

        // 2. Guardar el Token en el "Bolsillo" (Navegador)
        const token = response.data.access
        localStorage.setItem('token', token)
        localStorage.setItem('refresh_token', response.data.refresh)

        // 3. LA PREGUNTA DE SEGURIDAD 🕵️‍♂️
        // CORRECCIÓN: Usamos 'quien-soy/' (con guion medio) para que coincida con urls.py
        const userResponse = await api.get('quien-soy/', {
            headers: {
                Authorization: `Bearer ${token}` // Le mostramos la pulsera a Django
            }
        })

        // 4. GUARDAR LA MARCA Y REDIRIGIR 🧠
        const debeCambiarClave = userResponse.data.debe_cambiar_clave

        // Guardamos si es "true" o "false" para que nuestro Guardia de Rutas lo sepa
        localStorage.setItem('debe_cambiar_clave', debeCambiarClave)

        // Redirección Inteligente (usando router.push para que no parpadee la pantalla)
        if (debeCambiarClave) {
            router.push('/primer-ingreso') // ¡Atrapado! Lo mandamos a cambiar clave
        } else {
            router.push('/muro') // ¡Pase libre! Usuario antiguo
        }

    } catch (err) {
        console.error('Error detallado:', err)
        if (err.response && err.response.status === 401) {
            error.value = 'Usuario o contraseña incorrectos ❌'
        } else {
            error.value = 'Error de conexión con el servidor ⚠️'
        }
    } finally {
        cargando.value = false
    }
}
</script>

<template>
    <div class="login-container">
        <div class="login-box">
            <h1>🔐 Ingreso al Portal</h1>
            <p class="subtitulo">Gestión de Tesorería Escolar</p>

            <form @submit.prevent="iniciarSesion">
                <div class="campo">
                    <label>Usuario</label>
                    <input type="text" v-model="username" placeholder="Ej: apoderado1" required />
                </div>

                <div class="campo">
                    <label>Contraseña</label>
                    <input type="password" v-model="password" placeholder="••••••" required />
                </div>

                <p v-if="error" class="error-msg">{{ error }}</p>

                <button type="submit" :disabled="cargando">
                    {{ cargando ? 'Verificando...' : 'Ingresar' }}
                </button>
            </form>
        </div>
    </div>
</template>

<style scoped>
/* Estilos limpios y modernos */
.login-container {
    display: flex;
    justify-content: center;
    align-items: center;
    height: 80vh;
}

.login-box {
    background: white;
    padding: 40px;
    border-radius: 10px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
    width: 100%;
    max-width: 400px;
    text-align: center;
}

.subtitulo {
    color: #777;
    margin-bottom: 20px;
}

.campo {
    margin-bottom: 15px;
    text-align: left;
}

.campo label {
    display: block;
    font-weight: bold;
    margin-bottom: 5px;
    color: #333;
}

.campo input {
    width: 100%;
    padding: 10px;
    border: 1px solid #ddd;
    border-radius: 5px;
    font-size: 16px;
    /* Evita que el input se salga de la caja */
    box-sizing: border-box;
}

button {
    width: 100%;
    padding: 12px;
    background-color: #3498db;
    color: white;
    border: none;
    border-radius: 5px;
    font-size: 16px;
    cursor: pointer;
    margin-top: 10px;
    transition: background-color 0.3s;
}

button:hover {
    background-color: #2980b9;
}

button:disabled {
    background-color: #95a5a6;
    cursor: not-allowed;
}

.error-msg {
    color: #e74c3c;
    font-weight: bold;
    margin-top: 10px;
}
</style>