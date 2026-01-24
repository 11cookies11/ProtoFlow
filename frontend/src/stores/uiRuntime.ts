import { defineStore } from 'pinia'
import { validateUIConfig, type UIConfig, type WidgetSpec } from '@/ui/schema'

export type ParseError = {
  message: string
  line?: number
  column?: number
  path?: string
}

const DEFAULT_YAML = `ui:
  widgets:
    - id: wifi-ssid
      type: input.text
      props:
        label: WiFi SSID
        hint: 输入网络名称
        default: Office_Network
      bind: wifi.ssid
    - id: wifi-enabled
      type: input.switch
      props:
        label: 启用 WiFi
        default: true
      bind: wifi.enabled
    - id: apply
      type: action.button
      props:
        label: 应用设置
        payload:
          scope: wifi
      emit: action.wifi.apply
    - id: log-panel
      type: log.viewer
      props:
        title: WiFi 事件日志
      bind: wifi.events
  layout:
    type: split
    orientation: horizontal
    children:
      - type: leaf
        title: 网络配置
        widgets: [wifi-ssid, wifi-enabled, apply]
      - type: leaf
        title: 事件流
        widgets: [log-panel]
`

export const useUiRuntimeStore = defineStore('uiRuntime', {
  state: () => ({
    yamlText: DEFAULT_YAML,
    lastGoodConfig: null as UIConfig | null,
    parseError: null as ParseError | null,
    widgetsById: {} as Record<string, WidgetSpec>,
    selectedWidgetId: null as string | null,
    inputValues: {} as Record<string, unknown>,
    eventLog: [] as Array<{ ts: number; emit: string; payload?: unknown; source?: string }>,
    dataBus: {} as Record<string, unknown[]>,
    _debounceTimer: 0 as number | 0,
  }),
  actions: {
    setYamlText(text: string) {
      this.yamlText = text
    },
    tryParseAndValidate() {
      if (this._debounceTimer) {
        clearTimeout(this._debounceTimer)
      }
      this._debounceTimer = window.setTimeout(() => {
        this._parseWithBridge()
      }, 300)
    },
    async _parseWithBridge() {
      const bridge = (window as unknown as { bridge?: any }).bridge
      if (bridge && bridge.parse_ui_yaml) {
        try {
          const result = await Promise.resolve(bridge.parse_ui_yaml(this.yamlText))
          this._handleParseResult(result)
          return
        } catch (error) {
          this.parseError = { message: String(error || 'bridge parse error') }
          return
        }
      }
      this.parseError = { message: 'WebBridge unavailable for YAML parsing' }
    },
    _handleParseResult(result: { ok: boolean; value?: unknown; error?: { message: string; line?: number; column?: number } }) {
      if (!result.ok) {
        const err = result.error || { message: 'YAML parse error' }
        this.parseError = { message: err.message, line: err.line, column: err.column }
        return
      }
      const validated = validateUIConfig(result.value)
      if (!validated.ok) {
        this.parseError = { message: validated.error.message, path: validated.error.path }
        return
      }
      const config = validated.value
      const widgetsById: Record<string, WidgetSpec> = {}
      config.ui.widgets.forEach((widget) => {
        widgetsById[widget.id] = { ...widget, props: widget.props || {} }
      })
      this.widgetsById = widgetsById
      this.lastGoodConfig = config
      this.parseError = null
    },
    selectWidget(id: string) {
      this.selectedWidgetId = id
    },
    getInputValue(id: string, fallback?: unknown) {
      if (this.inputValues[id] === undefined && fallback !== undefined) {
        this.inputValues[id] = fallback
      }
      return this.inputValues[id]
    },
    setInputValue(id: string, value: unknown, bind?: string) {
      this.inputValues[id] = value
      if (bind) {
        this.pushData(bind, value)
      }
    },
    dispatchEvent(event: { emit: string; payload?: unknown; source?: string }) {
      this.eventLog.push({ ts: Date.now(), ...event })
      const bridge = (window as unknown as { bridge?: any }).bridge
      if (bridge && bridge.dispatch_ui_event) {
        bridge.dispatch_ui_event({ ts: Date.now(), ...event })
      }
    },
    pushData(bindKey: string, value: unknown) {
      if (!this.dataBus[bindKey]) {
        this.dataBus[bindKey] = []
      }
      this.dataBus[bindKey].push({ ts: Date.now(), value })
      if (this.dataBus[bindKey].length > 200) {
        this.dataBus[bindKey] = this.dataBus[bindKey].slice(-200)
      }
    },
    bindBridge(bridge: any) {
      if (!bridge || !bridge.ui_event_log) return
      bridge.ui_event_log.connect((payload: any) => {
        if (!payload) return
        this.eventLog.push({
          ts: payload.ts ? Number(payload.ts) : Date.now(),
          emit: payload.emit || '',
          payload: payload.payload,
          source: payload.source,
        })
      })
    },
  },
})
