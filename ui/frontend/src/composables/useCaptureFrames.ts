import type { Ref } from 'vue'

type UseCaptureFramesOptions = {
  captureFrames: Ref<any[]>
  captureMeta: Ref<any>
  maxCaptureFrames: number
}

export function formatCaptureTime(ts: number) {
  const date = new Date((ts || 0) * 1000)
  const pad = (value: number, length = 2) => String(value).padStart(length, '0')
  return `${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}.${pad(
    date.getMilliseconds(),
    3
  )}`
}

export function mapCaptureFrame(payload: any) {
  if (!payload || typeof payload !== 'object') return null
  const protocol = payload.protocol || {}
  const unknown = Boolean(protocol.unknown)
  const hasErrors = Array.isArray(payload.errors) && payload.errors.length > 0
  const direction = payload.direction || 'RX'
  const tone = unknown || hasErrors ? 'red' : direction === 'TX' ? 'blue' : 'green'
  return {
    id: payload.id || `cap-${Date.now()}`,
    direction,
    time: formatCaptureTime(payload.timestamp || Date.now() / 1000),
    size: payload.length || 0,
    note: payload.raw_hex || '',
    summary: payload.summary || '',
    summaryText: payload.summary || '',
    tone,
    warn: unknown || hasErrors,
    channel: payload.channel || '',
    baud: payload.baud || '',
    protocolLabel: protocol.name || (unknown ? 'Unknown' : ''),
    protocolType: unknown
      ? 'unknown'
      : (protocol.name || '').toLowerCase().includes('modbus')
        ? 'modbus'
        : 'custom',
    protocolTooltip: protocol.name ? `${protocol.name}${protocol.version ? ` ${protocol.version}` : ''}` : '',
    hexDump: payload.hex_dump || null,
    tree: payload.tree || [],
  }
}

export function useCaptureFrames(options: UseCaptureFramesOptions) {
  function ingestCaptureFrame(payload: any) {
    const frame = mapCaptureFrame(payload)
    if (!frame) return
    options.captureFrames.value.push(frame)
    if (options.captureFrames.value.length > options.maxCaptureFrames) {
      options.captureFrames.value.splice(0, options.captureFrames.value.length - options.maxCaptureFrames)
    }
    options.captureMeta.value.totalFrames += 1
    options.captureMeta.value.rangeEnd = options.captureMeta.value.totalFrames
    options.captureMeta.value.rangeStart = Math.max(
      1,
      options.captureMeta.value.totalFrames - options.captureFrames.value.length + 1
    )
    options.captureMeta.value.bufferUsed = Math.min(
      100,
      Math.round((options.captureFrames.value.length / options.maxCaptureFrames) * 100)
    )
    if (payload && payload.channel) {
      options.captureMeta.value.channel = payload.channel
    }
  }

  return {
    ingestCaptureFrame,
  }
}
