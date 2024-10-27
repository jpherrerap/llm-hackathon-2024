import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '../Dashboard.vue'
import MainChat from '../MainChat.vue'
import App from '../App.vue'

const routes = [
  {
    path: '/',
    name: 'App',
    component: App
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: Dashboard
  }
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes
})

export default router
