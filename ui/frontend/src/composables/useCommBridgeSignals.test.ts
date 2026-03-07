import { describe, expect, it } from 'vitest'
import { useCommBridgeSignals } from './useCommBridgeSignals'

function createSignal() {
  const listeners: Array<(payload: any) => void> = []
  return {
    connect(fn: (payload: any) => void) {
      listeners.push(fn)
    },
    emit(payload: any) {
      listeners.forEach((fn) => fn(payload))
    },
  }
}

describe('useCommBridgeSignals', () => {
  it('binds rx/tx and frame/capture logs', () => {
    const logs: Array<{ kind: string; payload: any }> = []
    const captures: any[] = []

    const mgr = useCommBridgeSignals({
      parseBridgePayload: (payload) => ({ text: String(payload) }),
      addCommLog: (kind, payload) => logs.push({ kind, payload }),
      addCommBatch: () => {},
      ingestCaptureFrame: (payload) => captures.push(payload),
      emitStatus: () => {},
      scheduleChannelRefresh: () => {},
      setConnectingFalse: () => {},
      onConnectionInfo: () => {},
      shouldEmitDisconnected: () => true,
    })

    const rx = createSignal()
    const tx = createSignal()
    const frame = createSignal()
    const capture = createSignal()

    mgr.bindCommBridgeSignals({
      comm_rx: rx,
      comm_tx: tx,
      protocol_frame: frame,
      capture_frame: capture,
    })

    rx.emit('r1')
    tx.emit('t1')
    frame.emit({ k: 1, ts: 1 })
    capture.emit({ c: 1, ts: 2 })

    expect(logs.map((item) => item.kind)).toEqual(['RX', 'TX', 'FRAME', 'CAPTURE'])
    expect(captures.length).toBe(1)
  })

  it('handles comm status branches', () => {
    const infos: Array<{ state: string; detail: string }> = []
    const statuses: string[] = []
    let refreshCount = 0
    let connectingFalse = 0

    const mgr = useCommBridgeSignals({
      parseBridgePayload: (payload) => payload,
      addCommLog: () => {},
      addCommBatch: () => {},
      ingestCaptureFrame: () => {},
      emitStatus: (text) => statuses.push(text),
      scheduleChannelRefresh: () => {
        refreshCount += 1
      },
      setConnectingFalse: () => {
        connectingFalse += 1
      },
      onConnectionInfo: (next) => infos.push(next),
      shouldEmitDisconnected: () => true,
    })

    const commStatus = createSignal()
    mgr.bindCommBridgeSignals({ comm_status: commStatus })

    commStatus.emit({ payload: null, reason: 'timeout', ts: 1 })
    commStatus.emit({ payload: 'boom', ts: 2 })
    commStatus.emit({ payload: { address: '127.0.0.1:1' }, ts: 3 })

    expect(connectingFalse).toBe(3)
    expect(refreshCount).toBe(3)
    expect(infos[0].state).toBe('disconnected')
    expect(infos[1]).toEqual({ state: 'error', detail: 'boom' })
    expect(infos[2].state).toBe('connected')
    expect(statuses.some((item) => item.includes('Disconnected'))).toBe(true)
    expect(statuses).toContain('Error: boom')
  })
})
