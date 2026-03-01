import { describe, expect, it } from 'vitest'
import { ref } from 'vue'
import { formatCaptureTime, mapCaptureFrame, useCaptureFrames } from './useCaptureFrames'

describe('useCaptureFrames', () => {
  it('formats capture time and maps frame payload', () => {
    const time = formatCaptureTime(1)
    expect(time).toMatch(/^\d{2}:\d{2}:\d{2}\.\d{3}$/)

    const mapped = mapCaptureFrame({
      id: 'f1',
      direction: 'TX',
      timestamp: 1,
      length: 4,
      raw_hex: 'AA BB',
      summary: 'sum',
      channel: 'COM3',
      protocol: { name: 'modbus', version: '1.0' },
      tree: [{ k: 1 }],
    })
    expect(mapped?.id).toBe('f1')
    expect(mapped?.tone).toBe('blue')
    expect(mapped?.protocolType).toBe('modbus')
  })

  it('ingests frame list and caps by max size', () => {
    const captureFrames = ref<any[]>([])
    const captureMeta = ref({
      channel: '',
      engine: 'x',
      bufferUsed: 0,
      rangeStart: 0,
      rangeEnd: 0,
      totalFrames: 0,
      page: 1,
      pageCount: 1,
    })
    const mgr = useCaptureFrames({ captureFrames, captureMeta, maxCaptureFrames: 2 })

    mgr.ingestCaptureFrame({ id: 'a', timestamp: 1, summary: 'A', channel: 'COM1' })
    mgr.ingestCaptureFrame({ id: 'b', timestamp: 2, summary: 'B', channel: 'COM1' })
    mgr.ingestCaptureFrame({ id: 'c', timestamp: 3, summary: 'C', channel: 'COM2' })

    expect(captureFrames.value).toHaveLength(2)
    expect(captureFrames.value[0].id).toBe('b')
    expect(captureMeta.value.totalFrames).toBe(3)
    expect(captureMeta.value.rangeStart).toBe(2)
    expect(captureMeta.value.rangeEnd).toBe(3)
    expect(captureMeta.value.channel).toBe('COM2')
  })
})
