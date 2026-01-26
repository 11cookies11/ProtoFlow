import type { Component } from 'vue'
import TextInput from '@/components/ui-kit/inputs/TextInput.vue'
import NumberInput from '@/components/ui-kit/inputs/NumberInput.vue'
import SwitchInput from '@/components/ui-kit/inputs/SwitchInput.vue'
import TextareaInput from '@/components/ui-kit/inputs/TextareaInput.vue'
import SelectInput from '@/components/ui-kit/inputs/SelectInput.vue'
import PrimaryButton from '@/components/ui-kit/actions/PrimaryButton.vue'
import EventLogPanel from '@/components/ui-kit/EventLogPanel.vue'
import InspectorJSON from '@/components/ui-kit/InspectorJSON.vue'
import UnknownWidget from './UnknownWidget.vue'

export const widgetRegistry: Record<string, Component> = {
  'input.text': TextInput,
  'input.number': NumberInput,
  'input.switch': SwitchInput,
  'input.textarea': TextareaInput,
  'input.select': SelectInput,
  'action.button': PrimaryButton,
  'log.viewer': EventLogPanel,
  'inspector.json': InspectorJSON,
}

export function resolveWidget(type: string): Component {
  return widgetRegistry[type] || UnknownWidget
}
