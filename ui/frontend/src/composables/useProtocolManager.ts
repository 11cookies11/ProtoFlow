import { computed, ref, type Ref } from 'vue'

type WithResultFn = (value: any, handler: (payload: any) => void) => void

type UseProtocolManagerOptions = {
  bridge: Ref<any>
  tr: (text: string) => string
  withResult: WithResultFn
}

function protocolCategory(key: string) {
  const name = String(key || '').toLowerCase()
  if (name === 'modbus_rtu' || name === 'modbus-rtu') return 'modbus-rtu'
  if (name === 'modbus_ascii' || name === 'modbus-ascii') return 'modbus-ascii'
  if (name === 'modbus_tcp' || name === 'modbus-tcp') return 'modbus-tcp'
  if (name.includes('tcp')) return 'tcp'
  return 'custom'
}

function prettyProtocolName(key: string, fallback: string, tr: (text: string) => string) {
  const value = String(key || '').trim()
  if (!value) return fallback || tr('协议')
  const parts = value.split('_').map((part) => {
    const upper = part.toUpperCase()
    if (['RTU', 'TCP', 'SCPI', 'AT', 'XMODEM', 'YMODEM'].includes(upper)) return upper
    if (upper.length <= 2) return upper
    return part.charAt(0).toUpperCase() + part.slice(1)
  })
  return parts.join(' ')
}

function protocolStatusInfo(status: string, tr: (text: string) => string) {
  if (status === 'available') return { text: tr('可用'), className: 'badge-green' }
  if (status === 'custom') return { text: tr('自定义'), className: 'badge-blue' }
  if (status === 'disabled') return { text: tr('已禁用'), className: 'badge-gray' }
  return { text: status || tr('未知'), className: 'badge-gray' }
}

export function useProtocolManager(options: UseProtocolManagerOptions) {
  const protocolTab = ref('all')
  const protocolDialogOpen = ref(false)
  const protocolDialogMode = ref('create')
  const protocolEditing = ref<any>(null)
  const protocolDeleteOpen = ref(false)
  const protocolDeleting = ref<any>(null)
  const protocolDraft = ref({
    id: '',
    key: '',
    name: '',
    desc: '',
    category: 'custom',
    status: 'custom',
  })
  const protocolCards = ref<any[]>([])

  const filteredProtocolCards = computed(() => {
    if (protocolTab.value === 'all') return protocolCards.value
    return protocolCards.value.filter((card) => card.category === protocolTab.value)
  })

  function setProtocols(items: any[]) {
    const list = Array.isArray(items) ? items : []
    protocolCards.value = list.map((item) => {
      const key = String(item.key || item.id || '')
      const driver = String(item.driver || '')
      const name = String(item.name || '')
      const category = String(item.category || protocolCategory(key))
      const status = String(item.status || 'available')
      const source = String(item.source || 'builtin')
      const desc = String(item.desc || '')
      const statusInfo = protocolStatusInfo(status, options.tr)
      return {
        id: key || driver || Math.random().toString(36).slice(2),
        key,
        name: name || prettyProtocolName(key, driver, options.tr),
        driver,
        category,
        desc,
        statusText: statusInfo.text,
        statusClass: statusInfo.className,
        status,
        source,
        rows: [
          { label: options.tr('键名'), value: key || '--' },
          { label: options.tr('驱动'), value: driver || '--' },
          { label: options.tr('分类'), value: category || '--' },
        ],
      }
    })
  }

  function refreshProtocols() {
    if (!options.bridge.value || !options.bridge.value.list_protocols) return
    options.withResult(options.bridge.value.list_protocols(), (items) => {
      setProtocols(items)
    })
  }

  function resetProtocolDraft() {
    protocolDraft.value = {
      id: '',
      key: '',
      name: '',
      desc: '',
      category: 'custom',
      status: 'custom',
    }
  }

  function openCreateProtocol() {
    protocolDialogMode.value = 'create'
    protocolEditing.value = null
    resetProtocolDraft()
    protocolDialogOpen.value = true
  }

  function openProtocolDetails(card: any) {
    if (!card) return
    protocolEditing.value = card
    protocolDialogMode.value = card.source === 'custom' ? 'edit' : 'view'
    protocolDraft.value = {
      id: card.id || '',
      key: card.key || '',
      name: card.name || '',
      desc: card.desc || '',
      category: card.category || 'custom',
      status: card.status || 'available',
    }
    protocolDialogOpen.value = true
  }

  function closeProtocolDialog() {
    protocolDialogOpen.value = false
  }

  function updateProtocolDraft({ field, value }: { field: string; value: any }) {
    if (!field) return
    protocolDraft.value = {
      ...protocolDraft.value,
      [field]: value,
    }
  }

  function saveProtocol() {
    if (!options.bridge.value) {
      protocolDialogOpen.value = false
      return
    }
    const payload = {
      id: protocolDraft.value.id,
      key: protocolDraft.value.key,
      name: protocolDraft.value.name,
      desc: protocolDraft.value.desc,
      category: protocolDraft.value.category,
      status: protocolDraft.value.status,
    }
    if (protocolDialogMode.value === 'create') {
      if (!options.bridge.value.create_protocol) return
      options.withResult(options.bridge.value.create_protocol(payload), () => {
        refreshProtocols()
        protocolDialogOpen.value = false
      })
      return
    }
    if (protocolDialogMode.value === 'edit') {
      if (!options.bridge.value.update_protocol) return
      options.withResult(options.bridge.value.update_protocol(payload), () => {
        refreshProtocols()
        protocolDialogOpen.value = false
      })
      return
    }
    protocolDialogOpen.value = false
  }

  function openProtocolDelete(card: any) {
    if (!card || card.source !== 'custom') return
    protocolDeleting.value = card
    protocolDeleteOpen.value = true
  }

  function closeProtocolDelete() {
    protocolDeleteOpen.value = false
    protocolDeleting.value = null
  }

  function confirmProtocolDelete() {
    if (!options.bridge.value || !options.bridge.value.delete_protocol || !protocolDeleting.value) {
      closeProtocolDelete()
      return
    }
    const id = protocolDeleting.value.id
    options.withResult(options.bridge.value.delete_protocol(id), () => {
      refreshProtocols()
      closeProtocolDelete()
    })
  }

  function setProtocolTab(tab: string) {
    protocolTab.value = tab
  }

  return {
    protocolTab,
    protocolDialogOpen,
    protocolDialogMode,
    protocolEditing,
    protocolDeleteOpen,
    protocolDeleting,
    protocolDraft,
    protocolCards,
    filteredProtocolCards,
    setProtocols,
    refreshProtocols,
    openCreateProtocol,
    openProtocolDetails,
    closeProtocolDialog,
    updateProtocolDraft,
    saveProtocol,
    openProtocolDelete,
    closeProtocolDelete,
    confirmProtocolDelete,
    setProtocolTab,
  }
}
