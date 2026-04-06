<template>
    <div class="cambiar-clave-container">
        <div class="tarjeta-seguridad">
            <div class="icono-candado">🔐</div>
            <h2>Crea tu Contraseña</h2>

            <div v-if="!tieneCredenciales" class="mensaje-error">
                ❌ Enlace inválido. Asegúrate de hacer clic directamente en el enlace que enviamos a tu correo.
            </div>

            <div v-else-if="exito" class="mensaje-exito">
                ✅ ¡Contraseña actualizada con éxito!
                Tu cuenta ahora está segura y ya puedes ingresar al portal.

                <router-link to="/" class="btn-login-link">
                    Ir a Iniciar Sesión 🚀
                </router-link>
            </div>

            <form v-else @submit.prevent="enviarNuevaClave" class="formulario">
                <p class="instrucciones">
                    Ingresa una contraseña segura que puedas recordar fácilmente.
                </p>

                <label for="clave1">Nueva Contraseña:</label>
                <input type="password" id="clave1" v-model="nuevaClave" placeholder="Escribe tu nueva clave" required
                    minlength="6" />

                <label for="clave2">Confirma tu Contraseña:</label>
                <input type="password" id="clave2" v-model="confirmarClave" placeholder="Repite la clave" required
                    minlength="6" />

                <button type="submit" :disabled="cargando" class="btn-guardar">
                    {{ cargando ? 'Guardando...' : 'Guardar Contraseña' }}
                </button>

                <div v-if="error" class="mensaje-error">
                    ⚠️ {{ error }}
                </div>
            </form>
        </div>
    </div>
</template>

<script setup>
import { ref } from 'vue';
import { useRoute } from 'vue-router';
import api from '../axios'; // ✨ IMPORTANTE: Traemos a nuestro Cartero oficial (Axios)

// Herramienta de Vue Router para leer la URL (ej: ?token=123&uid=4)
const route = useRoute();

const nuevaClave = ref('');
const confirmarClave = ref('');
const cargando = ref(false);
const error = ref('');
const exito = ref(false);

// Extraemos las credenciales ocultas en el enlace del correo
const uid = route.query.uid;
const token = route.query.token;

// Verificamos si el enlace viene con los datos necesarios
const tieneCredenciales = ref(!!uid && !!token);

const enviarNuevaClave = async () => {
    // 1. Validación en el frontend: ¿Las contraseñas son iguales?
    if (nuevaClave.value !== confirmarClave.value) {
        error.value = 'Las contraseñas no coinciden. Inténtalo de nuevo.';
        return;
    }

    cargando.value = true;
    error.value = '';

    try {
        // 2. Golpeamos la puerta de confirmación local en Django usando Axios
        // 🛠️ CORRECCIÓN DE URL: Removido el 'seguridad/' basado en las URLs típicas
        const respuesta = await api.post('confirmar-clave/', {
            uid: uid,
            token: token,
            nueva_clave: nuevaClave.value
        });

        // Si todo sale bien (Status 200)
        exito.value = true;
        
        // 🧹 EL GOLPE DE GRACIA: Limpiar la trampa del navegador
        // Destruimos la orden de "debe cambiar clave" y borramos cualquier token viejo
        // Así, al volver a hacer Login, se generará una sesión 100% limpia.
        localStorage.removeItem('debe_cambiar_clave');
        localStorage.removeItem('token');
        localStorage.removeItem('refresh_token');
        
    } catch (e) {
        console.error("Error detallado:", e);
        // Atrapamos el error exacto que nos envíe Django a través de Axios
        if (e.response && e.response.data && e.response.data.error) {
            error.value = e.response.data.error;
        } else {
            error.value = 'El enlace caducó o es inválido. Vuelve a solicitar uno nuevo.';
        }
    } finally {
        cargando.value = false;
    }
};
</script>

<style scoped>
.cambiar-clave-container {
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
    max-width: 400px;
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

.btn-guardar {
    background-color: #2196F3;
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

.btn-guardar:hover {
    background-color: #1976D2;
}

.btn-guardar:disabled {
    background-color: #9e9e9e;
    cursor: not-allowed;
}

.mensaje-exito {
    background-color: #e8f5e9;
    color: #2e7d32;
    padding: 20px;
    border-radius: 8px;
    font-weight: bold;
    display: flex;
    flex-direction: column;
    gap: 15px;
}

.btn-login-link {
    display: inline-block;
    background-color: #4CAF50;
    color: white;
    padding: 10px 15px;
    border-radius: 6px;
    text-decoration: none;
    font-weight: normal;
}

.btn-login-link:hover {
    background-color: #45a049;
}

.mensaje-error {
    color: #d32f2f;
    font-size: 14px;
    margin-top: 10px;
    text-align: center;
}
</style>