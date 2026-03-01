import { afterEach, describe, expect, it } from 'vitest'
import { createApp, defineComponent, h, nextTick } from 'vue'
import UiYamlPreviewModal from './UiYamlPreviewModal.vue'

function mountUiYamlPreviewModal(runtime: any) {
  const host = document.createElement('div')
  document.body.appendChild(host)
  const events: string[] = []

  const Root = defineComponent({
    components: { UiYamlPreviewModal },
    render() {
      return h(UiYamlPreviewModal, {
        open: true,
        runtime,
        onClose: () => events.push('close'),
      })
    },
  })

  const app = createApp(Root)
  app.provide('tr', (text: string) => text)
  app.mount(host)
  return {
    host,
    events,
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

describe('UiYamlPreviewModal interactions', () => {
  it('shows parse error and emits close', async () => {
    const vm = mountUiYamlPreviewModal({
      parseError: { message: 'bad yaml', path: 'root.a', line: 10, column: 2 },
      lastGoodConfig: null,
      widgetsById: {},
    })
    expect(vm.host.textContent).toContain('bad yaml')
    const closeButton = vm.host.querySelector('.icon-btn') as HTMLButtonElement
    closeButton?.click()
    await tick()
    expect(vm.events).toContain('close')
    vm.unmount()
  })

  it('shows empty state when no parse error and no layout', () => {
    const vm = mountUiYamlPreviewModal({
      parseError: null,
      lastGoodConfig: null,
      widgetsById: {},
    })
    expect(vm.host.textContent).toContain('暂无可渲染的 UI 配置')
    vm.unmount()
  })
})
