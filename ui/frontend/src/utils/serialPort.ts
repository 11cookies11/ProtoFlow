import { fallbackPorts } from '@/config/runtimeDefaults'

export function normalizeSerialPortName(value: unknown): string {
  const raw = String(value ?? '').trim()
  if (!raw) return ''
  const match = raw.match(/COM\d+/i)
  if (match) return match[0].toUpperCase()
  return raw
}

export function normalizeSerialPortList(items: unknown): string[] {
  if (!Array.isArray(items)) return []
  const seen = new Set<string>()
  const result: string[] = []
  for (const item of items) {
    const name = normalizeSerialPortName(item)
    if (!name || seen.has(name)) continue
    seen.add(name)
    result.push(name)
  }
  return result
}

export function isValidSerialPort(value: unknown): boolean {
  return /^[A-Za-z0-9._:-]+$/.test(normalizeSerialPortName(value))
}

export function portOptionsWithFallback(items: unknown): string[] {
  const normalized = normalizeSerialPortList(items)
  return normalized.length ? normalized : fallbackPorts
}
