import { afterEach, describe, expect, it } from 'vitest'
import { createApp, defineComponent, h, nextTick } from 'vue'
import ProtocolEditModal from './ProtocolEditModal.vue'

function mountProtocolEditModal() {
  const host = document.createElement('div')
  document.body.appendChild(host)
  const events: string[] = []

  const Root = defineComponent({
    components: { ProtocolEditModal },
    data() {
      return {
        draft: {
          name: 'A',
          key: 'a',
          category: 'custom',
          status: 'custom',
          desc: 'desc',
        },
      }
    },
    render() {
      return h(ProtocolEditModal, {
        open: true,
        mode: 'edit',
        draft: this.draft,
        editing: { driver: 'DriverX' },
        onClose: () => events.push('close'),
        onSave: () => events.push('save'),
        onUpdateDraft: ({ field, value }: { field: string; value: string }) => {
          events.push(`update:${field}:${value}`)
          this.draft = { ...this.draft, [field]: value }
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

describe('ProtocolEditModal interactions', () => {
  it('emits field updates and save', async () => {
    const vm = mountProtocolEditModal()
    const nameInput = vm.host.querySelector('input[type="text"]') as HTMLInputElement
    nameInput.value = 'NewName'
    nameInput.dispatchEvent(new Event('input', { bubbles: true }))
    const saveButton = Array.from(vm.host.querySelectorAll('.modal-footer button')).find((item) =>
      item.textContent?.includes('保存')
    ) as HTMLButtonElement
    saveButton?.click()
    await tick()

    expect(vm.events.find((item) => item.startsWith('update:name:'))).toBeTruthy()
    expect(vm.events).toContain('save')
    vm.unmount()
  })
})
