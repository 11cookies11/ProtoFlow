import { describe, expect, it, vi } from 'vitest'
import { ref } from 'vue'
import { countQuickPayload, useQuickCommands } from './useQuickCommands'

function createManager() {
  const quickCommands = ref<any[]>([{ id: 'q1', name: 'AT', payload: 'AT', mode: 'text', appendCR: true, appendLF: true }])
  const quickDialogOpen = ref(false)
  const quickDialogMode = ref('create')
  const quickEditingId = ref('')
  const quickDeleteOpen = ref(false)
  const quickDeleting = ref<any>(null)
  const quickDraft = ref<any>({ name: '', payload: '', mode: 'text', appendCR: true, appendLF: true })
  const sendMode = ref('text')
  const appendCR = ref(true)
  const appendLF = ref(false)
  const alertSpy = vi.fn()
  const manager = useQuickCommands({
    quickCommands,
    quickDialogOpen,
    quickDialogMode,
    quickEditingId,
    quickDeleteOpen,
    quickDeleting,
    quickDraft,
    sendMode,
    appendCR,
    appendLF,
    tr: (text) => text,
    alert: alertSpy,
    generateId: () => 'fixed-id',
  })
  return { quickCommands, quickDialogOpen, quickDialogMode, quickEditingId, quickDeleteOpen, quickDeleting, quickDraft, alertSpy, manager }
}

describe('useQuickCommands', () => {
  it('normalizes quick commands list', () => {
    const { quickCommands, manager } = createManager()
    const result = manager.normalizeQuickCommands(['PING', { name: 'HEX', payload: 'AA', mode: 'hex' }, null])
    expect(result).toHaveLength(2)
    expect(result[0].name).toBe('PING')
    expect(result[1].mode).toBe('hex')
    expect(manager.normalizeQuickCommands(null)).toBe(quickCommands.value)
  })

  it('opens and saves create/edit dialogs', () => {
    const { quickCommands, quickDialogMode, quickDialogOpen, quickDraft, manager } = createManager()
    manager.openQuickCommandDialog()
    expect(quickDialogOpen.value).toBe(true)
    expect(quickDialogMode.value).toBe('create')

    quickDraft.value = { name: 'CMD', payload: 'CMD', mode: 'text', appendCR: true, appendLF: true }
    manager.saveQuickCommand()
    expect(quickCommands.value.some((item) => item.id === 'fixed-id')).toBe(true)

    manager.openQuickCommandDialog(quickCommands.value[0])
    quickDraft.value = { name: 'AT2', payload: 'AT2', mode: 'text', appendCR: true, appendLF: true }
    manager.saveQuickCommand()
    expect(quickCommands.value[0].name).toBe('AT2')
  })

  it('deletes command via confirm flow', () => {
    const { quickCommands, quickDeleteOpen, manager } = createManager()
    manager.openQuickDeleteDialog(quickCommands.value[0])
    expect(quickDeleteOpen.value).toBe(true)
    manager.confirmQuickDelete()
    expect(quickCommands.value).toHaveLength(0)
  })

  it('alerts when save payload/name is empty', () => {
    const { alertSpy, quickDraft, manager } = createManager()
    quickDraft.value = { name: '', payload: '', mode: 'text', appendCR: true, appendLF: true }
    manager.saveQuickCommand()
    expect(alertSpy).toHaveBeenCalledTimes(1)
  })

  it('counts quick payload size', () => {
    expect(countQuickPayload('AA BB 0D', 'hex')).toBe(3)
    expect(countQuickPayload('HELLO', 'text')).toBe(5)
  })
})
