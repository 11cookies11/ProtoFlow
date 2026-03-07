import { describe, expect, it } from 'vitest'
import { isValidSerialPort, normalizeSerialPortList, normalizeSerialPortName, portOptionsWithFallback } from './serialPort'

describe('serialPort utils', () => {
  it('normalizes COM display names', () => {
    expect(normalizeSerialPortName('COM3 - USB Serial (115200)')).toBe('COM3')
    expect(normalizeSerialPortName(' com12 ')).toBe('COM12')
  })

  it('keeps non COM names and de-duplicates list', () => {
    const list = normalizeSerialPortList(['COM3 - USB', 'COM3', 'ttyUSB0', '', null])
    expect(list).toEqual(['COM3', 'ttyUSB0'])
  })

  it('validates serial port format', () => {
    expect(isValidSerialPort('COM9')).toBe(true)
    expect(isValidSerialPort('ttyUSB0')).toBe(true)
    expect(isValidSerialPort('bad port !')).toBe(false)
  })

  it('falls back to COM list when empty', () => {
    const items = portOptionsWithFallback([])
    expect(items[0]).toBe('COM1')
    expect(items.length).toBeGreaterThan(10)
  })
})
