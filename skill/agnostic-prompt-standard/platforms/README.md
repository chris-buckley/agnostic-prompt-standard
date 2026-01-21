# Platforms

APS is designed to be **platform-agnostic**, but real hosts (IDEs, agent runtimes, CI bots) differ in:

- File discovery conventions (where prompts/agents/skills live)
- YAML frontmatter dialects (which fields exist, required/optional)
- Tool availability, naming, and approval UX
- Safety constraints (auto-approve settings, restricted file paths)

This folder contains **platform adapters** that describe those differences *without changing the APS v1.0 spec*.

## Adapter layout (recommended)

```
platforms/
  _schemas/                       # JSON Schemas for adapter files
  _template/                      # skeleton for new adapters
  <platform-id>/
    README.md
    manifest.json                 # validates against _schemas/platform-manifest.schema.json
    tools-registry.json           # validates against _schemas/tools-registry.schema.json
    frontmatter/                  # copy/paste blocks for this platform
```

## Add a new platform adapter

1. Copy `platforms/_template/` to `platforms/<platform-id>/`
2. Fill in:
   - `manifest.json` (file discovery rules + docs links)
   - `tools-registry.json` (available tools + naming + risk tags)
3. Do **not** change `references/` unless you are intentionally publishing an APS spec revision.

## Contract

- Anything under `references/` is **normative** APS.
- Anything under `platforms/` is **non-normative** (documentation/templates/mappings only).
- Adapters should prefer **mapping + configuration** over rewriting APS core rules.

## Scope and Philosophy

Adapters are intended to **map** the APS standard to a host platform. They are **not** project generators.
We do not provide generic project scaffolding (like `settings.json` or root `CLAUDE.md` templates).

> See [ADR 0001: Adapter Scope](https://github.com/chris-buckley/agnostic-prompt-standard/blob/main/docs/adr/0001-adapter-scope-no-scaffolding.md)

