import type { Ref } from 'vue'

type SettingsDefaults = {
  uiDefaults: { language: string; theme: string; autoConnectOnStart: boolean }
  serialDefaults: { baud: number; parity: string; stopBits: string }
  networkDefaults: { timeoutMs: number; heartbeatSec: number; retryCount: number }
  defaultLanguage: string
  supportedLanguages: Set<string>
  workspaceFallback?: string
}

type SettingsRefs = {
  uiLanguage: Ref<string>
  uiTheme: Ref<string>
  autoConnectOnStart: Ref<boolean>
  dslWorkspacePath: Ref<string>
  quickCommands: Ref<any[]>
  defaultBaud: Ref<number>
  defaultParity: Ref<string>
  defaultStopBits: Ref<string>
  tcpTimeoutMs: Ref<number>
  tcpHeartbeatSec: Ref<number>
  tcpRetryCount: Ref<number>
  baud: Ref<number>
}

type UseSettingsPersistenceOptions = {
  refs: SettingsRefs
  defaults: SettingsDefaults
  normalizeQuickCommands: (value: any) => any[]
}

export function normalizeLanguage(value: any, supportedLanguages: Set<string>, defaultLanguage: string) {
  const raw = String(value || '')
  const lowered = raw.toLowerCase()
  const map: Record<string, string> = {
    'zh-cn': 'zh-CN',
    'zh-tw': 'zh-TW',
    'en-us': 'en-US',
    'ja-jp': 'ja-JP',
    'ko-kr': 'ko-KR',
    'fr-fr': 'fr-FR',
    'de-de': 'de-DE',
    'es-es': 'es-ES',
    'pt-br': 'pt-BR',
    'ru-ru': 'ru-RU',
    ar: 'ar',
    hi: 'hi',
    'it-it': 'it-IT',
    'nl-nl': 'nl-NL',
    'th-th': 'th-TH',
    'vi-vn': 'vi-VN',
    'id-id': 'id-ID',
    'tr-tr': 'tr-TR',
    'pl-pl': 'pl-PL',
    'uk-ua': 'uk-UA',
  }
  let normalized = map[lowered] || ''
  if (!normalized) {
    if (raw === '简体中文') normalized = 'zh-CN'
    else if (raw === '繁體中文' || raw === '繁体中文') normalized = 'zh-TW'
    else if (raw === 'English (US)') normalized = 'en-US'
  }
  if (!normalized) return defaultLanguage
  return supportedLanguages.has(normalized) ? normalized : defaultLanguage
}

export function normalizeTheme(value: any) {
  const raw = String(value || '')
  const lowered = raw.toLowerCase()
  if (raw === 'system' || lowered === 'system' || raw === '系统默认') return 'system'
  if (raw === 'dark' || lowered === 'dark' || raw === '深色 (工程模式)') return 'dark'
  if (raw === 'light' || lowered === 'light' || raw === '浅色') return 'light'
  return 'light'
}

export function useSettingsPersistence(options: UseSettingsPersistenceOptions) {
  const { refs, defaults, normalizeQuickCommands } = options

  function buildSettingsPayload() {
    return {
      uiLanguage: refs.uiLanguage.value,
      uiTheme: refs.uiTheme.value,
      autoConnectOnStart: !!refs.autoConnectOnStart.value,
      dslWorkspacePath: refs.dslWorkspacePath.value,
      quickCommands: refs.quickCommands.value,
      serial: {
        defaultBaud: Number(refs.defaultBaud.value || defaults.serialDefaults.baud),
        defaultParity: refs.defaultParity.value,
        defaultStopBits: refs.defaultStopBits.value,
      },
      network: {
        tcpTimeoutMs: Number(refs.tcpTimeoutMs.value || 0),
        tcpHeartbeatSec: Number(refs.tcpHeartbeatSec.value || 0),
        tcpRetryCount: Number(refs.tcpRetryCount.value || 0),
      },
    }
  }

  function normalizeSettings(payload: any) {
    const fallbackWorkspace = defaults.workspaceFallback || '/usr/local/protoflow/workflows'
    const defaultSettings = {
      uiLanguage: defaults.uiDefaults.language,
      uiTheme: defaults.uiDefaults.theme,
      autoConnectOnStart: defaults.uiDefaults.autoConnectOnStart,
      dslWorkspacePath: fallbackWorkspace,
      quickCommands: refs.quickCommands.value,
      serial: {
        defaultBaud: defaults.serialDefaults.baud,
        defaultParity: defaults.serialDefaults.parity,
        defaultStopBits: defaults.serialDefaults.stopBits,
      },
      network: {
        tcpTimeoutMs: defaults.networkDefaults.timeoutMs,
        tcpHeartbeatSec: defaults.networkDefaults.heartbeatSec,
        tcpRetryCount: defaults.networkDefaults.retryCount,
      },
    }

    if (!payload || typeof payload !== 'object') return defaultSettings

    return {
      ...defaultSettings,
      ...payload,
      uiLanguage: normalizeLanguage(payload.uiLanguage, defaults.supportedLanguages, defaults.defaultLanguage),
      uiTheme: normalizeTheme(payload.uiTheme),
      serial: {
        ...defaultSettings.serial,
        ...(payload.serial || {}),
      },
      network: {
        ...defaultSettings.network,
        ...(payload.network || {}),
      },
    }
  }

  function applySettings(payload: any) {
    const normalized = normalizeSettings(payload)
    refs.uiLanguage.value = normalized.uiLanguage
    refs.uiTheme.value = normalized.uiTheme
    refs.autoConnectOnStart.value = !!normalized.autoConnectOnStart
    refs.dslWorkspacePath.value = normalized.dslWorkspacePath
    refs.quickCommands.value = normalizeQuickCommands(normalized.quickCommands)
    refs.defaultBaud.value = Number(normalized.serial.defaultBaud || defaults.serialDefaults.baud)
    refs.defaultParity.value = normalized.serial.defaultParity || defaults.serialDefaults.parity
    refs.defaultStopBits.value = normalized.serial.defaultStopBits || defaults.serialDefaults.stopBits
    refs.tcpTimeoutMs.value = Number(normalized.network.tcpTimeoutMs || 0)
    refs.tcpHeartbeatSec.value = Number(normalized.network.tcpHeartbeatSec || 0)
    refs.tcpRetryCount.value = Number(normalized.network.tcpRetryCount || 0)
    refs.baud.value = Number(refs.defaultBaud.value || defaults.serialDefaults.baud)
  }

  return {
    buildSettingsPayload,
    normalizeSettings,
    applySettings,
  }
}
