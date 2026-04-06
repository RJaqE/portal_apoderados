<template>
    <div class="primer-ingreso-container">
        <div class="tarjeta-seguridad">
            <div class="icono-candado">🔒</div>
            <h2>¡Bienvenido al Portal!</h2>
            <p class="instrucciones">
                Por seguridad, como este es tu primer ingreso, necesitamos vincular tu cuenta a un <strong>correo
                    electrónico real</strong> para que puedas crear tu propia contraseña secreta.
            </p>

            <div v-if="correoEnviado" class="mensaje-exito">
                ✅ ¡Enlace enviado! Revisa tu bandeja de entrada (y la carpeta de Spam por si acaso).
                Haz clic en el enlace del correo para continuar.
            </div>

            <form v-else @submit.prevent="solicitarEnlace" class="formulario">
                <label for="email">Tu Correo Electrónico:</label>
                <input type="email" id="email" v-model="correo" placeholder="ejemplo@gmail.com" required />

                <button type="submit" :disabled="cargando" class="btn-enviar">
                    {{ cargando ? 'Enviando enlace...' : 'Enviar Enlace Mágico ✨' }}
                </button>

                <div v-if="error" class="mensaje-error">
                    ❌ {{ error }}
                </div>
            </form>

            <button @click="cerrarSesion" class="btn-cerrar-sesion">
                Cerrar sesión por ahora
            </button>
        </div>
    </div>
</template>

<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router'; // 👈 Importamos el router
import api from '../axios';

const router = useRouter(); // 👈 Instanciamos el router
const correo = ref('');
const cargando = ref(false);
const correoEnviado = ref(false);
const error = ref('');

const solicitarEnlace = async () => {
    cargando.value = true;
    error.value = '';

    try {
        const respuesta = await api.post('solicitar-enlace/', { // Asegúrate que esta ruta coincide con tu backend
            correo: correo.value
        });
        correoEnviado.value = true;
    } catch (e) {
        console.error("Error detallado:", e);
        if (e.response && e.response.data && e.response.data.error) {
            error.value = e.response.data.error;
        } else {
            error.value = 'Error de conexión con el servidor.';
        }
    } finally {
        cargando.value = false;
    }
};

// 👇 NUEVO: Función para limpiar la trampa y salir
const cerrarSesion = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('debe_cambiar_clave'); // Limpiamos la trampa
    router.push('/'); // Lo devolvemos al Login
};
</script>

<style scoped>
.primer-ingreso-container {
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 80vh;
    background-color: #f4f6f9;
    padding: 20px;
}

.tarjeta-seguridad {
    background: white;
    padding: 40px;
    border-radius: 12px;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
    max-width: 450px;
    text-align: center;
}

.icono-candado {
    font-size: 50px;
    margin-bottom: 10px;
}

.instrucciones {
    color: #555;
    margin-bottom: 25px;
    line-height: 1.5;
}

.formulario {
    display: flex;
    flex-direction: column;
    gap: 15px;
    text-align: left;
}

input {
    padding: 12px;
    border: 1px solid #ccc;
    border-radius: 8px;
    font-size: 16px;
}

.btn-enviar {
    background-color: #4CAF50;
    color: white;
    padding: 12px;
    border: none;
    border-radius: 8px;
    font-size: 16px;
    cursor: pointer;
    font-weight: bold;
    transition: background-color 0.3s;
}

.btn-enviar:hover {
    background-color: #45a049;
}

.btn-enviar:disabled {
    background-color: #9e9e9e;
    cursor: not-allowed;
}

.mensaje-exito {
    background-color: #e8f5e9;
    color: #2e7d32;
    padding: 15px;
    border-radius: 8px;
    font-weight: bold;
}

.mensaje-error {
    color: #d32f2f;
    font-size: 14px;
    margin-top: 10px;
    text-align: center;
}

/* 👇 NUEVO ESTILO */
.btn-cerrar-sesion {
    margin-top: 20px;
    background: none;
    border: none;
    color: #95a5a6;
    text-decoration: underline;
    cursor: pointer;
    font-size: 0.9rem;
    transition: color 0.2s;
}

.btn-cerrar-sesion:hover {
    color: #e74c3c;
}
</style>