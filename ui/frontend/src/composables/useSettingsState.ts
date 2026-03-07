import { computed, type Ref } from 'vue'

type UseSettingsStateOptions = {
  settingsSnapshot: Ref<any>
  buildPayload: () => any
  normalize: (payload: any) => any
  apply: (payload: any) => void
}

export function useSettingsState(options: UseSettingsStateOptions) {
  const settingsDirty = computed(() => {
    if (!options.settingsSnapshot.value) return false
    const current = options.normalize(options.buildPayload())
    return JSON.stringify(current) !== JSON.stringify(options.settingsSnapshot.value)
  })

  function setSnapshot(payload: any) {
    options.settingsSnapshot.value = options.normalize(payload)
  }

  function commitCurrent() {
    setSnapshot(options.buildPayload())
  }

  function discard() {
    if (!options.settingsSnapshot.value) return
    options.apply(options.settingsSnapshot.value)
  }

  return {
    settingsDirty,
    setSnapshot,
    commitCurrent,
    discard,
  }
}
