import type { Ref } from 'vue'

type UseScriptLogHelpersOptions = {
  scriptLogs: Ref<any[]>
  scriptLogBuffer: any[]
  scriptLogRef: Ref<any>
  scriptVariablesList: Ref<any[]>
  yamlText: Ref<string>
  parseScriptVariables: (text: string) => any[]
  clearScriptVarTimer: () => void
}

export function useScriptLogHelpers(options: UseScriptLogHelpersOptions) {
  function clearScriptLogs() {
    options.scriptLogs.value = []
    options.scriptLogBuffer.length = 0
  }

  function scrollScriptLogsToBottom() {
    if (!options.scriptLogRef.value) return
    const root = options.scriptLogRef.value.rootEl
    const el = root && root.value ? root.value : root
    if (!el) return
    el.scrollTop = el.scrollHeight
  }

  function refreshScriptVariables() {
    options.clearScriptVarTimer()
    options.scriptVariablesList.value = options.parseScriptVariables(options.yamlText.value)
  }

  return {
    clearScriptLogs,
    scrollScriptLogsToBottom,
    refreshScriptVariables,
  }
}
