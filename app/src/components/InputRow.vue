<script>
export default {
    name: 'InputRow',
    props: {
        sendSocketMessage: {
            type: Function,
            required: true,
        },
    },
    data() {
        return {
            messageContent: '',
        };
    },
    methods: {
        async sendMessage(event) {
            // If the user presses enter, prevent the default form action
            if (event) {
                event.preventDefault();
            }

            if (this.messageContent.trim() !== '') {

                const newMessage = {
                    type: 'new_message',
                    content: this.messageContent,
                };
                this.sendSocketMessage(newMessage);
                this.messageContent = '';
            }
        },
        async clearMessages() {
            const newMessage = {
                type: 'clear_messages',
            };
            this.sendSocketMessage(newMessage);
        }
    }
}
</script>

<template>
  <div class='input-row flex items-stretch bg-white rounded-lg shadow-md p-2'>
    <button @click="clearMessages" class="btn-clear bg-red-500 text-white px-4 py-2 rounded-lg mr-2 hover:bg-red-600 transition-colors">Clear Chat</button>
    <textarea rows="3" v-model="this.messageContent" placeholder="Type a message" @keydown.enter="sendMessage" class="flex-grow border rounded-lg p-2 mr-2 focus:outline-none focus:ring-2 focus:ring-primary"></textarea>
    <button @click="sendMessage" class="btn-send bg-primary text-white px-4 py-2 rounded-lg hover:bg-blue-600 transition-colors">Send</button>
  </div>
</template>

<style scoped>
.input-row {
    display: flex;
    align-items: stretch;
    background-color: #fdf0d7;
    border-radius: 10px;
    box-shadow: 0 0 10px rgba(0, 0, 0, 0.2);
    padding: 10px;
    width: 100%;
}

textarea {
    flex-grow: 1;
    margin: 0 10px;
}

.input-row button {
    background-color: #f0e6fb;
    border: none;
    border-radius: 5px;
    padding: 10px;
    cursor: pointer;
    color: #00000089;
    box-shadow: 1px 2px 3px rgba(0, 0, 0, 0.25);
    transition: background-color 0.2s ease-in-out, box-shadow 0.1s ease-in-out;
}

button:hover {
    filter: brightness(0.9);
}

button:active {
    box-shadow: none;
}

.input-row .btn-clear {
    background-color: #f17b7b;
}

</style>
