```yaml
---
name: Your Prompt Name
description: What this reusable prompt does.
# Optional: short hint shown in the UI
argument-hint: "Describe the input…"
# Optional: default agent to run this prompt with (ask|edit|agent|<custom-agent-id>)
agent: 'agent'
# Optional: tools or tool sets for this prompt
tools: ["search/codebase", "githubRepo", "web/fetch"]
# Optional: default model
model: "GPT-4.1"
---
```

Notes:
- VS Code loads prompt files from `.github/prompts/*.prompt.md`.
- Tools list priority: prompt frontmatter > agent frontmatter > user selection (see VS Code docs).
