import type { Ref } from 'vue'

type UseScriptRunnerOptions = {
  bridge: Ref<any>
  uiRuntime: any
  uiModalOpen: Ref<boolean>
  yamlText: Ref<string>
  scriptRunning: Ref<boolean>
  scriptState: Ref<string>
  scriptStartMs: Ref<number>
  scriptElapsedMs: Ref<number>
  scriptProgress: Ref<number>
  addScriptLog: (line: string) => void
}

export function useScriptRunner(options: UseScriptRunnerOptions) {
  async function openUiYamlModal() {
    if (!options.uiModalOpen.value) {
      options.uiModalOpen.value = true
    }
    options.uiRuntime.yamlText = options.yamlText.value
    await options.uiRuntime._parseWithBridge()
  }

  function closeUiYamlModal() {
    options.uiModalOpen.value = false
  }

  function runScript() {
    if (!options.bridge.value) return
    const payload = options.yamlText.value.trim()
    if (!payload) {
      options.addScriptLog('[WARN] YAML is empty, abort run.')
      return
    }
    options.scriptRunning.value = true
    options.scriptState.value = 'starting'
    options.scriptStartMs.value = Date.now()
    options.scriptElapsedMs.value = 0
    options.scriptProgress.value = 0
    openUiYamlModal()
    options.bridge.value.run_script(payload)
  }

  function stopScript() {
    if (!options.bridge.value) return
    options.scriptState.value = 'stopping'
    options.bridge.value.stop_script()
    options.addScriptLog('[INFO] Stop requested.')
  }

  return {
    openUiYamlModal,
    closeUiYamlModal,
    runScript,
    stopScript,
  }
}
