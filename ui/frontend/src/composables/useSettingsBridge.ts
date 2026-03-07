import type { Ref } from 'vue'

type UseSettingsBridgeOptions = {
  bridge: Ref<any>
  settingsSaving: Ref<boolean>
  dslWorkspacePath: Ref<string>
  tr: (text: string) => string
  withResult: (result: any, onSuccess: (payload: any) => void) => void
  normalizeSettings: (payload: any) => any
  applySettings: (payload: any) => void
  setSettingsSnapshot: (payload: any) => void
  buildSettingsPayload: () => any
  commitSettingsSnapshot: () => void
}

export function useSettingsBridge(options: UseSettingsBridgeOptions) {
  function loadSettings() {
    if (options.bridge.value && options.bridge.value.load_settings) {
      options.withResult(options.bridge.value.load_settings(), (payload) => {
        const normalized = options.normalizeSettings(payload)
        options.applySettings(normalized)
        options.setSettingsSnapshot(normalized)
      })
      return
    }
    const normalized = options.normalizeSettings(null)
    options.applySettings(normalized)
    options.setSettingsSnapshot(normalized)
  }

  function saveSettings() {
    const payload = options.buildSettingsPayload()
    options.settingsSaving.value = true
    const finalize = () => {
      options.commitSettingsSnapshot()
      options.settingsSaving.value = false
    }
    if (options.bridge.value && options.bridge.value.save_settings) {
      options.withResult(options.bridge.value.save_settings(payload), () => finalize())
    } else {
      finalize()
    }
  }

  function chooseDslWorkspace() {
    if (!options.bridge.value || !options.bridge.value.select_directory) return
    options.withResult(
      options.bridge.value.select_directory(options.tr('选择工作区'), options.dslWorkspacePath.value || ''),
      (value) => {
        if (value) {
          options.dslWorkspacePath.value = value
        }
      }
    )
  }

  return {
    loadSettings,
    saveSettings,
    chooseDslWorkspace,
  }
}
