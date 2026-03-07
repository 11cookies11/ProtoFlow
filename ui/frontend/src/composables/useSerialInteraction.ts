import { normalizeSerialPortName } from '@/utils/serialPort'

export function useSerialInteraction() {
  function resolveSerialPort(candidate: unknown): string {
    return normalizeSerialPortName(candidate)
  }

  return {
    resolveSerialPort,
  }
}
