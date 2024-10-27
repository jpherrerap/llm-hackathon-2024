<script setup>
import { ref, computed } from 'vue'
import MainChat from './MainChat.vue'
import Dashboard from './Dashboard.vue'

const routes = {
  '/': MainChat,
  '/dashboard': Dashboard
}

const currentPath = ref(window.location.hash)

window.addEventListener('hashchange', () => {
  currentPath.value = window.location.hash
})

const currentView = computed(() => {
  return routes[currentPath.value.slice(1) || '/'] || NotFound
})
</script>

<template>
  <component :is="currentView" />
</template>