import type { Ref } from 'vue'

type UseCommLogExportOptions = {
  displayMode: Ref<string>
  commLogs: Ref<any[]>
  formatTime: (ts: number) => string
  createObjectUrl?: (blob: Blob) => string
  revokeObjectUrl?: (url: string) => void
  createAnchor?: () => HTMLAnchorElement
}

export function useCommLogExport(options: UseCommLogExportOptions) {
  const createObjectUrl = options.createObjectUrl || ((blob: Blob) => URL.createObjectURL(blob))
  const revokeObjectUrl = options.revokeObjectUrl || ((url: string) => URL.revokeObjectURL(url))
  const createAnchor = options.createAnchor || (() => document.createElement('a'))

  function formatPayload(item: any) {
    if (!item) return ''
    if (options.displayMode.value === 'hex' && item.hex) return item.hex
    return item.text || item.hex || ''
  }

  function formatCommLine(item: any) {
    if (!item) return ''
    const ts = item.ts ? options.formatTime(item.ts) : ''
    const kind = item.kind || ''
    const payload = formatPayload(item).replace(/\r?\n/g, '\\n')
    return `${ts}\t${kind}\t${payload}`
  }

  function exportCommLogs() {
    const lines = options.commLogs.value.map((item) => formatCommLine(item)).filter(Boolean)
    const payload = lines.join('\n')
    const name = `io_logs_${new Date().toISOString().replace(/[:.]/g, '-')}.log`
    const blob = new Blob([payload], { type: 'text/plain' })
    const url = createObjectUrl(blob)
    const link = createAnchor()
    link.href = url
    link.download = name
    document.body.appendChild(link)
    link.click()
    link.remove()
    revokeObjectUrl(url)
  }

  return {
    formatPayload,
    formatCommLine,
    exportCommLogs,
  }
}
