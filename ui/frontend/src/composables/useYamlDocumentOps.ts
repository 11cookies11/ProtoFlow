import type { Ref } from 'vue'

type UseYamlDocumentOpsOptions = {
  bridge: Ref<any>
  withResult: (value: any, handler: (payload: any) => void) => void
  yamlText: Ref<string>
  scriptFileName: Ref<string>
  scriptFilePath: Ref<string>
  yamlFileInputRef: Ref<any>
  refreshScriptVariables: () => void
  addScriptLog: (line: string) => void
}

export function useYamlDocumentOps(options: UseYamlDocumentOpsOptions) {
  function loadYaml() {
    if (options.bridge.value && options.bridge.value.load_yaml) {
      options.withResult(options.bridge.value.load_yaml(), (payload) => {
        if (!payload || !payload.text) return
        options.yamlText.value = payload.text
        options.scriptFileName.value = payload.name || options.scriptFileName.value
        options.scriptFilePath.value = payload.path || options.scriptFilePath.value
        options.refreshScriptVariables()
        options.addScriptLog(`[INFO] Loaded: ${options.scriptFileName.value}`)
      })
      return
    }
    if (!options.yamlFileInputRef.value) return
    options.yamlFileInputRef.value.value = ''
    options.yamlFileInputRef.value.click()
  }

  function saveYaml() {
    const payload = options.yamlText.value.trim()
    if (!payload) {
      options.addScriptLog('[WARN] YAML is empty, not saved.')
      return
    }
    if (options.bridge.value && options.bridge.value.save_yaml) {
      options.withResult(options.bridge.value.save_yaml(payload, options.scriptFileName.value || 'workflow.yaml'), (info) => {
        if (!info) return
        if (info.name) options.scriptFileName.value = info.name
        if (info.path) options.scriptFilePath.value = info.path
        options.addScriptLog(`[INFO] Saved: ${options.scriptFileName.value}`)
      })
      return
    }
    const name = options.scriptFileName.value || 'script.yaml'
    const blob = new Blob([payload], { type: 'text/yaml' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = name
    document.body.appendChild(link)
    link.click()
    link.remove()
    URL.revokeObjectURL(url)
    options.addScriptLog(`[INFO] Saved: ${name}`)
  }

  function handleYamlFile(event: any) {
    const file = event && event.target && event.target.files ? event.target.files[0] : null
    if (!file) return
    const reader = new FileReader()
    reader.onload = () => {
      const text = typeof reader.result === 'string' ? reader.result : ''
      options.yamlText.value = text
      options.scriptFileName.value = file.name
      options.scriptFilePath.value = file.name
      options.refreshScriptVariables()
      options.addScriptLog(`[INFO] Loaded: ${file.name}`)
    }
    reader.readAsText(file)
  }

  async function copyYaml() {
    const payload = options.yamlText.value.trim()
    if (!payload) {
      options.addScriptLog('[WARN] YAML is empty, nothing to copy.')
      return
    }
    if (navigator.clipboard && navigator.clipboard.writeText) {
      try {
        await navigator.clipboard.writeText(payload)
        options.addScriptLog('[INFO] YAML copied to clipboard.')
        return
      } catch {
        options.addScriptLog('[WARN] Clipboard API failed, falling back.')
      }
    }
    const temp = document.createElement('textarea')
    temp.value = payload
    document.body.appendChild(temp)
    temp.select()
    document.execCommand('copy')
    temp.remove()
    options.addScriptLog('[INFO] YAML copied to clipboard.')
  }

  return {
    loadYaml,
    saveYaml,
    handleYamlFile,
    copyYaml,
  }
}
