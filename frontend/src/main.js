import { createApp } from 'vue'
//import './style.css' // (Si tienes este archivo, déjalo. Si no, bórralo)
import App from './App.vue'
import router from './router' // 1. IMPORTAR EL ROUTER

const app = createApp(App)

app.use(router) // 2. ¡ESTO ES LO QUE FALTA! CONECTAR EL CABLE

app.mount('#app')