<template>
  <div class="ticket-list">
    <div v-for="ticket in tickets" :key="ticket.id" class="ticket bg-white p-4 rounded-lg shadow mb-4">
      <h3 class="font-semibold">{{ ticket.title }}</h3>
      <p class="text-sm text-gray-600">{{ ticket.description }}</p>
      <div class="mt-2 flex justify-between items-center">
        <span class="text-xs text-gray-500">{{ formatDate(ticket.createdAt) }}</span>
        <span :class="['px-2 py-1 rounded text-xs', ticket.resolved ? 'bg-green-200 text-green-800' : 'bg-yellow-200 text-yellow-800']">
          {{ ticket.resolved ? 'Resolved' : 'Open' }}
        </span>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'TicketList',
  props: {
    tickets: {
      type: Array,
      required: true,
    },
  },
  methods: {
    formatDate(date) {
      return new Date(date).toLocaleDateString();
    },
  },
};
</script>
