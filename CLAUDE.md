# Starburst MCP2 — Project Instructions

## MANDATORY: Read Before Any Action

**Session memory file:** `~/.claude/projects/c--Users-Lenovo/memory/starburst-mcp2-session.md`
Read this file at the START of every conversation to understand current project state.

---

## Development Protocol

### Pre-Execution Logging (NON-NEGOTIABLE)

Before executing ANY code, CLI command, API call, or automation:
1. **Log the action** to the session memory file with timestamp, action type, purpose, and code/command
2. **Execute** the action
3. **Log the result** — including full errors, never skip failures
4. **Log next step** — what comes after this action

If logging fails or is skipped → STOP development and fix logging first.

### Action Classification

Every action must be tagged with one of:
- `CODE` — writing/modifying source files
- `CLI` — terminal commands (npm, git, etc.)
- `API` — HTTP requests, external service calls
- `CONFIG` — environment, settings, configuration changes
- `DESIGN` — architectural decisions, system design changes

### Chain of Thought (Required Before Every Action)

1. **UNDERSTAND** — What is the task? How does it fit the project?
2. **BASICS** — Dependencies, inputs, expected outputs
3. **BREAK DOWN** — Pre-action → Execution → Post-action
4. **ANALYZE** — Verify correctness, check for risks
5. **BUILD** — Write to session memory BEFORE execution
6. **EXECUTE** — Run it
7. **EDGE CASES** — Capture errors fully, prepare fix iteration
8. **FINAL ANSWER** — Log result, observations, next step

---

## Session Memory File Structure

The session memory file (`starburst-mcp2-session.md`) follows this structure:

```
# PROJECT MEMORY FILE
## PROJECT OVERVIEW (goal, description, tech stack)
## CURRENT STATE (completed, in progress, known issues)
## SESSION LOGS (timestamped entries with pre/post execution)
## KNOWN PATTERNS / DECISIONS
## SECURITY NOTES
## RECOVERY INSTRUCTIONS
```

### Entry Format (Every Action)

```
### [YYYY-MM-DD HH:MM]
#### ACTION TYPE: CODE / CLI / API / CONFIG / DESIGN
#### PURPOSE: (why this action is performed)
#### PRE-EXECUTION
<code or command>
#### EXECUTION RESULT
<output>
#### STATUS: SUCCESS / FAILURE
#### OBSERVATIONS: (what happened, insights)
#### NEXT STEP: (what will be done next)
```

---

## Strict Rules

- NEVER execute code before logging it to session memory
- NEVER omit errors — log full output including stack traces
- NEVER summarize instead of logging raw output (no "fixed bug" — log what was fixed and how)
- NEVER store unmasked API keys or secrets (mask like: `sk-****1234`)
- NEVER skip failed attempts — every iteration matters for recovery
- NEVER assume context without writing it down
- ALWAYS update CURRENT STATE section after completing a milestone
- ALWAYS update RECOVERY INSTRUCTIONS when the resume path changes

## Security

- Mask all API keys, tokens, and secrets in logs
- Never commit `.env` files or credentials
- Use environment variables for sensitive configuration

## Recovery Protocol

If starting a new session or resuming after interruption:
1. Read this CLAUDE.md file
2. Read the session memory file: `~/.claude/projects/c--Users-Lenovo/memory/starburst-mcp2-session.md`
3. Check CURRENT STATE section
4. Read the latest SESSION LOG entry
5. Execute the NEXT STEP from that entry
