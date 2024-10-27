<script>
export default {
    name: 'ChatBubble',
    props: {
        message: {
            type: Object,
            required: true,
        },
    },
}
</script>

<template>
  <div :class="['chat-bubble flex items-start mb-4', message.role]">
    <div :class="['chat-bubble-avatar w-10 h-10 rounded-full flex items-center justify-center text-white font-bold']">
      {{ message.role[0].toUpperCase() }}
    </div>
    <div :class="['chat-bubble-content rounded-lg p-3 max-w-[80%]']">
      {{ message.content }}
    </div>
  </div>
</template>

<style scoped>
.chat-bubble {
    display: flex;
    align-items: center;
    margin-bottom: 10px;
    flex-direction: row-reverse;
}

.chat-bubble.assistant {
    flex-direction: row;
}

.chat-bubble-avatar {
    flex-shrink: 0;
    background-color: #e1e1e1;
    border-radius: 50%;
    color: #000;
    font-weight: bold;
    height: 40px;
    width: 40px;
    line-height: 40px;
    margin-right: 10px;
    text-align: center;
    margin: 0px 10px;
    box-shadow: 0 0 5px rgba(0, 0, 0, 0.2);
}

.chat-bubble-content {
    border-radius: 10px;
    padding: 10px;
    box-shadow: 0 0 5px rgba(0, 0, 0, 0.2);
    max-width: 80%;
}

.user .chat-bubble-content {
    background-color: #161B33;
    color: #f2f2f2;
}

.assistant .chat-bubble-content{
    background-color: beige;
}
</style>
