type UseCommBridgeSignalsOptions = {
  parseBridgePayload: (payload: any) => any
  addCommLog: (kind: string, payload: any) => void
  addCommBatch: (batch: any) => void
  ingestCaptureFrame: (payload: any) => void
  emitStatus: (text: string, ts: number) => void
  scheduleChannelRefresh: () => void
  setConnectingFalse: () => void
  onConnectionInfo: (nextInfo: { state: string; detail: string }) => void
  shouldEmitDisconnected: (reason: string) => boolean
}

export function useCommBridgeSignals(options: UseCommBridgeSignalsOptions) {
  function bindCommBridgeSignals(obj: any) {
    if (!obj) return
    if (obj.comm_rx && obj.comm_tx && typeof obj.comm_rx.connect === 'function' && typeof obj.comm_tx.connect === 'function') {
      obj.comm_rx.connect((payload: any) => {
        const parsed = options.parseBridgePayload(payload)
        options.addCommLog('RX', parsed)
      })
      obj.comm_tx.connect((payload: any) => {
        const parsed = options.parseBridgePayload(payload)
        options.addCommLog('TX', parsed)
      })
    } else if (obj.comm_batch && typeof obj.comm_batch.connect === 'function') {
      obj.comm_batch.connect((batch: any) => options.addCommBatch(batch))
    }

    if (obj.protocol_frame && typeof obj.protocol_frame.connect === 'function') {
      obj.protocol_frame.connect((payload: any) => {
        const ts = payload && payload.ts ? payload.ts : Date.now() / 1000
        options.addCommLog('FRAME', { text: JSON.stringify(payload), ts })
      })
    }

    if (obj.capture_frame && typeof obj.capture_frame.connect === 'function') {
      obj.capture_frame.connect((payload: any) => {
        const ts = payload && payload.ts ? payload.ts : Date.now() / 1000
        options.addCommLog('CAPTURE', { text: JSON.stringify(payload), ts })
        options.ingestCaptureFrame(payload)
      })
    }

    if (obj.comm_status && typeof obj.comm_status.connect === 'function') {
      obj.comm_status.connect((payload: any) => {
        const detail = payload && payload.payload !== undefined ? payload.payload : payload
        const ts = payload && payload.ts ? payload.ts : Date.now() / 1000
        options.setConnectingFalse()
        if (!detail) {
          const reason = payload && payload.reason ? String(payload.reason) : ''
          const message = reason ? `Disconnected: ${reason}` : 'Disconnected'
          if (options.shouldEmitDisconnected(reason)) {
            options.emitStatus(message, ts)
          }
          options.onConnectionInfo({ state: 'disconnected', detail: '' })
          options.scheduleChannelRefresh()
          return
        }
        if (typeof detail === 'string') {
          options.emitStatus(`Error: ${detail}`, ts)
          options.onConnectionInfo({ state: 'error', detail })
          options.scheduleChannelRefresh()
          return
        }
        if (detail && typeof detail === 'object') {
          const target = detail.address || detail.port || detail.type || ''
          options.emitStatus(`Connected: ${target}`, ts)
        }
        options.onConnectionInfo({
          state: 'connected',
          detail: detail.address || detail.port || detail.type || '',
        })
        options.scheduleChannelRefresh()
      })
    }
  }

  return {
    bindCommBridgeSignals,
  }
}
