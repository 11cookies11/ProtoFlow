import type { Ref } from 'vue'

type UseCommBatchIngestorOptions = {
  commPaused: Ref<boolean>
  addCommLog: (kind: string, payload: any) => void
}

export function useCommBatchIngestor(options: UseCommBatchIngestorOptions) {
  function parseBridgePayload(payload: any) {
    if (typeof payload !== 'string') return payload
    try {
      return JSON.parse(payload)
    } catch (err) {
      return { text: String(payload) }
    }
  }

  function addCommBatch(batch: any) {
    if (options.commPaused.value) return
    batch = parseBridgePayload(batch)
    if (!Array.isArray(batch)) return
    for (const item of batch) {
      if (!item) continue
      const kind = item.kind || 'RX'
      if (kind === 'FRAME') {
        options.addCommLog('FRAME', { text: JSON.stringify(item.payload), ts: item.ts })
        continue
      }
      let payload = item.payload || {}
      if (
        payload &&
        typeof payload === 'object' &&
        !payload.text &&
        !payload.hex &&
        (item.text || item.hex)
      ) {
        payload = { text: item.text || '', hex: item.hex || '', ts: item.ts || payload.ts }
      }
      if (payload && typeof payload === 'object' && !payload.text && !payload.hex) {
        payload = { text: JSON.stringify(item), ts: item.ts || payload.ts }
      }
      options.addCommLog(kind, payload)
    }
  }

  return {
    parseBridgePayload,
    addCommBatch,
  }
}
