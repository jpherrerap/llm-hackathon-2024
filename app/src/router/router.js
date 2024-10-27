import { createRouter, createWebHistory } from 'vue-router'
import Home from '../Home.vue'
import Dashboard from '../Dashboard.vue'
import App from '../App.vue'
import ChatContent from '../components/ChatContent.vue'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home
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
