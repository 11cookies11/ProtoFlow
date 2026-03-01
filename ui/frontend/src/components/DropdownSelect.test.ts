import { afterEach, describe, expect, it } from 'vitest'
import { createApp, defineComponent, h, nextTick } from 'vue'
import DropdownSelect from './DropdownSelect.vue'

function mountDropdown(props: Record<string, unknown> = {}) {
  const host = document.createElement('div')
  document.body.appendChild(host)

  const Root = defineComponent({
    components: { DropdownSelect },
    data() {
      return {
        value: 'COM3',
      }
    },
    render() {
      return h(DropdownSelect, {
        modelValue: this.value,
        'onUpdate:modelValue': (next: string) => {
          this.value = next
        },
        options: ['COM1', 'COM2', 'COM3'],
        ...props,
      })
    },
  })

  const app = createApp(Root)
  app.mount(host)

  return {
    host,
    app,
    getTrigger: () => host.querySelector('.select-trigger') as HTMLButtonElement | null,
    getRoot: () => host.querySelector('.select-wrap') as HTMLDivElement | null,
    getMenu: () => document.body.querySelector('.select-menu') as HTMLDivElement | null,
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
  document.body.classList.remove('dropdown-open')
})

describe('DropdownSelect interactions', () => {
  it('opens menu and marks aria/data state when clicked', async () => {
    const vm = mountDropdown()
    vm.getTrigger()?.click()
    await tick()

    expect(vm.getMenu()).not.toBeNull()
    expect(vm.getTrigger()?.getAttribute('aria-expanded')).toBe('true')
    expect(vm.getRoot()?.dataset.open).toBe('true')

    vm.unmount()
  })

  it('closes menu on Escape', async () => {
    const vm = mountDropdown()
    vm.getTrigger()?.click()
    await tick()
    window.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true }))
    await tick()

    expect(vm.getMenu()).toBeNull()
    expect(vm.getTrigger()?.getAttribute('aria-expanded')).toBe('false')

    vm.unmount()
  })

  it('closes when clicking outside', async () => {
    const vm = mountDropdown()
    vm.getTrigger()?.click()
    await tick()
    document.body.dispatchEvent(new Event('pointerdown', { bubbles: true }))
    await tick()

    expect(vm.getMenu()).toBeNull()
    expect(vm.getRoot()?.dataset.open).toBe('false')

    vm.unmount()
  })

  it('stays closed when disabled and exposes disabled reason', async () => {
    const vm = mountDropdown({ disabled: true, disabledReason: 'loading ports' })
    vm.getTrigger()?.click()
    await tick()

    expect(vm.getMenu()).toBeNull()
    expect(vm.getTrigger()?.getAttribute('aria-disabled')).toBe('true')
    expect(vm.getTrigger()?.getAttribute('title')).toBe('loading ports')

    vm.unmount()
  })
})
