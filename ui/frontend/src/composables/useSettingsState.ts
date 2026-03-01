import { computed, type Ref } from 'vue'

export function useSettingsState(settingsSnapshot: Ref<any>, current: Ref<any>) {
  const settingsDirty = computed(() => {
    if (!settingsSnapshot.value || !current.value) return false
    return JSON.stringify(settingsSnapshot.value) !== JSON.stringify(current.value)
  })

  return {
    settingsDirty,
  }
}
