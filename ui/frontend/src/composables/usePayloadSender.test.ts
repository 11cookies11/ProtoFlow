import { describe, expect, it } from 'vitest'
import { ref } from 'vue'
import { applyHexLineEndings, applyLineEndings, usePayloadSender } from './usePayloadSender'

describe('usePayloadSender', () => {
  it('applies line endings helpers', () => {
    expect(applyLineEndings('AT', true, true)).toBe('AT\r\n')
    expect(applyHexLineEndings('AA BB', true, false)).toBe('AA BB 0D')
  })

  it('sends payload by mode', () => {
    let sentText = ''
    let sentHex = ''
    const sender = usePayloadSender({
      bridge: ref({
        send_text: (value: string) => {
          sentText = value
        },
        send_hex: (value: string) => {
          sentHex = value
        },
      }),
      sendMode: ref('text'),
      sendText: ref('PING'),
      sendHex: ref('AA BB'),
      appendCR: ref(true),
      appendLF: ref(false),
    })
    sender.sendPayload()
    expect(sentText).toBe('PING\r')

    const senderHex = usePayloadSender({
      bridge: ref({
        send_text: () => {},
        send_hex: (value: string) => {
          sentHex = value
        },
      }),
      sendMode: ref('hex'),
      sendText: ref(''),
      sendHex: ref('AA BB'),
      appendCR: ref(false),
      appendLF: ref(true),
    })
    senderHex.sendPayload()
    expect(sentHex).toBe('AA BB 0A')
  })

  it('sends quick command and updates mode buffers', () => {
    let sentText = ''
    let sentHex = ''
    const sendMode = ref('text')
    const sendText = ref('')
    const sendHex = ref('')

    const sender = usePayloadSender({
      bridge: ref({
        send_text: (value: string) => {
          sentText = value
        },
        send_hex: (value: string) => {
          sentHex = value
        },
      }),
      sendMode,
      sendText,
      sendHex,
      appendCR: ref(true),
      appendLF: ref(true),
    })

    sender.sendQuickCommand({ payload: 'AT+GMR', mode: 'text', appendCR: false, appendLF: true })
    expect(sendMode.value).toBe('text')
    expect(sendText.value).toBe('AT+GMR')
    expect(sentText).toBe('AT+GMR\n')

    sender.sendQuickCommand({ payload: 'AA BB', mode: 'hex', appendCR: true, appendLF: false })
    expect(sendMode.value).toBe('hex')
    expect(sendHex.value).toBe('AA BB')
    expect(sentHex).toBe('AA BB 0D')
  })
})
