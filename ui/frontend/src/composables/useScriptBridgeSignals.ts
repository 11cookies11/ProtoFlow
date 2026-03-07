import type { Ref } from 'vue'

type UseScriptBridgeSignalsOptions = {
  scriptRunning: Ref<boolean>
  scriptState: Ref<string>
  scriptProgress: Ref<number>
  addScriptLog: (line: any) => void
  scheduleSetChannels: (items: any) => void
}

export function useScriptBridgeSignals(options: UseScriptBridgeSignalsOptions) {
  function bindScriptBridgeSignals(obj: any) {
    if (!obj) return
    if (obj.script_log && typeof obj.script_log.connect === 'function') {
      obj.script_log.connect((line: any) => options.addScriptLog(line))
    }
    if (obj.script_state && typeof obj.script_state.connect === 'function') {
      obj.script_state.connect((state: string) => {
        if (state === '__running__') {
          options.scriptRunning.value = true
          options.scriptState.value = 'running'
          return
        }
        if (state === '__finished__') {
          options.scriptRunning.value = false
          options.scriptState.value = 'idle'
          options.scriptProgress.value = 100
          return
        }
        if (state === '__stopped__') {
          options.scriptRunning.value = false
          options.scriptState.value = 'idle'
          return
        }
        if (state === '__error__') {
          options.scriptRunning.value = false
          options.scriptState.value = 'error'
          return
        }
        options.scriptState.value = state
        if (state) {
          options.scriptRunning.value = true
        }
      })
    }
    if (obj.script_progress && typeof obj.script_progress.connect === 'function') {
      obj.script_progress.connect((value: number) => {
        options.scriptProgress.value = value
      })
    }
    if (obj.channel_update && typeof obj.channel_update.connect === 'function') {
      obj.channel_update.connect((items: any) => {
        options.scheduleSetChannels(items)
      })
    }
  }

  return {
    bindScriptBridgeSignals,
  }
}
