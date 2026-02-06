import { z } from 'zod'

export type WidgetSpec = {
  id: string
  type: string
  props: Record<string, unknown>
  bind?: string
  emit?: string
}

export type LayoutNode =
  | {
      type: 'split'
      orientation: 'horizontal' | 'vertical'
      children: LayoutNode[]
    }
  | {
      type: 'leaf'
      title?: string
      widgets: string[]
    }

export type UIConfig = {
  ui: {
    widgets: WidgetSpec[]
    layout: LayoutNode
  }
}

const widgetSchema = z.object({
  id: z.string().min(1),
  type: z.string().min(1),
  props: z.record(z.any()).optional().default({}),
  bind: z.string().optional(),
  emit: z.string().optional(),
})

const layoutSchema: z.ZodType<LayoutNode> = z.lazy(() =>
  z.discriminatedUnion('type', [
    z.object({
      type: z.literal('split'),
      orientation: z.enum(['horizontal', 'vertical']),
      children: z.array(layoutSchema).min(1),
    }),
    z.object({
      type: z.literal('leaf'),
      title: z.string().optional(),
      widgets: z.array(z.string()).min(1),
    }),
  ])
)

const uiSchema = z.object({
  ui: z.object({
    widgets: z.array(widgetSchema).default([]),
    layout: layoutSchema,
  }),
})

export function validateUIConfig(obj: unknown):
  | { ok: true; value: UIConfig }
  | { ok: false; error: { message: string; path: string } } {
  const parsed = uiSchema.safeParse(obj)
  if (!parsed.success) {
    const issue = parsed.error.issues[0]
    const path = issue.path.length ? issue.path.join('.') : 'ui'
    return { ok: false, error: { message: issue.message, path } }
  }

  const config = parsed.data as UIConfig
  const seen = new Set<string>()
  for (const widget of config.ui.widgets) {
    if (seen.has(widget.id)) {
      return { ok: false, error: { message: `duplicate widget id: ${widget.id}`, path: 'ui.widgets' } }
    }
    seen.add(widget.id)
  }

  const widgetsById = new Set(config.ui.widgets.map((w) => w.id))
  const missing: string[] = []
  function walk(node: LayoutNode, basePath: string) {
    if (node.type === 'split') {
      node.children.forEach((child, idx) => walk(child, `${basePath}.children[${idx}]`))
    } else {
      node.widgets.forEach((id, idx) => {
        if (!widgetsById.has(id)) {
          missing.push(`${basePath}.widgets[${idx}] -> ${id}`)
        }
      })
    }
  }
  walk(config.ui.layout, 'ui.layout')
  if (missing.length) {
    return { ok: false, error: { message: `unknown widget id: ${missing[0]}`, path: 'ui.layout' } }
  }

  return { ok: true, value: config }
}
