import { describe, expect, it } from 'vitest'
import { validateUIConfig } from './schema'

function validConfig() {
  return {
    ui: {
      widgets: [
        { id: 'wifi-ssid', type: 'input.text', props: { label: 'WiFi SSID' }, bind: 'wifi.ssid' },
        { id: 'apply', type: 'action.button', props: { label: 'Apply' }, emit: 'action.wifi.apply' },
      ],
      layout: {
        type: 'leaf',
        title: 'Network',
        widgets: ['wifi-ssid', 'apply'],
      },
    },
  }
}

describe('validateUIConfig', () => {
  it('accepts valid config', () => {
    const result = validateUIConfig(validConfig())
    expect(result.ok).toBe(true)
  })

  it('rejects duplicate widget id', () => {
    const cfg = validConfig()
    cfg.ui.widgets.push({ id: 'apply', type: 'input.text', props: {} })
    const result = validateUIConfig(cfg)
    expect(result.ok).toBe(false)
    if (!result.ok) {
      expect(result.error.path).toBe('ui.widgets')
      expect(result.error.message).toContain('duplicate widget id')
    }
  })

  it('rejects layout reference to unknown widget id', () => {
    const cfg = validConfig()
    cfg.ui.layout.widgets.push('missing-id')
    const result = validateUIConfig(cfg)
    expect(result.ok).toBe(false)
    if (!result.ok) {
      expect(result.error.path).toBe('ui.layout')
      expect(result.error.message).toContain('unknown widget id')
    }
  })
})
