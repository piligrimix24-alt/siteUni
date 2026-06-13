import DefaultTheme from 'vitepress/theme'
import './custom.css'
import ChatWidget from './components/ChatWidget.vue'

export default {
    extends: DefaultTheme,
    enhanceApp({ app, router, siteData }) {
        app.component('ChatWidget', ChatWidget)
    }
}