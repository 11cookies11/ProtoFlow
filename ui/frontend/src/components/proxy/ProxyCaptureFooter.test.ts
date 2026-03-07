import { afterEach, describe, expect, it } from 'vitest'
import { createApp, defineComponent, h, nextTick, ref } from 'vue'
import ProxyCaptureFooter from './ProxyCaptureFooter.vue'

function mountFooter(metaValue: any) {
  const host = document.createElement('div')
  document.body.appendChild(host)
  const events: string[] = []
  const meta = ref(metaValue)

  const Root = defineComponent({
    render() {
      return h(ProxyCaptureFooter, {
        captureMeta: meta.value,
        onPageFirst: () => events.push('first'),
        onPagePrev: () => events.push('prev'),
        onPageNext: () => events.push('next'),
        onPageLast: () => events.push('last'),
        onExport: () => events.push('export'),
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

describe('ProxyCaptureFooter', () => {
  it('emits page and export actions when enabled', async () => {
    const vm = mountFooter({ page: 2, pageCount: 4, bufferUsed: 10, rangeStart: 1, rangeEnd: 20, totalFrames: 99 })
    const buttons = vm.host.querySelectorAll('button')
    ;(buttons[0] as HTMLButtonElement).click()
    ;(buttons[1] as HTMLButtonElement).click()
    ;(buttons[2] as HTMLButtonElement).click()
    ;(buttons[3] as HTMLButtonElement).click()
    ;(buttons[4] as HTMLButtonElement).click()
    await tick()
    expect(vm.events).toEqual(['first', 'prev', 'next', 'last', 'export'])
    vm.unmount()
  })
})
