<template>
    <div class="recuperar-clave-container">
        <div class="tarjeta-seguridad">
            <div class="icono-candado">📬</div>
            <h2>Recuperar Contraseña</h2>

            <div v-if="exito" class="mensaje-exito">
                ✅ ¡Enlace enviado! Revisa tu bandeja de entrada (y la de Spam).
                <br><br>
                <router-link to="/" class="btn-volver">Volver al inicio</router-link>
            </div>

            <div v-else-if="correoNoEncontrado" class="mensaje-error-especial">
                ⚠️ <strong>Correo no registrado</strong><br><br>
                El correo ingresado no se encuentra en nuestra base de datos.<br><br>
                Si eres apoderado del 8°B y no puedes acceder, por favor envía un correo directamente a:<br>
                <strong class="correo-soporte">generacion2030.coe@gmail.com</strong>
                <br><br>
                <router-link to="/" class="btn-volver">Volver al inicio</router-link>
            </div>

            <form v-else @submit.prevent="enviarCorreo" class="formulario">
                <p class="instrucciones">
                    Ingresa el correo electrónico asociado a tu cuenta y te enviaremos un enlace para crear una nueva
                    contraseña.
                </p>

                <label for="email">Tu Correo Electrónico:</label>
                <input type="email" id="email" v-model="correo" placeholder="ejemplo@gmail.com" required />

                <button type="submit" :disabled="cargando" class="btn-enviar">
                    {{ cargando ? 'Buscando en el sistema...' : 'Enviar Enlace de Recuperación' }}
                </button>

                <div v-if="error" class="mensaje-error">
                    ❌ {{ error }}
                </div>

                <div class="enlaces-extra">
                    <router-link to="/">Volver a Iniciar Sesión</router-link>
                </div>
            </form>
        </div>
    </div>
</template>

<script setup>
import { ref } from 'vue';
import api from '../axios';

const correo = ref('');
const cargando = ref(false);
const error = ref('');
const exito = ref(false);
const correoNoEncontrado = ref(false);

const enviarCorreo = async () => {
    cargando.value = true;
    error.value = '';
    correoNoEncontrado.value = false;

    try {
        // Golpeamos la nueva puerta que hicimos en Django
        await api.post('seguridad/recuperar-clave/', {
            correo: correo.value
        });

        // Si Django responde OK (Status 200)
        exito.value = true;

    } catch (e) {
        console.error("Error al recuperar:", e);
        // Si Django responde que no encontró el correo (Status 404)
        if (e.response && e.response.status === 404) {
            correoNoEncontrado.value = true;
        } else if (e.response && e.response.data && e.response.data.error) {
            error.value = e.response.data.error;
        } else {
            error.value = 'Error de conexión con el servidor.';
        }
    } finally {
        cargando.value = false;
    }
};
</script>

<style scoped>
.recuperar-clave-container {
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
    width: 100%;
    text-align: center;
}

.icono-candado {
    font-size: 50px;
    margin-bottom: 10px;
}

.instrucciones {
    color: #555;
    margin-bottom: 20px;
    font-size: 14px;
    line-height: 1.5;
}

.formulario {
    display: flex;
    flex-direction: column;
    gap: 15px;
    text-align: left;
}

label {
    font-weight: bold;
    color: #333;
    font-size: 14px;
}

input {
    padding: 12px;
    border: 1px solid #ccc;
    border-radius: 8px;
    font-size: 16px;
    width: 100%;
    box-sizing: border-box;
}

.btn-enviar {
    background-color: #3498db;
    color: white;
    padding: 12px;
    border: none;
    border-radius: 8px;
    font-size: 16px;
    cursor: pointer;
    font-weight: bold;
    margin-top: 10px;
    transition: background-color 0.3s;
}

.btn-enviar:hover {
    background-color: #2980b9;
}

.btn-enviar:disabled {
    background-color: #95a5a6;
    cursor: not-allowed;
}

.mensaje-exito {
    background-color: #e8f5e9;
    color: #2e7d32;
    padding: 20px;
    border-radius: 8px;
    font-weight: bold;
}

.mensaje-error-especial {
    background-color: #ffebee;
    color: #c62828;
    padding: 20px;
    border-radius: 8px;
    font-size: 15px;
    line-height: 1.4;
}

.correo-soporte {
    color: #b71c1c;
    font-size: 16px;
    display: block;
    margin-top: 10px;
}

.mensaje-error {
    color: #d32f2f;
    font-size: 14px;
    text-align: center;
}

.btn-volver {
    display: inline-block;
    background-color: #7f8c8d;
    color: white;
    padding: 10px 15px;
    border-radius: 6px;
    text-decoration: none;
    font-weight: normal;
    margin-top: 10px;
}

.btn-volver:hover {
    background-color: #95a5a6;
}

.enlaces-extra {
    text-align: center;
    margin-top: 15px;
    font-size: 14px;
}

.enlaces-extra a {
    color: #3498db;
    text-decoration: none;
}

.enlaces-extra a:hover {
    text-decoration: underline;
}
</style>