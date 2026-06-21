import { defineConfig } from 'vitepress'

// https://vitepress.dev/reference/site-config
export default defineConfig({
  title: "Зеленый уголок",
  description: "База знаний по уходу за комнатными растениями, болезням и размножению",
  ignoreDeadLinks: true,
  base: '/siteUni/',
  head: [
    ['link', { rel: 'icon', href: '/favicon.png' }]
  ],
  themeConfig: {
    // https://vitepress.dev/reference/default-theme-config
    nav: [
      { text: 'Главная страница', link: '/' },
      { text: 'AI ассистент', link: '/AIintroduction' },
      { text: 'Рецепты', link: '/recipes' },
      { text: 'Уход', link: '/care' },
      { text: 'Статьи', link: '/plants' }
    ],

    sidebar: [
      {
        text: 'Навигация',
        items: [
          { text: 'Начать знакомство с AI ассистентом', link: '/AIintroduction' },
          { text: 'Статьи о растениях', link: '/plants/' },
          { text: 'Правильный уход', link: '/care/' },
          { text: 'Готовые рецепты', link: '/recipes/' }
        ]
      }
    ]
  }
})
