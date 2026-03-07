import { describe, expect, it } from 'vitest'
import { calculateWindowRange } from './useWindowedList'

describe('useWindowedList helpers', () => {
  it('returns zero range for empty list', () => {
    expect(calculateWindowRange(0, 36, 400, 0)).toEqual({ start: 0, end: 0, topOffset: 0, bottomOffset: 0 })
  })

  it('computes in-view window with offsets', () => {
    const range = calculateWindowRange(1000, 20, 200, 400, 5, 10)
    expect(range.start).toBeGreaterThan(0)
    expect(range.end).toBeGreaterThan(range.start)
    expect(range.topOffset).toBe(range.start * 20)
    expect(range.bottomOffset).toBe((1000 - range.end) * 20)
  })

  it('clamps end within item count', () => {
    const range = calculateWindowRange(15, 30, 600, 0, 10, 20)
    expect(range.start).toBe(0)
    expect(range.end).toBe(15)
    expect(range.bottomOffset).toBe(0)
  })
})
