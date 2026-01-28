# Agnostic Prompt Standard Principles

## I. Agent As Authority (Paradigm)

Data should be embodied in agents. The agent's instructions govern
access, the input contract demands context, and the output contract
provides meaning—not just values.

### Why

- Static data is a myth. Change is inevitable. Agents evolve in one place. Instead of changing documentation + an agent that reads it, change the agent's logic - the single source of truth.
- Files express shape. Agents express semantics.
- Files permit misuse. Agents enforce policy.
- Files answer "what." Agents answer "what, why, when, and how."

### Implication

There is no "just reading a value." Every interaction is a consultation
with an authority that knows its domain, demands appropriate context,
and returns meaning alongside data.

## II. Derive Once, Flow Downstream (Pattern)

Within a single workflow execution, consult an authority once at the
natural derivation point, then flow the result as data to all consumers.

This respects the paradigm (you consult the agent) while avoiding
redundant consultations within the same execution context.

The pattern (derive once, flow downstream) resembles **pure transformation**—context goes in, enriched context comes out, consumers receive what they need as explicit arguments.

When multiple agents need the same information, extend an existing context-gathering agent to derive that information once, then pass it as data through orchestration to all consumers.

### Anti-patterns

- **Duplication**: Each agent defines the same values independently.
- **Service Agent**: A dedicated agent exists solely to answer "what is X?" and gets called repeatedly.

### Pattern

```
┌─────────────────────────────┐
│ context-gathering agent     │  ← already runs early in workflow
│                             │
│ Derives: shared_value = ... │
└─────────────┬───────────────┘
              │
              ▼
        CONTEXT (enriched)
              │
     ┌────────┼────────┐
     ▼        ▼        ▼
  agent-A  agent-B  agent-C
  (reads   (reads   (reads
   input)   input)   input)
```

### Example

**Scenario**: Three agents need to know which date format the organization uses (`ISO-8601` vs `US-locale`).

**Solution**: The agent that already analyzes project configuration detects the date format preference and emits it in its output. The coordinator passes that output to downstream agents. Each consumer reads the format from its input rather than rediscovering or hardcoding it.

One derivation. Many consumers. No repeated queries.