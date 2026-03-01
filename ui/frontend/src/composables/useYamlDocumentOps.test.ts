import { describe, expect, it, vi } from 'vitest'
import { ref } from 'vue'
import { useYamlDocumentOps } from './useYamlDocumentOps'

function withResult(value: any, handler: (payload: any) => void) {
  handler(value)
}

describe('useYamlDocumentOps', () => {
  it('loads yaml from bridge payload', () => {
    const logs: string[] = []
    const yamlText = ref('')
    const scriptFileName = ref('old.yaml')
    const scriptFilePath = ref('')
    const refreshScriptVariables = vi.fn()

    const ops = useYamlDocumentOps({
      bridge: ref({
        load_yaml: () => ({ text: 'a: 1', name: 'new.yaml', path: '/tmp/new.yaml' }),
      }),
      withResult,
      yamlText,
      scriptFileName,
      scriptFilePath,
      yamlFileInputRef: ref(null),
      refreshScriptVariables,
      addScriptLog: (line) => logs.push(line),
    })

    ops.loadYaml()
    expect(yamlText.value).toBe('a: 1')
    expect(scriptFileName.value).toBe('new.yaml')
    expect(refreshScriptVariables).toHaveBeenCalled()
    expect(logs.some((line) => line.includes('Loaded: new.yaml'))).toBe(true)
  })

  it('saves yaml through bridge and updates file info', () => {
    const logs: string[] = []
    const yamlText = ref('a: 2')
    const scriptFileName = ref('current.yaml')
    const scriptFilePath = ref('')

    const ops = useYamlDocumentOps({
      bridge: ref({
        save_yaml: () => ({ name: 'saved.yaml', path: '/tmp/saved.yaml' }),
      }),
      withResult,
      yamlText,
      scriptFileName,
      scriptFilePath,
      yamlFileInputRef: ref(null),
      refreshScriptVariables: () => {},
      addScriptLog: (line) => logs.push(line),
    })

    ops.saveYaml()
    expect(scriptFileName.value).toBe('saved.yaml')
    expect(logs.some((line) => line.includes('Saved: saved.yaml'))).toBe(true)
  })

  it('warns when copying empty yaml', async () => {
    const logs: string[] = []
    const ops = useYamlDocumentOps({
      bridge: ref(null),
      withResult,
      yamlText: ref(''),
      scriptFileName: ref('x.yaml'),
      scriptFilePath: ref(''),
      yamlFileInputRef: ref(null),
      refreshScriptVariables: () => {},
      addScriptLog: (line) => logs.push(line),
    })

    await ops.copyYaml()
    expect(logs).toContain('[WARN] YAML is empty, nothing to copy.')
  })
})
