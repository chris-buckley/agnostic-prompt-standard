```yaml
---
# Path-scoped rules frontmatter for Claude Code
# Rules with paths: only apply when working with files matching these globs

paths:
  - "src/**/*.ts"
  - "src/**/*.tsx"
---
```

Notes:
- Claude Code loads rules from `.claude/rules/*.md`.
- Rules without `paths:` frontmatter apply globally.
- Rules with `paths:` frontmatter only apply when working with files matching those glob patterns.
- Multiple glob patterns can be specified as an array.
- Globs use standard glob syntax (e.g., `**` for recursive matching, `*` for single directory).

Examples:

```yaml
---
# Apply only to TypeScript files
paths:
  - "**/*.ts"
  - "**/*.tsx"
---
```

```yaml
---
# Apply only to test files
paths:
  - "**/*.test.ts"
  - "**/*.spec.ts"
  - "tests/**/*"
---
```

```yaml
---
# Apply only to documentation
paths:
  - "docs/**/*.md"
  - "README.md"
---
```
