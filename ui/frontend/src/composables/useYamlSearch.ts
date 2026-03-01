type UseYamlSearchOptions = {
  tr: (text: string) => string
  addScriptLog: (line: string) => void
  getEditor: () => any
}

export function useYamlSearch(options: UseYamlSearchOptions) {
  function searchYaml() {
    const keyword = window.prompt(options.tr('搜索关键词'))
    if (!keyword) return
    const yamlEditor = options.getEditor()
    if (yamlEditor) {
      const doc = yamlEditor.state.doc.toString()
      const lower = doc.toLowerCase()
      const idx = lower.indexOf(keyword.toLowerCase())
      if (idx === -1) {
        options.addScriptLog(`[INFO] Not found: ${keyword}`)
        return
      }
      yamlEditor.dispatch({
        selection: { anchor: idx, head: idx + keyword.length },
        scrollIntoView: true,
      })
      return
    }
    const found = window.find(keyword)
    if (!found) {
      options.addScriptLog(`[INFO] Not found: ${keyword}`)
    }
  }

  return {
    searchYaml,
  }
}
