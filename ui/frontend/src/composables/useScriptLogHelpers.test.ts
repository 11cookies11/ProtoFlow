import { describe, expect, it } from 'vitest'
import { ref } from 'vue'
import { useScriptLogHelpers } from './useScriptLogHelpers'

describe('useScriptLogHelpers', () => {
  it('clears logs and buffer', () => {
    const scriptLogs = ref([{ text: 'a' }])
    const scriptLogBuffer = [{ text: 'b' }]
    const helpers = useScriptLogHelpers({
      scriptLogs,
      scriptLogBuffer,
      scriptLogRef: ref(null),
      scriptVariablesList: ref([]),
      yamlText: ref(''),
      parseScriptVariables: () => [],
      clearScriptVarTimer: () => {},
    })

    helpers.clearScriptLogs()
    expect(scriptLogs.value).toEqual([])
    expect(scriptLogBuffer.length).toBe(0)
  })

  it('scrolls to bottom when log element exists', () => {
    const el = { scrollTop: 0, scrollHeight: 200 }
    const helpers = useScriptLogHelpers({
      scriptLogs: ref([]),
      scriptLogBuffer: [],
      scriptLogRef: ref({ rootEl: el }),
      scriptVariablesList: ref([]),
      yamlText: ref(''),
      parseScriptVariables: () => [],
      clearScriptVarTimer: () => {},
    })

    helpers.scrollScriptLogsToBottom()
    expect(el.scrollTop).toBe(200)
  })

  it('refreshes script variables with parser output', () => {
    let cleared = 0
    const scriptVariablesList = ref<any[]>([])
    const helpers = useScriptLogHelpers({
      scriptLogs: ref([]),
      scriptLogBuffer: [],
      scriptLogRef: ref(null),
      scriptVariablesList,
      yamlText: ref('a: 1\nb: 2'),
      parseScriptVariables: () => [{ name: 'a' }],
      clearScriptVarTimer: () => {
        cleared += 1
      },
    })

    helpers.refreshScriptVariables()
    expect(cleared).toBe(1)
    expect(scriptVariablesList.value).toEqual([{ name: 'a' }])
  })
})
