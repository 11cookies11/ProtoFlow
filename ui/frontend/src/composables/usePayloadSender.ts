import type { Ref } from 'vue'

type UsePayloadSenderOptions = {
  bridge: Ref<any>
  sendMode: Ref<string>
  sendText: Ref<string>
  sendHex: Ref<string>
  appendCR: Ref<boolean>
  appendLF: Ref<boolean>
}

export function applyLineEndings(text: string, cr = false, lf = false) {
  let payload = text
  if (cr) payload += '\r'
  if (lf) payload += '\n'
  return payload
}

export function applyHexLineEndings(text: string, cr = false, lf = false) {
  const parts = String(text || '')
    .trim()
    .split(/\s+/)
    .filter(Boolean)
  if (cr) parts.push('0D')
  if (lf) parts.push('0A')
  return parts.join(' ')
}

export function usePayloadSender(options: UsePayloadSenderOptions) {
  function sendAscii() {
    if (!options.bridge.value || !options.sendText.value) return
    const payload = applyLineEndings(options.sendText.value, options.appendCR.value, options.appendLF.value)
    options.bridge.value.send_text(payload)
  }

  function sendHexData() {
    if (!options.bridge.value || !options.sendHex.value) return
    const payload = applyHexLineEndings(options.sendHex.value, options.appendCR.value, options.appendLF.value)
    options.bridge.value.send_hex(payload)
  }

  function sendPayload() {
    if (options.sendMode.value === 'hex') {
      sendHexData()
      return
    }
    sendAscii()
  }

  function sendQuickCommand(cmd: any) {
    if (!cmd) return
    const payload = typeof cmd === 'string' ? cmd : cmd.payload || cmd.name || ''
    if (!payload) return
    const mode = typeof cmd === 'string' ? 'text' : cmd.mode || 'text'
    const cr = typeof cmd === 'string' ? options.appendCR.value : cmd.appendCR ?? options.appendCR.value
    const lf = typeof cmd === 'string' ? options.appendLF.value : cmd.appendLF ?? options.appendLF.value
    if (mode === 'hex') {
      options.sendMode.value = 'hex'
      options.sendHex.value = payload
      if (!options.bridge.value) return
      const data = applyHexLineEndings(payload, cr, lf)
      options.bridge.value.send_hex(data)
      return
    }
    options.sendMode.value = 'text'
    options.sendText.value = payload
    if (!options.bridge.value) return
    const data = applyLineEndings(payload, cr, lf)
    options.bridge.value.send_text(data)
  }

  return {
    sendPayload,
    sendQuickCommand,
  }
}
