import { createApp } from 'vue'
import MainChat from './MainChat.vue'
import router from './router/router'
import App from './App.vue'
import './assets/tailwind.css'

createApp(App).use(router).mount('#app')
