<template>
  <Layout>
    <template #layout-bottom>
      <ChatWidget />
    </template>
  </Layout>
</template>

<script setup>
import DefaultTheme from 'vitepress/theme'
import ChatWidget from './components/ChatWidget.vue'

const { Layout } = DefaultTheme
</script>