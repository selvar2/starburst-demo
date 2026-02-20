---
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
description: Generate a production-ready system prompt from a description. Accepts a free-form description with optional --tone, --format, --domain flags.
---

You are executing the **System Prompt Generator** command. Your job is to take the user's description and produce a complete, production-ready system prompt.

## Input Parsing

The user provides their request as the command argument. Parse it for:

1. **Description** (required): The free-form description of what the AI should do
2. **--tone** (optional): Desired tone (formal, casual, technical, friendly, authoritative)
3. **--format** (optional): Output structure preference (minimal, standard, comprehensive)
4. **--domain** (optional): Specific domain (engineering, writing, support, education, security, data, etc.)

### Defaults
- **tone**: professional and authoritative
- **format**: comprehensive (all sections included)
- **domain**: inferred from the description

## Execution Flow

### Phase 1: Analyze the Request

Read the user's description and extract:
- What role should the AI play?
- What is the primary task?
- Who is the target audience?
- What constraints are implied?
- What output format would be ideal?

### Phase 2: Generate the System Prompt

Build a complete system prompt with these mandatory sections:

#### ROLE
Define a clear, authoritative identity. Be specific about expertise level and domain.
- Good: "You are a senior backend engineer specializing in distributed systems with 15 years of experience in Go and Kubernetes."
- Bad: "You are a helpful coding assistant."

#### CONTEXT
Provide background that grounds the AI in its operating environment.
- What domain knowledge should it assume?
- What is the operating context?
- What does the user typically need?

#### OBJECTIVE
State the primary mission in one clear sentence.

#### INSTRUCTIONS
Numbered, actionable steps the AI follows for every interaction:
1. First action (analyze/understand)
2. Second action (evaluate/plan)
3. Third action (execute/synthesize)
4. Fourth action (deliver/validate)

#### CONSTRAINTS
Hard rules using NEVER/ALWAYS/REFUSE language:
- At least 3 negative constraints (what NOT to do)
- At least 2 positive constraints (what to ALWAYS do)
- Boundary definitions (when to refuse or escalate)

#### OUTPUT FORMAT
Explicit structure specification:
- Response format (markdown, JSON, plain text, etc.)
- Section organization
- Length guidelines
- Formatting requirements

#### EXAMPLES (when --format is "comprehensive" or unset)
Include 2 concrete input/output pairs showing ideal behavior.

### Phase 3: Deliver

Present the system prompt inside a clearly marked block:

```
========================================
GENERATED SYSTEM PROMPT
========================================
Domain: [detected/specified domain]
Tone: [applied tone]
Format: [applied format level]
Estimated Tokens: [approximate count]
========================================

[THE COMPLETE SYSTEM PROMPT]

========================================
END OF SYSTEM PROMPT
========================================

USAGE NOTES:
- Copy everything between the markers above
- Paste into your AI platform's system prompt field
- Customize the [bracketed placeholders] if any remain
- Test with 3-5 sample interactions before deploying
```

## Format Levels

### --format minimal
Include only: ROLE + INSTRUCTIONS + CONSTRAINTS
Best for: Small models, simple tasks, quick prototyping

### --format standard
Include: ROLE + CONTEXT + OBJECTIVE + INSTRUCTIONS + CONSTRAINTS + OUTPUT FORMAT
Best for: Most use cases, mid-size models

### --format comprehensive (default)
Include: All sections including EXAMPLES
Best for: Production deployment, large models, complex tasks

## Tone Modulation

| Tone | Characteristics |
|------|----------------|
| formal | Third-person references, precise language, academic structure |
| casual | Direct address, conversational phrasing, relaxed structure |
| technical | Jargon-heavy, specification-oriented, precise definitions |
| friendly | Warm language, encouraging tone, approachable structure |
| authoritative | Commanding language, expert assertions, definitive statements |

## Quality Checklist

Before delivering, verify internally:
- [ ] Role is specific (not generic)
- [ ] Instructions are numbered and actionable
- [ ] At least 3 constraints define boundaries
- [ ] Output format is explicitly defined
- [ ] No vague language ("try to", "maybe", "somewhat")
- [ ] Domain terminology is accurate
- [ ] Tone is consistent throughout
- [ ] Prompt is self-contained (no external dependencies)

## Error Handling

If the description is too vague (fewer than 5 words with no clear intent):
- Ask ONE clarifying question: "What specific task should this AI perform?"
- Do NOT generate a generic prompt from insufficient input

If conflicting flags are provided:
- Prioritize explicit flags over inferred values
- Note the conflict in the usage notes
