import { afterEach, describe, expect, it } from 'vitest'
import { createApp, defineComponent, h, nextTick } from 'vue'
import ProtocolCardsSection from './ProtocolCardsSection.vue'

function mountProtocolCardsSection(withCards = true) {
  const host = document.createElement('div')
  document.body.appendChild(host)
  const events: string[] = []
  const cards = withCards
    ? [
        {
          id: 'c1',
          name: 'Modbus RTU',
          desc: '',
          statusClass: 'badge-green',
          statusText: '已启用',
          source: 'custom',
          rows: [{ label: '版本', value: '1.0.0' }],
        },
      ]
    : []

  const Root = defineComponent({
    components: { ProtocolCardsSection },
    data() {
      return { tab: 'all' }
    },
    render() {
      return h(ProtocolCardsSection, {
        protocolTab: this.tab,
        filteredProtocolCards: cards,
        onSetTab: (nextTab: string) => {
          events.push(`tab:${nextTab}`)
          this.tab = nextTab
        },
        onCreate: () => events.push('create'),
        onDetails: () => events.push('details'),
        onDelete: () => events.push('delete'),
      })
    },
  })

  const app = createApp(Root)
  app.provide('t', (key: string) => key)
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

describe('ProtocolCardsSection interactions', () => {
  it('emits tab and item actions', async () => {
    const vm = mountProtocolCardsSection(true)
    const tabButton = Array.from(vm.host.querySelectorAll('.tab-strip button')).find((item) =>
      item.textContent?.includes('Modbus')
    ) as HTMLButtonElement
    tabButton?.click()
    await tick()

    const ghostButton = vm.host.querySelector('.protocol-actions .btn.btn-ghost') as HTMLButtonElement
    const deleteButton = vm.host.querySelector('.protocol-actions .icon-btn') as HTMLButtonElement
    ghostButton?.click()
    deleteButton?.click()
    await tick()

    expect(vm.events).toContain('tab:modbus')
    expect(vm.events).toContain('details')
    expect(vm.events).toContain('delete')
    vm.unmount()
  })

  it('shows empty state and emits create', async () => {
    const vm = mountProtocolCardsSection(false)
    const createButton = vm.host.querySelector('.protocol-card.empty .btn.btn-primary') as HTMLButtonElement
    createButton?.click()
    await tick()
    expect(vm.events).toContain('create')
    vm.unmount()
  })
})
