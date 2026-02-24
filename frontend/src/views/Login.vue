<script setup>
import { ref } from 'vue'
// import axios from 'axios' <--- BORRA ESTO, ya no usamos el axios "crudo"
import api from '../axios' // <--- NUEVO: Importamos tu archivo axios.js maestro con la URL de Railway

// import { useRouter } from 'vue-router' <--- BORRA ESTO, NO LO USAREMOS AHORA

// Variables para el formulario
const username = ref('')
const password = ref('')
const error = ref('')
const cargando = ref(false)

const iniciarSesion = async () => {
    error.value = ''
    cargando.value = true

    try {
        // 1. Pedir la "Pulsera" (Token) a Django
        // Asegúrate de que esta URL sea correcta (http://localhost:8000 o http://127.0.0.1:8000)

        // 👇 CAMBIO CLAVE: Usamos 'api.post' y solo ponemos 'token/' porque la ruta completa ya vive en tu axios.js
        const response = await api.post('token/', {
            username: username.value,
            password: password.value
        })

        // 2. Guardar el Token en el "Bolsillo"
        localStorage.setItem('token', response.data.access)
        localStorage.setItem('refresh_token', response.data.refresh)

        // 3. LA SOLUCIÓN NUCLEAR ☢️
        // En vez de router.push, forzamos una recarga completa.
        // Esto mata cualquier pantalla negra "zombie" y limpia la memoria.
        window.location.href = '/muro'

    } catch (err) {
        console.error(err)
        // Manejo de errores un poco más detallado
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
                    <input type="text" v-model="username" placeholder="Ej: admin" required />
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
.login-container {
    display: flex;
    justify-content: center;
    align-items: center;
    height: 80vh;
    /* Ocupa casi toda la pantalla */
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
}

button:hover {
    background-color: #2980b9;
}

button:disabled {
    background-color: #95a5a6;
}

.error-msg {
    color: red;
    font-weight: bold;
    margin-top: 10px;
}
</style>