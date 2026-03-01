export const fallbackPorts = Array.from({ length: 32 }, (_, idx) => `COM${idx + 1}`)

export const supportedBaudRates = [9600, 19200, 38400, 57600, 115200]

export const serialDefaults = {
  portPlaceholder: 'COMx',
  baud: 115200,
  dataBits: '8',
  stopBits: '1',
  parity: 'none',
  flowControl: 'none',
  readTimeoutMs: 1000,
  writeTimeoutMs: 1000,
}

export const networkDefaults = {
  host: '127.0.0.1',
  port: 502,
  timeoutMs: 5000,
  heartbeatSec: 60,
  retryCount: 3,
}

export const uiDefaults = {
  language: 'zh-CN',
  theme: 'light',
  autoConnectOnStart: true,
  appVersionFallback: 'v0.0.0',
}
