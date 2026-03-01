import type { Ref } from 'vue'
import { ref } from 'vue'

type UseLogBuffersOptions = {
  commLogs: Ref<any[]>
  scriptLogs: Ref<any[]>
  commPaused: Ref<boolean>
  scriptRunning: Ref<boolean>
  scriptState: Ref<string>
  maxCommLogs: number
  maxScriptLogs: number
}

export function useLogBuffers(options: UseLogBuffersOptions) {
  const commLogBuffer: any[] = []
  const scriptLogBuffer: any[] = []
  const hasStatusActivity = ref(false)
  let logFlushHandle = 0
  let commLogSeq = 0
  let scriptLogSeq = 0
  let lastStatusText = ''

  function flushLogs() {
    if (commLogBuffer.length) {
      const batch = commLogBuffer.splice(0, commLogBuffer.length)
      options.commLogs.value.push(...batch)
      if (options.commLogs.value.length > options.maxCommLogs) {
        options.commLogs.value.splice(0, options.commLogs.value.length - options.maxCommLogs)
      }
    }
    if (scriptLogBuffer.length) {
      options.scriptLogs.value.push(...scriptLogBuffer.splice(0, scriptLogBuffer.length))
      if (options.scriptLogs.value.length > options.maxScriptLogs) {
        options.scriptLogs.value.splice(0, options.scriptLogs.value.length - options.maxScriptLogs)
      }
    }
  }

  function scheduleLogFlush() {
    if (logFlushHandle) return
    logFlushHandle = window.requestAnimationFrame(() => {
      logFlushHandle = 0
      flushLogs()
    })
  }

  function addCommLog(kind: string, payload: any) {
    if (options.commPaused.value) return
    if (!payload || typeof payload !== 'object') {
      payload = { text: String(payload || ''), hex: '', ts: Date.now() / 1000 }
    } else if (!payload.text && !payload.hex) {
      payload = { text: JSON.stringify(payload), hex: '', ts: payload.ts || Date.now() / 1000 }
    }
    commLogBuffer.push({
      id: `c${commLogSeq++}`,
      kind,
      text: payload.text || '',
      hex: payload.hex || '',
      ts: payload.ts || Date.now() / 1000,
    })
    scheduleLogFlush()
  }

  function emitStatus(text: string, ts: number) {
    const message = String(text || '')
    if (!message || message === lastStatusText) return
    lastStatusText = message
    hasStatusActivity.value = true
    addCommLog('STATUS', { text: message, ts })
  }

  function addScriptLog(line: any) {
    const text = String(line || '')
    scriptLogBuffer.push({ id: `s${scriptLogSeq++}`, text })
    scheduleLogFlush()
    if (
      text.includes('Script finished') ||
      text.includes('Script stopped') ||
      text.toLowerCase().includes('[error]')
    ) {
      options.scriptRunning.value = false
      options.scriptState.value = 'idle'
    }
  }

  function clearCommLogs() {
    options.commLogs.value = []
    commLogBuffer.length = 0
  }

  function toggleCommPaused() {
    options.commPaused.value = !options.commPaused.value
  }

  function disposeLogBuffers() {
    if (!logFlushHandle) return
    window.cancelAnimationFrame(logFlushHandle)
    logFlushHandle = 0
  }

  return {
    scriptLogBuffer,
    hasStatusActivity,
    addCommLog,
    emitStatus,
    addScriptLog,
    clearCommLogs,
    toggleCommPaused,
    disposeLogBuffers,
  }
}
