<template>
  <LayoutNodeRenderer :node="config.ui.layout" />
</template>

<script setup lang="ts">
import { defineComponent, h, inject } from 'vue'
import PanelCard from '@/components/ui-kit/PanelCard.vue'
import SplitContainer from '@/components/ui-kit/SplitContainer.vue'
import { resolveWidget } from './registry'
import type { LayoutNode, UIConfig, WidgetSpec } from './schema'
import { useUiRuntimeStore } from '@/stores/uiRuntime'

const props = defineProps<{ config: UIConfig; widgetsById: Record<string, WidgetSpec> }>()
const store = useUiRuntimeStore()
const tr = inject('tr', (text: string) => text)

const LayoutNodeRenderer = defineComponent({
  name: 'LayoutNodeRenderer',
  props: {
    node: {
      type: Object as () => LayoutNode,
      required: true,
    },
  },
  setup(nodeProps) {
    return () => {
      const node = nodeProps.node
      if (node.type === 'split') {
        return h(
          SplitContainer,
          { orientation: node.orientation },
          {
            default: () => node.children.map((child) => h(LayoutNodeRenderer, { node: child })),
          }
        )
      }

      return h(
        PanelCard,
        { title: node.title },
        {
          default: () =>
            node.widgets.map((id) => {
              const widget = props.widgetsById[id]
              if (!widget) return null
              const Comp = resolveWidget(widget.type)
              const isInput = widget.type.startsWith('input.')
              const isAction = widget.type.startsWith('action.')
              const isLogViewer = widget.type === 'log.viewer'
              const modelValue = store.getInputValue(widget.id, widget.props?.default)

              const wrapperClass = [
                'rounded-lg',
                'p-2',
                'transition',
                'cursor-pointer',
                store.selectedWidgetId === widget.id ? 'ring-2 ring-primary/40' : 'hover:bg-slate-50',
              ]
                .filter(Boolean)
                .join(' ')

              const onClick = () => store.selectWidget(widget.id)

              const commonProps = {
                ...(widget.props || {}),
              }
              const localizedProps = {
                ...commonProps,
                label: commonProps.label ? tr(commonProps.label) : commonProps.label,
                title: commonProps.title ? tr(commonProps.title) : commonProps.title,
                hint: commonProps.hint ? tr(commonProps.hint) : commonProps.hint,
                placeholder: commonProps.placeholder ? tr(commonProps.placeholder) : commonProps.placeholder,
              }

              if (isLogViewer) {
                const items = widget.bind ? store.dataBus[widget.bind] || [] : []
                return h('div', { class: wrapperClass, onClick }, [
                  h(Comp, {
                    ...localizedProps,
                    title: localizedProps.title || widget.id,
                    value: items.slice(-50),
                  }),
                ])
              }

              if (isAction) {
                return h('div', { class: wrapperClass, onClick }, [
                  h(
                    Comp,
                    {
                      ...localizedProps,
                      onClick: () => {
                        if (widget.type === 'action.button') {
                          const payload = widget.props?.payload || { source: widget.id }
                          store.dispatchEvent({ emit: widget.emit || 'action.unknown', payload, source: widget.id })
                          // TODO: sendEventToBackend
                        }
                      },
                    },
                    { default: () => localizedProps.label || tr('动作') }
                  ),
                ])
              }

              if (isInput) {
                return h('div', { class: wrapperClass, onClick }, [
                  h(Comp, {
                    ...localizedProps,
                    modelValue,
                    'onUpdate:modelValue': (value: unknown) => store.setInputValue(widget.id, value, widget.bind),
                  }),
                ])
              }

              return h('div', { class: wrapperClass, onClick }, [
                h(Comp, {
                  ...localizedProps,
                  widgetId: widget.id,
                  widgetType: widget.type,
                }),
              ])
            }),
        }
      )
    }
  },
})
</script>
