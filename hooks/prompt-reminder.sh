#!/usr/bin/env bash
# UserPromptSubmit hook: inject the research-first reminder into the agent's
# context before it takes any action on the user's prompt. Fires once per
# user prompt — the strongest moment to influence first-action behaviour.
#
# Unconditional by design: the reminder is emitted on every prompt and the
# agent self-polices the "already searched this session" skip. Keeping the
# hook stateless avoids brittle detection of prior searches.
#
# Drains stdin (the hook receives the prompt JSON) but does not use it.
set -euo pipefail

cat >/dev/null || true

reminder="Before designing, planning, implementing custom code, refactoring or extracting code, choosing a tool/library/protocol, or debugging an unfamiliar error: RUN a WebSearch. This applies to questions/decisions you face, not user narration - if the user is stating what they are about to do (rather than asking how), absorb it as context rather than searching on it. (Or Read/Grep, if the question is purely about your own codebase - but most design questions have an external component.) Listing what you would search for does not count - execute the tool. Skipping because you think you already know is exactly the failure mode this rule guards against. Only valid skip: you have already run the same search in this session."

jq -n --arg msg "$reminder" '{
    hookSpecificOutput: {
        hookEventName: "UserPromptSubmit",
        additionalContext: $msg
    }
}'
