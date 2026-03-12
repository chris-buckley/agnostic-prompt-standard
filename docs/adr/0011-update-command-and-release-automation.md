# ADR-011: Update Command and Release Automation

**Date:** 2026-03-12
**Status:** Accepted
**Deciders:** @chris-buckley
**PR/Issue:** N/A

## Context

APS now ships on two package registries:
- npm (`@agnostic-prompt/aps`)
- PyPI (`agnostic-prompt-aps`)

Users can install APS in multiple scopes and locations:
- repo-scoped skills (`.github/skills`, `.claude/skills`)
- personal skills (`~/.copilot/skills`, `~/.claude/skills`)

This created two related problems:
1. **User update friction** — users needed a consistent way to check whether a newer APS CLI release exists and then refresh installed skill directories from the latest bundled payload.
2. **Release drift** — APS changes could land without a version bump, which prevented new npm/PyPI releases from being cut and left `aps update` with nothing new to install.

The repository also had a concrete consistency gap: `packages/aps-cli-node/package-lock.json` could drift away from the canonical APS version.

## Quick Reference

1. [Expose an `update` command in both CLIs](#1-expose-an-update-command-in-both-clis) — Node and Python ship the same update behavior.
2. [Refresh the running CLI before refreshing skills](#2-refresh-the-running-cli-before-refreshing-skills) — If a newer registry release exists, the CLI attempts self-update first.
3. [Automate missed version bumps on `main`](#3-automate-missed-version-bumps-on-main) — A workflow creates a follow-up version bump commit when releasable files change.
4. [Publish from version tags with trusted publishing](#4-publish-from-version-tags-with-trusted-publishing) — Tag-driven npm/PyPI release workflow.

## Consequences

### Positive
- Users get one command (`aps update`) across both ecosystems
- Installed skill directories refresh from the same bundled APS payload logic in both CLIs
- Release-relevant changes no longer depend on humans remembering a manual version bump
- npm, package-lock, Python package metadata, and SKILL.md remain aligned
- Tag-driven publishing creates a predictable release boundary for update checks

### Negative
- The update command adds runtime network checks against npm/PyPI
- Auto-bump introduces a follow-up commit on `main`, which slightly changes branch history
- Release automation now depends on repository-level trusted publishing configuration in npm and PyPI

### Neutral
- `aps update` refreshes installed APS skill directories; it does not attempt to migrate user customizations inside those installed directories
- Repo-local payload syncing remains part of the release/build path

## Decisions

### 1. Expose an `update` command in both CLIs

**Decision:** Both the Node and Python CLIs expose `aps update` with matching flags and reporting style.

**Behavior:**
- `aps update` checks the latest published CLI version from npm/PyPI
- `aps update --check` reports only
- `aps update --dry-run` shows the planned refresh without writing
- `aps update --repo` and `aps update --personal` scope the refresh targets
- `aps update --force` refreshes installed APS skill directories even when versions already match
- the command reports the current CLI version, bundled skill version, latest registry version, runtime mode, and each target installation result

**Rationale:** The repo already enforced command parity between the two CLIs. Update behavior belongs in the CLI layer rather than as an imagined `npx update` or `pipx update` package-manager subcommand.

---

### 2. Refresh the running CLI before refreshing skills

**Decision:** When a newer registry release exists, `aps update` attempts to refresh the running CLI package first, then re-runs the update command with the new payload.

**Behavior:**
- npx/ephemeral execution re-runs with the latest package version
- pipx/installed execution attempts `pipx upgrade --install`
- global npm execution attempts a global reinstall
- local project installs are classified separately so the CLI can choose the least surprising refresh path
- an internal guard environment variable prevents recursive update loops

**Rationale:** If the running CLI is older than the newest published APS release, refreshing installed skills first would still use the old bundled payload. Self-update-first makes the user-visible result match the latest registry release.

---

### 3. Automate missed version bumps on `main`

**Decision:** The repository includes `tools/auto_bump_version.py` and an `auto-bump-version.yml` workflow to create a version bump commit when releasable files changed but the canonical APS version did not.

**Behavior:**
- the script compares the current canonical version with the latest semver tag
- if the current version already exceeds the latest tag, no action is taken
- if the current version matches the latest tag and releasable files changed under `skill/`, `packages/`, or `tools/`, the script bumps the version (default: patch)
- the workflow runs on pushes to `main`, commits the bump, and syncs payloads before pushing the follow-up commit
- `bump_version.py` and `check_versions.py` now also include `packages/aps-cli-node/package-lock.json`

**Rationale:** Release automation should not depend on perfect human discipline. The repository needs a deterministic fallback that keeps package publishing unblocked.

---

### 4. Publish from version tags with trusted publishing

**Decision:** npm and PyPI publication runs from semver tags (`vX.Y.Z`) through a dedicated GitHub Actions workflow.

**Behavior:**
- the publish workflow validates `SKILL.md`, package metadata, Python metadata, and Node `package-lock.json` against the tag
- the workflow syncs CLI payloads before building
- Node publishes to npm from the tagged source
- Python builds and publishes distributions to PyPI from the tagged source
- the workflow is designed for repository-level trusted publishing / OIDC configuration

**Rationale:** `aps update` can only deliver the newest APS skill if a new package release exists. Tag-driven trusted publishing makes that release boundary explicit and removes manual registry publishing from the normal path.
