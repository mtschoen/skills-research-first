# running-spikes

Claude Code skill that flips Claude's default toward **running code** over **reading more** when the question is observable behavior of an external system.

Lives as a submodule under [skills-dev](https://github.com/mtschoen/skills-dev) and installed via `install-skills.{sh,bat}`.

## What it does

Phase-agnostically detects when Claude is about to do extended Read / Grep / thinking on a question that running code could resolve in a few minutes. Suggests a small spike (single-file probe or scratch hello-world) instead. Findings land in `~/.claude/notes/spike_<slug>.md` so future sessions don't re-litigate.

See [SKILL.md](./SKILL.md) for the full skill text.

## Conventions

- **Repo name:** `skills-running-spikes` on both Gitea (`schoen/`) and GitHub (`mtschoen/`).
- **Submodule path** in skills-dev: `running-spikes/`.
- **Workspace** for eval iteration lives at `running-spikes/workspace/`, gitignored.
- **License:** MIT (inherits from skills-dev).
