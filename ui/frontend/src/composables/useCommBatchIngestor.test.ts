import { describe, expect, it } from 'vitest'
import { ref } from 'vue'
import { useCommBatchIngestor } from './useCommBatchIngestor'

describe('useCommBatchIngestor', () => {
  it('parses bridge payload json and fallback text', () => {
    const calls: Array<{ kind: string; payload: any }> = []
    const mgr = useCommBatchIngestor({
      commPaused: ref(false),
      addCommLog: (kind, payload) => calls.push({ kind, payload }),
    })

    expect(mgr.parseBridgePayload('[{\"kind\":\"RX\"}]')).toEqual([{ kind: 'RX' }])
    expect(mgr.parseBridgePayload('not-json')).toEqual({ text: 'not-json' })
  })

  it('ingests batch and normalizes payloads', () => {
    const calls: Array<{ kind: string; payload: any }> = []
    const mgr = useCommBatchIngestor({
      commPaused: ref(false),
      addCommLog: (kind, payload) => calls.push({ kind, payload }),
    })

    mgr.addCommBatch([
      { kind: 'RX', text: 'A', ts: 1 },
      { kind: 'FRAME', payload: { p: 1 }, ts: 2 },
      { kind: 'TX', payload: { foo: 1 }, ts: 3 },
    ])

    expect(calls).toHaveLength(3)
    expect(calls[0]).toEqual({ kind: 'RX', payload: { text: 'A', hex: '', ts: 1 } })
    expect(calls[1].kind).toBe('FRAME')
    expect(calls[1].payload.text).toBe(JSON.stringify({ p: 1 }))
    expect(calls[2].payload.text).toBe(JSON.stringify({ kind: 'TX', payload: { foo: 1 }, ts: 3 }))
  })

  it('ignores batches when paused', () => {
    let count = 0
    const mgr = useCommBatchIngestor({
      commPaused: ref(true),
      addCommLog: () => {
        count += 1
      },
    })
    mgr.addCommBatch([{ kind: 'RX', text: 'A' }])
    expect(count).toBe(0)
  })
})
