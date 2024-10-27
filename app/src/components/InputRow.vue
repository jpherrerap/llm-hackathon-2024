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
    <button @click="clearMessages" class="btn-clear bg-red-500 text-white p-2 rounded-lg mr-2 hover:bg-red-600 transition-colors">
      <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-6 h-6">
        <path stroke-linecap="round" stroke-linejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" />
      </svg>
    </button>
    <textarea rows="3" v-model="this.messageContent" placeholder="Type a message" @keydown.enter="sendMessage" class="flex-grow border rounded-lg p-2 mr-2 focus:outline-none focus:ring-2 focus:ring-primary"></textarea>
    <button @click="sendMessage" class="btn-send bg-primary text-white p-2 rounded-lg hover:bg-blue-600 transition-colors">
      <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-6 h-6">
        <path stroke-linecap="round" stroke-linejoin="round" d="M6 12L3.269 3.126A59.768 59.768 0 0121.485 12 59.77 59.77 0 013.27 20.876L5.999 12zm0 0h7.5" />
      </svg>
    </button>
  </div>
</template>

<style scoped>
.input-row {
    display: flex;
    align-items: stretch;
    background-color: #474973;
    border-radius: 10px;
    box-shadow: 0 0 10px rgba(0, 0, 0, 0.2);
    padding: 10px;
    width: 100%;
    height: 10%;
}

textarea {
    flex-grow: 1;
    margin: 0 10px;
    resize: none;
    height: 100%;
}

.input-row button {
    background-color: #161B33;
    border: none;
    border-radius: 5px;
    padding: 10px;
    cursor: pointer;
    color: #F1DAC4;
    box-shadow: 1px 2px 3px rgba(0, 0, 0, 0.25);
    transition: background-color 0.2s ease-in-out, box-shadow 0.1s ease-in-out;
}

button:hover {
    filter: brightness(1.5);
}

button:active {
    box-shadow: none;
}

.input-row .btn-clear {
    background-color: #161B33;
}

</style>
