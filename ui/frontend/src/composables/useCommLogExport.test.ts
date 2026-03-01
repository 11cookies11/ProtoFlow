import { describe, expect, it, vi } from 'vitest'
import { ref } from 'vue'
import { useCommLogExport } from './useCommLogExport'

describe('useCommLogExport', () => {
  it('formats payload by display mode', () => {
    const mgr = useCommLogExport({
      displayMode: ref('ascii'),
      commLogs: ref([]),
      formatTime: () => '00:00:00.000',
    })

    expect(mgr.formatPayload({ text: 'ABC', hex: '41 42 43' })).toBe('ABC')

    const mgrHex = useCommLogExport({
      displayMode: ref('hex'),
      commLogs: ref([]),
      formatTime: () => '00:00:00.000',
    })
    expect(mgrHex.formatPayload({ text: 'ABC', hex: '41 42 43' })).toBe('41 42 43')
  })

  it('exports logs through object url and anchor click', async () => {
    let capturedBlob: Blob | null = null
    let revokedUrl = ''
    const clickSpy = vi.fn()
    const anchor = document.createElement('a')
    anchor.click = clickSpy

    const mgr = useCommLogExport({
      displayMode: ref('ascii'),
      commLogs: ref([{ ts: 1, kind: 'RX', text: 'A\nB' }]),
      formatTime: () => '10:00:00.000',
      createObjectUrl: (blob) => {
        capturedBlob = blob
        return 'blob:test'
      },
      revokeObjectUrl: (url) => {
        revokedUrl = url
      },
      createAnchor: () => anchor,
    })

    mgr.exportCommLogs()

    expect(clickSpy).toHaveBeenCalledTimes(1)
    expect(anchor.download.startsWith('io_logs_')).toBe(true)
    expect(revokedUrl).toBe('blob:test')
    expect(capturedBlob).toBeTruthy()
    expect(await capturedBlob!.text()).toContain('10:00:00.000\tRX\tA\\nB')
  })
})
