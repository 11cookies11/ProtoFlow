import { describe, expect, it } from 'vitest'
import { withResult } from './withResult'

describe('withResult', () => {
  it('handles plain values', () => {
    let output = 0
    withResult(42, (value) => {
      output = value
    })
    expect(output).toBe(42)
  })

  it('handles promise values', async () => {
    let output = ''
    withResult(Promise.resolve('ok'), (value) => {
      output = value
    })
    await Promise.resolve()
    expect(output).toBe('ok')
  })
})
