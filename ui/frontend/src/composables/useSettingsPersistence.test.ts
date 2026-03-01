import { describe, expect, it } from 'vitest'
import { ref } from 'vue'
import { normalizeLanguage, normalizeTheme, useSettingsPersistence } from './useSettingsPersistence'

describe('useSettingsPersistence', () => {
  it('normalizes language aliases and falls back to default', () => {
    const supported = new Set(['zh-CN', 'en-US'])
    expect(normalizeLanguage('zh-cn', supported, 'en-US')).toBe('zh-CN')
    expect(normalizeLanguage('English (US)', supported, 'zh-CN')).toBe('en-US')
    expect(normalizeLanguage('fr-FR', supported, 'zh-CN')).toBe('zh-CN')
  })

  it('normalizes theme aliases', () => {
    expect(normalizeTheme('系统默认')).toBe('system')
    expect(normalizeTheme('深色 (工程模式)')).toBe('dark')
    expect(normalizeTheme('unknown')).toBe('light')
  })

  it('builds and applies normalized settings payload', () => {
    const refs = {
      uiLanguage: ref('zh-CN'),
      uiTheme: ref('light'),
      autoConnectOnStart: ref(false),
      dslWorkspacePath: ref('/tmp/workspace'),
      quickCommands: ref([{ id: 'a' }]),
      defaultBaud: ref(115200),
      defaultParity: ref('none'),
      defaultStopBits: ref('1'),
      tcpTimeoutMs: ref(1000),
      tcpHeartbeatSec: ref(5),
      tcpRetryCount: ref(3),
      baud: ref(115200),
    }
    const { buildSettingsPayload, normalizeSettings, applySettings } = useSettingsPersistence({
      refs,
      defaults: {
        uiDefaults: { language: 'zh-CN', theme: 'light', autoConnectOnStart: true },
        serialDefaults: { baud: 9600, parity: 'even', stopBits: '2' },
        networkDefaults: { timeoutMs: 1500, heartbeatSec: 10, retryCount: 2 },
        defaultLanguage: 'zh-CN',
        supportedLanguages: new Set(['zh-CN', 'en-US']),
        workspaceFallback: '/workspace/default',
      },
      normalizeQuickCommands: (value) => (Array.isArray(value) ? value : []),
    })

    const built = buildSettingsPayload()
    expect(built.serial.defaultBaud).toBe(115200)

    const normalized = normalizeSettings({
      uiLanguage: 'en-us',
      uiTheme: '系统默认',
      serial: { defaultBaud: 4800 },
    })
    expect(normalized.uiLanguage).toBe('en-US')
    expect(normalized.uiTheme).toBe('system')
    expect(normalized.serial.defaultBaud).toBe(4800)
    expect(normalized.network.tcpTimeoutMs).toBe(1500)

    applySettings({
      uiLanguage: 'fr-FR',
      uiTheme: 'dark',
      serial: { defaultBaud: 19200 },
      network: { tcpRetryCount: 9 },
    })
    expect(refs.uiLanguage.value).toBe('zh-CN')
    expect(refs.uiTheme.value).toBe('dark')
    expect(refs.defaultBaud.value).toBe(19200)
    expect(refs.tcpRetryCount.value).toBe(9)
    expect(refs.baud.value).toBe(19200)
  })
})
