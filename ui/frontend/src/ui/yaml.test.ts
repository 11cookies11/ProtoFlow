import { describe, expect, it } from 'vitest'
import { parseYamlUI } from './yaml'

describe('parseYamlUI', () => {
  it('parses valid yaml text', () => {
    const result = parseYamlUI('ui:\n  widgets: []\n  layout:\n    type: leaf\n    widgets: [a]')
    expect(result.ok).toBe(true)
    if (result.ok) {
      expect((result.value as any).ui.widgets).toEqual([])
    }
  })

  it('returns line and column on parse error', () => {
    const result = parseYamlUI('ui:\n  widgets:\n    - id: a\n      type: input.text\n  layout: [')
    expect(result.ok).toBe(false)
    if (!result.ok) {
      expect(result.error.message.length).toBeGreaterThan(0)
      expect(result.error.line).toBeTypeOf('number')
      expect(result.error.column).toBeTypeOf('number')
    }
  })
})
