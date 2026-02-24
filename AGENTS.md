# AGENTS.md

This file defines repository-specific instructions for coding agents (including Codex).

## Where Progress Contract

- Source file: `where.sourceFile` (default: `.where-agent-progress.md`)
- Format: **Markdown only** (JSON is not allowed)
- Encoding: UTF-8

Required structure:

```md
# Plan: <title>
- [ ] <task>
- [~] <task>
- [!] <task>
- [x] <task>
```

Status mapping:

- `[ ]` -> `todo`
- `[~]` -> `in_progress`
- `[!]` -> `blocked`
- `[x]` -> `done`

## Agent Behavior

- Keep one task per line.
- Update existing tasks when status changes; avoid duplicate tasks.
- Keep task titles short and actionable.
- For blocked tasks, include blocker reason in the title.
- Do not output JSON for progress data.
- Do not add unrelated long prose in the progress file.

## Reference

- Detailed spec: `docs/AGENT_PROGRESS_SPEC.zh-CN.md`
