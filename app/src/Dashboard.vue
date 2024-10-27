<template>
  <div class="dashboard">
    <h1 class="text-2xl font-bold mb-4">Ticket Dashboard</h1>
    <div class="grid grid-cols-2 gap-4">
      <div>
        <h2 class="text-xl font-semibold mb-2">Open Tickets</h2>
        <TicketList :tickets="openTickets" />
      </div>
      <div>
        <h2 class="text-xl font-semibold mb-2">Resolved Tickets</h2>
        <TicketList :tickets="resolvedTickets" />
      </div>
    </div>
  </div>
</template>

<script>
import TicketList from './components/TicketList.vue';

export default {
  name: 'Dashboard',
  components: {
    TicketList,
  },
  data() {
    return {
      tickets: [],
    };
  },
  computed: {
    openTickets() {
      return this.tickets.filter(ticket => !ticket.resolved);
    },
    resolvedTickets() {
      return this.tickets.filter(ticket => ticket.resolved);
    },
  },
  mounted() {
    this.fetchTickets();
  },
  methods: {
    async fetchTickets() {
      try {
        const response = await fetch('/api/tickets');
        this.tickets = await response.json();
      } catch (error) {
        console.error('Error fetching tickets:', error);
      }
    },
  },
};
</script>
