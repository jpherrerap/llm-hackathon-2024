<template>
  <div id="app">
    <App />
    <Dashboard />
  </div>
</template>

<script>
import App from './MainChat.vue'
import Dashboard from './Dashboard.vue'

export default {
  name: 'Home',
  components: {
    App,
    Dashboard
  }
}
</script>

<style>
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: #2c3e50;
  margin-top: 60px;
}
</style>
