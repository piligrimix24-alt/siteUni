import { defineConfig } from 'vitepress'

// https://vitepress.dev/reference/site-config
export default defineConfig({
  title: "Зеленый уголок",
  description: "База знаний по уходу за комнатными растениями, болезням и размножению",
  themeConfig: {
    // https://vitepress.dev/reference/default-theme-config
    nav: [
      { text: 'Главная страница', link: '/' },
      { text: 'AI ассистент', link: '/' },//Добавить ссылку на страницу с иишкой
      { text: 'Рецепты', link: '/recipes' },
      { text: 'Уход', link: '/care' },
      { text: 'Статьи', link: '/plants' }
    ],

    sidebar: [
      {
        text: 'Examples',
        items: [
          { text: 'Markdown Examples', link: '/markdown-examples' },
          { text: 'Мята', link: '/plants/mint' }
        ]
      }
    ],

    // socialLinks: [
    //   { icon: 'github', link: 'https://github.com/vuejs/vitepress' }
    // ]
  }
})
