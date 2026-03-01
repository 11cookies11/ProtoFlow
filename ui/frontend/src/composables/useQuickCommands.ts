import type { Ref } from 'vue'

type QuickCommand = {
  id: string
  name: string
  payload: string
  mode: string
  appendCR: boolean
  appendLF: boolean
}

type UseQuickCommandsOptions = {
  quickCommands: Ref<QuickCommand[]>
  quickDialogOpen: Ref<boolean>
  quickDialogMode: Ref<string>
  quickEditingId: Ref<string>
  quickDeleteOpen: Ref<boolean>
  quickDeleting: Ref<any>
  quickDraft: Ref<any>
  sendMode: Ref<string>
  appendCR: Ref<boolean>
  appendLF: Ref<boolean>
  tr: (text: string) => string
  alert?: (message: string) => void
  generateId?: () => string
}

const defaultAlert = (message: string) => window.alert(message)
const defaultId = () => `qc_${Date.now()}_${Math.random().toString(16).slice(2, 6)}`

export function countQuickPayload(payload: string, mode: string) {
  const value = String(payload || '')
  if (mode === 'hex') {
    const cleaned = value.replace(/[^0-9a-fA-F]/g, '')
    return Math.floor(cleaned.length / 2)
  }
  return value.length
}

export function useQuickCommands(options: UseQuickCommandsOptions) {
  const showAlert = options.alert || defaultAlert
  const createId = options.generateId || defaultId

  function normalizeQuickCommands(list: any) {
    if (!Array.isArray(list)) return options.quickCommands.value
    const normalized: QuickCommand[] = []
    list.forEach((item, index) => {
      if (!item) return
      if (typeof item === 'string') {
        normalized.push({
          id: `qc_${index}`,
          name: item,
          payload: item,
          mode: 'text',
          appendCR: true,
          appendLF: true,
        })
        return
      }
      const name = String(item.name || item.payload || '').trim()
      const payload = String(item.payload || item.name || '').trim()
      if (!name || !payload) return
      normalized.push({
        id: item.id || `qc_${index}`,
        name,
        payload,
        mode: item.mode === 'hex' ? 'hex' : 'text',
        appendCR: item.appendCR ?? true,
        appendLF: item.appendLF ?? true,
      })
    })
    return normalized.length ? normalized : options.quickCommands.value
  }

  function openQuickDeleteDialog(cmd: any) {
    if (!cmd) return
    options.quickDeleting.value = cmd
    options.quickDeleteOpen.value = true
  }

  function closeQuickDeleteDialog() {
    options.quickDeleteOpen.value = false
    options.quickDeleting.value = null
  }

  function confirmQuickDelete() {
    if (!options.quickDeleting.value) return
    options.quickCommands.value = options.quickCommands.value.filter((item) => item.id !== options.quickDeleting.value.id)
    closeQuickDeleteDialog()
  }

  function openQuickCommandDialog(cmd?: any) {
    if (cmd) {
      options.quickDialogMode.value = 'edit'
      options.quickEditingId.value = cmd.id
      options.quickDraft.value = {
        name: cmd.name || '',
        payload: cmd.payload || cmd.name || '',
        mode: cmd.mode === 'hex' ? 'hex' : 'text',
        appendCR: cmd.appendCR ?? true,
        appendLF: cmd.appendLF ?? true,
      }
    } else {
      options.quickDialogMode.value = 'create'
      options.quickEditingId.value = ''
      options.quickDraft.value = {
        name: '',
        payload: '',
        mode: options.sendMode.value === 'hex' ? 'hex' : 'text',
        appendCR: options.appendCR.value,
        appendLF: options.appendLF.value,
      }
    }
    options.quickDialogOpen.value = true
  }

  function closeQuickCommandDialog() {
    options.quickDialogOpen.value = false
  }

  function saveQuickCommand() {
    const name = String(options.quickDraft.value.name || '').trim()
    const payload = String(options.quickDraft.value.payload || '').trim()
    if (!name || !payload) {
      showAlert(options.tr('请输入指令名称和内容'))
      return
    }
    const record = {
      name,
      payload: options.quickDraft.value.payload,
      mode: options.quickDraft.value.mode === 'hex' ? 'hex' : 'text',
      appendCR: options.quickDraft.value.appendCR ?? true,
      appendLF: options.quickDraft.value.appendLF ?? true,
    }
    if (options.quickDialogMode.value === 'edit' && options.quickEditingId.value) {
      const target = options.quickCommands.value.find((item) => item.id === options.quickEditingId.value)
      if (target) {
        Object.assign(target, record)
      } else {
        options.quickCommands.value.push({
          id: options.quickEditingId.value,
          ...record,
        })
      }
    } else {
      options.quickCommands.value.push({
        id: createId(),
        ...record,
      })
    }
    closeQuickCommandDialog()
  }

  function addQuickCommand() {
    openQuickCommandDialog()
  }

  function editQuickCommand(cmd: any) {
    openQuickCommandDialog(cmd)
  }

  function removeQuickCommand(cmd: any) {
    openQuickDeleteDialog(cmd)
  }

  return {
    normalizeQuickCommands,
    openQuickDeleteDialog,
    closeQuickDeleteDialog,
    confirmQuickDelete,
    openQuickCommandDialog,
    closeQuickCommandDialog,
    saveQuickCommand,
    addQuickCommand,
    editQuickCommand,
    removeQuickCommand,
    countQuickPayload,
  }
}
