import { describe, expect, it } from 'vitest'
import { ref } from 'vue'
import { useProtocolManager } from './useProtocolManager'

function withResult(value: any, handler: (payload: any) => void) {
  handler(value)
}

describe('useProtocolManager', () => {
  it('maps and filters protocol cards', () => {
    const bridge = ref({})
    const mgr = useProtocolManager({
      bridge,
      tr: (text) => text,
      withResult,
    })

    mgr.setProtocols([
      { key: 'modbus_rtu', driver: 'DrvA', status: 'available', source: 'builtin' },
      { key: 'custom_x', driver: 'DrvB', status: 'custom', source: 'custom', category: 'custom' },
    ])
    expect(mgr.filteredProtocolCards.value.length).toBe(2)
    mgr.setProtocolTab('custom')
    expect(mgr.filteredProtocolCards.value.length).toBe(1)
  })

  it('opens create/edit dialogs and updates draft', () => {
    const mgr = useProtocolManager({
      bridge: ref({}),
      tr: (text) => text,
      withResult,
    })
    mgr.openCreateProtocol()
    expect(mgr.protocolDialogOpen.value).toBe(true)
    expect(mgr.protocolDialogMode.value).toBe('create')

    mgr.openProtocolDetails({ id: 'p1', name: 'A', key: 'a', source: 'custom', status: 'custom', category: 'custom' })
    expect(mgr.protocolDialogMode.value).toBe('edit')
    mgr.updateProtocolDraft({ field: 'name', value: 'B' })
    expect(mgr.protocolDraft.value.name).toBe('B')
  })

  it('save and delete call bridge paths', () => {
    let created = 0
    let updated = 0
    let deleted = 0
    const bridge = ref({
      list_protocols: () => [],
      create_protocol: () => {
        created += 1
        return true
      },
      update_protocol: () => {
        updated += 1
        return true
      },
      delete_protocol: () => {
        deleted += 1
        return true
      },
    })
    const mgr = useProtocolManager({
      bridge,
      tr: (text) => text,
      withResult,
    })

    mgr.openCreateProtocol()
    mgr.saveProtocol()
    expect(created).toBe(1)

    mgr.openProtocolDetails({ id: 'p1', name: 'A', key: 'a', source: 'custom', status: 'custom', category: 'custom' })
    mgr.saveProtocol()
    expect(updated).toBe(1)

    mgr.openProtocolDelete({ id: 'p1', source: 'custom' })
    mgr.confirmProtocolDelete()
    expect(deleted).toBe(1)
  })
})
