import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { useUiRuntimeStore } from './uiRuntime'

describe('useUiRuntimeStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.restoreAllMocks()
    ;(window as any).bridge = undefined
  })

  it('updates runtime state when parse + validation succeeds', () => {
    const store = useUiRuntimeStore()

    store._handleParseResult({
      ok: true,
      value: {
        ui: {
          widgets: [{ id: 'w1', type: 'input.text', props: { label: 'Name' }, bind: 'name' }],
          layout: { type: 'leaf', widgets: ['w1'] },
        },
      },
    })

    expect(store.parseError).toBeNull()
    expect(store.lastGoodConfig).not.toBeNull()
    expect(store.widgetsById.w1).toBeDefined()
    expect(store.widgetsById.w1.bind).toBe('name')
  })

  it('stores parse error returned by bridge', () => {
    const store = useUiRuntimeStore()
    store._handleParseResult({
      ok: false,
      error: { message: 'bad yaml', line: 3, column: 8 },
    })

    expect(store.parseError).toEqual({
      message: 'bad yaml',
      line: 3,
      column: 8,
    })
  })

  it('pushData keeps only latest 200 events for a bind key', () => {
    const nowSpy = vi.spyOn(Date, 'now').mockReturnValue(1700000000000)
    const store = useUiRuntimeStore()

    for (let i = 0; i < 205; i += 1) {
      store.pushData('wifi.events', i)
    }

    expect(store.dataBus['wifi.events']).toHaveLength(200)
    expect((store.dataBus['wifi.events'][0] as any).value).toBe(5)
    expect((store.dataBus['wifi.events'][199] as any).value).toBe(204)
    nowSpy.mockRestore()
  })
})
