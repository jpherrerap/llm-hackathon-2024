<template>
  <div class="dashboard">
    <div class="bg-blue-100 p-4 mb-4 relative h-24 overflow-hidden">
      <img src="@/assets/image.png" alt="Banner" class="absolute top-0 left-1/2 transform -translate-x-1/2 h-full w-auto">
      <h1 class="text-2xl font-bold text-navy relative z-10">RelaxAgent</h1>
    </div>
    <div class="p-4">
      <div class="grid gap-4">
        <div v-for="ticket in tickets" :key="ticket.id" class="bg-white p-4 rounded-lg shadow">
          <h2 class="text-xl font-semibold mb-2">{{ ticket.title }}</h2>
          <p class="text-sm text-gray-600 mb-2">{{ ticket.description }}</p>
          <div class="flex justify-between items-center text-sm">
            <span class="text-gray-500">Created: {{ formatDate(ticket.createdAt) }}</span>
            <span :class="['px-2 py-1 rounded', ticket.resolved ? 'bg-green-200 text-green-800' : 'bg-yellow-200 text-yellow-800']">
              {{ ticket.resolved ? 'Resolved' : 'Open' }}
            </span>
          </div>
          <div class="mt-4">
            <div class="flex items-center mb-2">
              <h3 class="font-semibold">Conversation:</h3>
              <button @click="toggleConversation(ticket)" class="ml-2 focus:outline-none">
                <span class="transform inline-block" :class="{ 'rotate-180': ticket.showConversation }">
                  &#9660;
                </span>
              </button>
            </div>
            <div v-if="ticket.showConversation">
              <div v-for="(message, index) in ticket.conversation" :key="index" class="mb-2">
                <strong>{{ message.role }}:</strong> {{ message.content }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'Dashboard',
  data() {
    return {
      tickets: [],
    };
  },
  mounted() {
    this.fetchTickets();
  },
  methods: {
    async fetchTickets() {
      try {
        const response = await fetch('http://localhost:8000/api/tickets');
        if (!response.ok) {
          throw new Error('Failed to fetch tickets');
        }
        const fetchedTickets = await response.json();
        this.tickets = fetchedTickets
          .map(ticket => ({
            ...ticket,
            showConversation: false
          }))
          .sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt)); // Sort tickets by createdAt in descending order
      } catch (error) {
        console.error('Error fetching tickets:', error);
      }
    },
    formatDate(date) {
      return new Date(date).toLocaleString();
    },
    toggleConversation(ticket) {
      ticket.showConversation = !ticket.showConversation;
    },
  },
};
</script>
