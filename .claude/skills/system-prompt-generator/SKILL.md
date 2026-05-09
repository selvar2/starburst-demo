---
name: system-prompt-generator
description: "Interactive system prompt builder with progressive disclosure. Guides you through structured questions to define the AI's role, task, constraints, output format, and examples, then generates a production-ready system prompt. Use when you want guided, step-by-step prompt creation instead of a one-shot command."
user_invocable: true
---

# Interactive System Prompt Generator

You are running the **Interactive System Prompt Generator**. Guide the user through a structured conversation to build a high-quality system prompt, then generate the final output.

## Progressive Disclosure Flow

Walk the user through these phases. Use AskUserQuestion at each phase to gather structured input. Do NOT skip phases or ask all questions at once.

---

### Phase 1: Role Definition

Ask the user to define the AI's identity.

**Question:** "What role should the AI play?"

**Options to present:**
- **Software Engineer** - Code generation, review, debugging, architecture
- **Data Analyst** - Data analysis, visualization, statistical reasoning
- **Content Writer** - Articles, documentation, marketing copy, creative writing
- **Customer Support** - Help desk, troubleshooting, product guidance

Let the user pick or provide a custom role via "Other".

**Follow-up:** "What expertise level? (Junior, Mid-level, Senior, Principal/Expert)"

Capture: `role` and `expertise_level`

---

### Phase 2: Task Scope

Ask the user to define what the AI should accomplish.

**Question:** "What is the primary task this AI should perform?"

Let the user describe in their own words. Then confirm by restating it back.

**Follow-up question:** "What is the target audience for this AI?"

**Options:**
- **Developers** - Technical users building software
- **Business Users** - Non-technical stakeholders
- **Students** - Learners at various levels
- **General Public** - Broad, mixed-skill audience

Capture: `primary_task`, `audience`

---

### Phase 3: Constraints & Boundaries

Ask the user to define rules and limitations.

**Question:** "What should this AI NEVER do? (Select all that apply)"

**Options (multi-select):**
- **Never make up information** - Admit uncertainty instead of guessing
- **Never execute harmful requests** - Refuse dangerous or unethical tasks
- **Never break character** - Stay in the defined role at all times
- **Never provide overly long responses** - Keep answers concise and focused

Let the user add custom constraints via "Other".

**Follow-up:** "What should this AI ALWAYS do?"

**Options (multi-select):**
- **Always cite sources** - Reference documentation or data
- **Always explain reasoning** - Show chain of thought
- **Always ask for clarification** - When the request is ambiguous
- **Always provide examples** - Include concrete illustrations

Capture: `never_rules[]`, `always_rules[]`

---

### Phase 4: Output Format

Ask the user how the AI should structure its responses.

**Question:** "How should the AI format its responses?"

**Options:**
- **Structured Markdown** - Headers, lists, code blocks, tables
- **Plain Text** - Simple paragraphs, no formatting
- **JSON/Structured Data** - Machine-readable output format
- **Conversational** - Natural dialogue style

**Follow-up:** "Any specific length preference?"

**Options:**
- **Concise** - 1-3 paragraphs, bullet points preferred
- **Moderate** - 3-6 paragraphs, balanced detail
- **Detailed** - Comprehensive coverage, thorough explanations
- **Adaptive** - Match response length to question complexity

Capture: `output_format`, `response_length`

---

### Phase 5: Tone & Style

**Question:** "What tone should the AI use?"

**Options:**
- **Professional** - Formal, business-appropriate language
- **Technical** - Precise, jargon-heavy, specification-oriented
- **Friendly** - Warm, approachable, encouraging
- **Authoritative** - Expert, definitive, commanding

Capture: `tone`

---

### Phase 6: Examples (Optional but Recommended)

**Question:** "Would you like to provide example interactions to guide the AI's behavior?"

**Options:**
- **Yes, I'll provide examples** - User provides 1-2 sample exchanges
- **Generate examples for me** - Auto-generate based on collected context
- **Skip examples** - No examples (not recommended for production)

If "Yes": Ask the user for a sample user input and the ideal AI response. Collect 1-2 examples.

If "Generate": Create 2 realistic examples based on the role, task, and constraints.

Capture: `examples[]`

---

### Phase 7: Advanced Options

**Question:** "Any advanced configuration? (Select all that apply)"

**Options (multi-select):**
- **Chain-of-thought reasoning** - AI shows its thinking process before answering
- **Self-correction protocol** - AI reviews and corrects its own output
- **Escalation rules** - Define when the AI should refuse or hand off
- **None** - Keep it standard

Capture: `advanced_options[]`

---

## Generation Phase

After collecting all inputs, assemble the system prompt with all mandatory sections: ROLE, CONTEXT, OBJECTIVE, INSTRUCTIONS, CONSTRAINTS, OUTPUT FORMAT, and EXAMPLES.

## Delivery

Present the generated prompt with:

1. **Preview**: Show the complete system prompt in a code block
2. **Summary**: List all captured parameters
3. **Refinement offer**: "Would you like to modify any section?"

## Quality Standards

Every generated prompt must pass:
- [ ] Specific role (not "helpful assistant")
- [ ] Actionable numbered instructions
- [ ] At least 3 negative constraints
- [ ] At least 2 positive constraints
- [ ] Explicit output format
- [ ] Consistent tone throughout
- [ ] Domain-appropriate terminology
- [ ] Self-contained (no external dependencies)

## Refinement Loop

After presenting the generated prompt, always offer:

**"Would you like to refine this prompt?"**

Options:
- **Looks good** - Finalize and deliver
- **Modify a section** - Edit specific parts
- **Start over** - Reset and begin fresh
- **Make it shorter** - Condense to essential sections only
