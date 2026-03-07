import { afterEach, describe, expect, it } from 'vitest'
import { createApp, defineComponent, h, nextTick } from 'vue'
import SettingsPanels from './SettingsPanels.vue'

function mountSettingsPanels() {
  const host = document.createElement('div')
  document.body.appendChild(host)
  const calls: string[] = []

  const Root = defineComponent({
    components: { SettingsPanels },
    data() {
      return {
        tab: 'general',
        uiLanguage: 'zh-CN',
        uiTheme: 'light',
        autoConnectOnStart: false,
      }
    },
    render() {
      return h(SettingsPanels, {
        settingsTab: this.tab,
        uiLanguage: this.uiLanguage,
        uiTheme: this.uiTheme,
        autoConnectOnStart: this.autoConnectOnStart,
        dslWorkspacePath: '/tmp/workspace',
        languageOptions: [
          { value: 'zh-CN', label: '简体中文' },
          { value: 'en-US', label: 'English (US)' },
        ],
        themeOptions: [
          { value: 'light', label: 'Light' },
          { value: 'dark', label: 'Dark' },
        ],
        onSetTab: (nextTab: string) => {
          calls.push(`tab:${nextTab}`)
          this.tab = nextTab
        },
        'onUpdate:uiLanguage': (nextValue: string) => {
          calls.push(`lang:${nextValue}`)
          this.uiLanguage = nextValue
        },
        'onUpdate:uiTheme': (nextValue: string) => {
          calls.push(`theme:${nextValue}`)
          this.uiTheme = nextValue
        },
        'onUpdate:autoConnectOnStart': (nextValue: boolean) => {
          calls.push(`auto:${nextValue}`)
          this.autoConnectOnStart = nextValue
        },
      })
    },
  })

  const app = createApp(Root)
  app.provide('t', (key: string) => key)
  app.provide('tr', (text: string) => text)
  app.mount(host)

  return {
    host,
    calls,
    unmount: () => {
      app.unmount()
      host.remove()
    },
  }
}

async function tick() {
  await nextTick()
  await Promise.resolve()
}

afterEach(() => {
  document.body.innerHTML = ''
})

describe('SettingsPanels interactions', () => {
  it('switches settings tab by clicking tab buttons', async () => {
    const vm = mountSettingsPanels()
    const pluginsTabButton = Array.from(vm.host.querySelectorAll('.tab-strip button')).find((item) =>
      item.textContent?.includes('settings.tab.plugins')
    ) as HTMLButtonElement
    pluginsTabButton?.click()
    await tick()

    expect(vm.calls).toContain('tab:plugins')
    vm.unmount()
  })

  it('updates auto connect toggle', async () => {
    const vm = mountSettingsPanels()
    const checkbox = vm.host.querySelector('input[type="checkbox"]') as HTMLInputElement
    checkbox.checked = true
    checkbox.dispatchEvent(new Event('change', { bubbles: true }))
    await tick()

    expect(vm.calls).toContain('auto:true')
    vm.unmount()
  })
})
