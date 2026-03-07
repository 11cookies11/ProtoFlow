import { describe, expect, it } from 'vitest'
import { ref } from 'vue'
import { useScriptRunner } from './useScriptRunner'

describe('useScriptRunner', () => {
  it('opens and closes ui yaml modal', async () => {
    const uiRuntime = {
      yamlText: '',
      _parseWithBridge: async () => {},
    }
    const runner = useScriptRunner({
      bridge: ref({ run_script: () => {}, stop_script: () => {} }),
      uiRuntime,
      uiModalOpen: ref(false),
      yamlText: ref('a: 1'),
      scriptRunning: ref(false),
      scriptState: ref('idle'),
      scriptStartMs: ref(0),
      scriptElapsedMs: ref(0),
      scriptProgress: ref(0),
      addScriptLog: () => {},
    })

    await runner.openUiYamlModal()
    runner.closeUiYamlModal()
  })

  it('runs script when yaml is non-empty', () => {
    let called = 0
    const scriptRunning = ref(false)
    const scriptState = ref('idle')
    const scriptProgress = ref(50)
    const runner = useScriptRunner({
      bridge: ref({
        run_script: () => {
          called += 1
        },
        stop_script: () => {},
      }),
      uiRuntime: { yamlText: '', _parseWithBridge: async () => {} },
      uiModalOpen: ref(false),
      yamlText: ref('name: test'),
      scriptRunning,
      scriptState,
      scriptStartMs: ref(0),
      scriptElapsedMs: ref(10),
      scriptProgress,
      addScriptLog: () => {},
    })

    runner.runScript()
    expect(called).toBe(1)
    expect(scriptRunning.value).toBe(true)
    expect(scriptState.value).toBe('starting')
    expect(scriptProgress.value).toBe(0)
  })

  it('stops script and logs', () => {
    let stopped = 0
    const logs: string[] = []
    const scriptState = ref('running')
    const runner = useScriptRunner({
      bridge: ref({
        run_script: () => {},
        stop_script: () => {
          stopped += 1
        },
      }),
      uiRuntime: { yamlText: '', _parseWithBridge: async () => {} },
      uiModalOpen: ref(false),
      yamlText: ref('abc'),
      scriptRunning: ref(true),
      scriptState,
      scriptStartMs: ref(0),
      scriptElapsedMs: ref(0),
      scriptProgress: ref(0),
      addScriptLog: (line) => logs.push(line),
    })

    runner.stopScript()
    expect(stopped).toBe(1)
    expect(scriptState.value).toBe('stopping')
    expect(logs).toContain('[INFO] Stop requested.')
  })
})
