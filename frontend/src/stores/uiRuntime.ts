import { defineStore } from 'pinia'
import { parseYamlUI } from '@/ui/yaml'
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
        const parsed = parseYamlUI(this.yamlText)
        if (!parsed.ok) {
          this.parseError = { message: parsed.error.message, line: parsed.error.line, column: parsed.error.column }
          return
        }
        const validated = validateUIConfig(parsed.value)
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
      }, 300)
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
  },
})
