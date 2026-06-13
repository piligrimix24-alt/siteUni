<template>
  <div class="chat-widget">
    <button class="chat-toggle" @click="toggleChat">
      <span v-if="!isOpen">💬</span>
      <span v-else>✕</span>
    </button>
    
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
          <div class="message-content">Думаю...</div>
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
  { id: 1, role: 'assistant', content: 'Привет! Я бот "Сада на подоконнике". Спрашивай о растениях, уходе и рецептах!' }
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
      messages.value.push({ id: Date.now(), role: 'assistant', content: ` Ошибка: ${data.error}` })
    }
  } catch (error) {
    messages.value.push({ id: Date.now(), role: 'assistant', content: ` Не удалось связаться с сервером. Убедитесь, что он запущен.` })
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
}

.chat-toggle {
  width: 56px;
  height: 56px;
  border-radius: 28px;
  background: #4caf50;
  border: none;
  color: white;
  font-size: 24px;
  cursor: pointer;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}

.chat-toggle:hover {
  background: #45a049;
}

.chat-window {
  position: absolute;
  bottom: 70px;
  right: 0;
  width: 350px;
  height: 450px;
  background: white;
  border-radius: 16px;
  box-shadow: 0 8px 24px rgba(0,0,0,0.2);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border: 1px solid #ddd;
}

.chat-header {
  padding: 12px 16px;
  background: #4caf50;
  color: white;
}

.chat-header h3 {
  margin: 0;
  font-size: 16px;
}

.chat-header p {
  margin: 4px 0 0;
  font-size: 12px;
  opacity: 0.9;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
  background: #f5f5f5;
}

.message {
  margin-bottom: 8px;
}

.message.user {
  text-align: right;
}

.message.user .message-content {
  display: inline-block;
  background: #4caf50;
  color: white;
  border-radius: 16px 16px 4px 16px;
  padding: 8px 12px;
  max-width: 80%;
  font-size: 14px;
}

.message.assistant .message-content {
  display: inline-block;
  background: white;
  border: 1px solid #ddd;
  border-radius: 16px 16px 16px 4px;
  padding: 8px 12px;
  max-width: 80%;
  font-size: 14px;
}

.chat-input {
  display: flex;
  padding: 12px;
  background: white;
  border-top: 1px solid #ddd;
  gap: 8px;
}

.chat-input input {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 20px;
  outline: none;
}

.chat-input input:focus {
  border-color: #4caf50;
}

.chat-input button {
  width: 36px;
  height: 36px;
  border-radius: 18px;
  background: #4caf50;
  border: none;
  color: white;
  cursor: pointer;
}

.chat-input button:disabled {
  opacity: 0.5;
}
</style>