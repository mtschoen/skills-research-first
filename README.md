# skills-research-first

"Search before you decide" — a Claude Code skill plus a `UserPromptSubmit`
hook that nudges the agent to run a WebSearch (or Read/Grep for
codebase-only questions) before designing, choosing a tool, writing
custom code, refactoring, or debugging an unfamiliar error.

## What it is

- `SKILL.md` — the discipline the agent follows: which decisions trigger a
  search, what counts as a decision vs. user narration, and the one valid
  skip (already searched this session).
- `hooks/prompt-reminder.sh` — a `UserPromptSubmit` hook that injects the
  reminder as `additionalContext` on every prompt. Unconditional by
  design; the agent self-polices the "already searched" skip.

## Install

`install-skills.{sh,bat}` (in the skills-dev umbrella) ships `SKILL.md`
plus the `hooks/` dir (declared in `.skillpack`) into
`~/.claude/skills/research-first/`.

The hook is **not** auto-wired — like every skill hook, add it to
`~/.claude/settings.json` under `UserPromptSubmit` manually:

```json
{
  "type": "command",
  "command": "bash ~/.claude/skills/research-first/hooks/prompt-reminder.sh"
}
```

This replaces the older inline `echo '{...}'` UserPromptSubmit hook that
hard-coded the same reminder string in `settings.json`.
