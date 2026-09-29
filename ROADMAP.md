# Roadmap

## v0: Schema & template
- [x] `vault/` skeleton with the layout from [architecture](docs/architecture.md)
- [x] `minime.md` template (identity + operating manual) with a quality checklist
- [x] frontmatter spec ([docs/spec.md](docs/spec.md)) + a small validator script (`tools/validate.py`)

## v1: Intake
- [ ] standard "dump your memory of me" prompt for ChatGPT / Claude / Copilot
- [ ] extraction prompt: raw material → four layers, tagged `[imported:*]`
- [ ] sanitising prompt for company sources
- [ ] interview agent to fill gaps in minime.md
- [ ] first real vault: my own

## v2: Drop-in exports
- [ ] script: minime.md → ChatGPT custom-instructions length
- [ ] script: bundle for Claude project files

## v3: MCP server
- [ ] FTS5 index built from the vault
- [ ] tools: `get_core`, `search`, `read`, `list`, `get_skill`, `propose`, `handoff`
- [ ] per-client scope allowlist
- [ ] runs next to the local LLM setup

## v4: Curation
- [ ] weekly curation Action → PR (dupes, expiry, contradictions, pruning)

## Later
- vectors if FTS recall is poor · temporal graph · offboarding kit as a bridge-work.ai offer
