import { describe, expect, it, vi } from 'vitest'
import { ref } from 'vue'
import { useSettingsBridge } from './useSettingsBridge'

function withResult(result: any, onSuccess: (payload: any) => void) {
  onSuccess(result)
}

describe('useSettingsBridge', () => {
  it('loads settings from bridge when available', () => {
    const applySettings = vi.fn()
    const setSettingsSnapshot = vi.fn()
    const normalizeSettings = vi.fn((payload) => ({ normalized: payload }))

    const bridge = ref({
      load_settings: () => ({ lang: 'en-US' }),
    })

    const { loadSettings } = useSettingsBridge({
      bridge,
      settingsSaving: ref(false),
      dslWorkspacePath: ref('/tmp'),
      tr: (text) => text,
      withResult,
      normalizeSettings,
      applySettings,
      setSettingsSnapshot,
      buildSettingsPayload: () => ({}),
      commitSettingsSnapshot: () => {},
    })

    loadSettings()
    expect(normalizeSettings).toHaveBeenCalledWith({ lang: 'en-US' })
    expect(applySettings).toHaveBeenCalledWith({ normalized: { lang: 'en-US' } })
    expect(setSettingsSnapshot).toHaveBeenCalledWith({ normalized: { lang: 'en-US' } })
  })

  it('falls back to defaults when bridge loader missing', () => {
    const applySettings = vi.fn()
    const setSettingsSnapshot = vi.fn()
    const normalizeSettings = vi.fn((payload) => ({ normalized: payload }))

    const { loadSettings } = useSettingsBridge({
      bridge: ref({}),
      settingsSaving: ref(false),
      dslWorkspacePath: ref('/tmp'),
      tr: (text) => text,
      withResult,
      normalizeSettings,
      applySettings,
      setSettingsSnapshot,
      buildSettingsPayload: () => ({}),
      commitSettingsSnapshot: () => {},
    })

    loadSettings()
    expect(normalizeSettings).toHaveBeenCalledWith(null)
    expect(applySettings).toHaveBeenCalledWith({ normalized: null })
    expect(setSettingsSnapshot).toHaveBeenCalledWith({ normalized: null })
  })

  it('saves settings and clears saving flag', () => {
    const settingsSaving = ref(false)
    const commitSettingsSnapshot = vi.fn()
    const bridge = ref({
      save_settings: (payload: any) => payload,
    })

    const { saveSettings } = useSettingsBridge({
      bridge,
      settingsSaving,
      dslWorkspacePath: ref('/tmp'),
      tr: (text) => text,
      withResult,
      normalizeSettings: (payload) => payload,
      applySettings: () => {},
      setSettingsSnapshot: () => {},
      buildSettingsPayload: () => ({ key: 1 }),
      commitSettingsSnapshot,
    })

    saveSettings()
    expect(commitSettingsSnapshot).toHaveBeenCalled()
    expect(settingsSaving.value).toBe(false)
  })

  it('chooses workspace via bridge and updates path', () => {
    const dslWorkspacePath = ref('/old')
    const bridge = ref({
      select_directory: () => '/new',
    })

    const { chooseDslWorkspace } = useSettingsBridge({
      bridge,
      settingsSaving: ref(false),
      dslWorkspacePath,
      tr: (text) => text,
      withResult,
      normalizeSettings: (payload) => payload,
      applySettings: () => {},
      setSettingsSnapshot: () => {},
      buildSettingsPayload: () => ({}),
      commitSettingsSnapshot: () => {},
    })

    chooseDslWorkspace()
    expect(dslWorkspacePath.value).toBe('/new')
  })
})
