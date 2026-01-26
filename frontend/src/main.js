import { createApp } from 'vue'
import { createPinia } from 'pinia'
import './style.css'
import App from './App.vue'

function initWebChannel() {
  if (!window.qt || !window.qt.webChannelTransport) {
    return Promise.resolve(null)
  }
  return new Promise((resolve) => {
    // eslint-disable-next-line no-undef
    new QWebChannel(window.qt.webChannelTransport, (channel) => {
      const bridge = channel.objects.bridge
      window.bridge = bridge
      resolve(bridge)
    })
  })
}

async function bootstrap() {
  const bridge = await initWebChannel()
  if (bridge) {
    bridge.log.connect((msg) => {
      console.log('[bridge]', msg)
    })
    bridge.notify_ready()
    bridge.ping('frontend').then((resp) => console.log(resp))
  }
  const app = createApp(App)
  app.use(createPinia())
  app.mount('#app')
}

bootstrap()
