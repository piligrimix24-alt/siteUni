<template>
  <div class="chat-widget">
    <!-- Кнопка для открытия чата -->
    <button class="chat-toggle" @click="toggleChat">
      <span v-if="!isOpen">💬</span>
      <span v-else>✕</span>
    </button>

    <!-- Окно чата -->
    <div v-if="isOpen" class="chat-window">
      <div class="chat-header">
        <h3>🌱 AI-ассистент</h3>
        <p>Спросите о растениях, уходе или рецептах</p>
      </div>

      <div class="chat-messages" ref="messagesContainer">
        <div v-for="msg in messages" :key="msg.id" :class="['message', msg.role]">
          <div class="message-content">{{ msg.content }}</div>
        </div>
        <div v-if="isLoading" class="message assistant">
          <div class="message-content">🤔 Думаю...</div>
        </div>
      </div>

      <div class="chat-input">
        <input
          v-model="inputText"
          @keyup.enter="sendMessage"
          placeholder="Задайте вопрос..."
          :disabled="isLoading"
        />
        <button @click="sendMessage" :disabled="isLoading">➤</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick } from 'vue'

const isOpen = ref(false)
const inputText = ref('')
const isLoading = ref(false)
const messages = ref([
  { id: 1, role: 'assistant', content: '🌱 Привет! Я бот "Сада на подоконнике". Спрашивай о растениях, уходе и рецептах!' }
])

const messagesContainer = ref(null)

const toggleChat = () => {
  isOpen.value = !isOpen.value
}

const scrollToBottom = async () => {
  await nextTick()
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

const sendMessage = async () => {
  if (!inputText.value.trim() || isLoading.value) return

  const question = inputText.value
  inputText.value = ''

  messages.value.push({ id: Date.now(), role: 'user', content: question })
  scrollToBottom()

  isLoading.value = true

  try {
    const response = await fetch('http://localhost:8000/ask', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question: question })
    })

    const data = await response.json()

    if (data.answer) {
      messages.value.push({ id: Date.now(), role: 'assistant', content: data.answer })
    } else if (data.error) {
      messages.value.push({ id: Date.now(), role: 'assistant', content: `❌ Ошибка: ${data.error}` })
    }
  } catch (error) {
    messages.value.push({ id: Date.now(), role: 'assistant', content: `❌ Не удалось связаться с сервером. Убедитесь, что он запущен.` })
  }

  isLoading.value = false
  scrollToBottom()
}
</script>

<style>
.chat-widget {
  position: fixed;
  bottom: 20px;
  right: 20px;
  z-index: 9999;
  font-family: system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif;
}

.chat-toggle {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: #4caf50;
  border: none;
  color: white;
  font-size: 28px;
  cursor: pointer;
  box-shadow: 0 4px 12px rgba(0,0,0,0.2);
  transition: transform 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}
.chat-toggle:hover {
  background: #45a049;
  transform: scale(1.05);
}

.chat-window {
  position: absolute;
  bottom: 70px;
  right: 0;
  width: 360px;
  height: 500px;
  background: white;
  border-radius: 20px;
  box-shadow: 0 8px 28px rgba(0,0,0,0.2);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border: 1px solid #e0e0e0;
}

.chat-header {
  padding: 14px 18px;
  background: #4caf50;
  color: white;
}
.chat-header h3 {
  margin: 0;
  font-size: 18px;
}
.chat-header p {
  margin: 5px 0 0;
  font-size: 12px;
  opacity: 0.9;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  background: #f9f9f9;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.message {
  display: flex;
}
.message.user {
  justify-content: flex-end;
}
.message.user .message-content {
  background: #4caf50;
  color: white;
  border-radius: 20px 20px 4px 20px;
  padding: 8px 14px;
  max-width: 80%;
  font-size: 14px;
}
.message.assistant {
  justify-content: flex-start;
}
.message.assistant .message-content {
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 20px 20px 20px 4px;
  padding: 8px 14px;
  max-width: 85%;
  font-size: 14px;
  color: #333;
}

.chat-input {
  display: flex;
  padding: 12px;
  background: white;
  border-top: 1px solid #eee;
  gap: 8px;
}
.chat-input input {
  flex: 1;
  padding: 10px 14px;
  border: 1px solid #ddd;
  border-radius: 40px;
  outline: none;
  font-size: 14px;
}
.chat-input input:focus {
  border-color: #4caf50;
}
.chat-input button {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: #4caf50;
  border: none;
  color: white;
  cursor: pointer;
  font-size: 18px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
.chat-input button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>