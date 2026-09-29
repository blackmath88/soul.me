# Roadmap

## v0: Schema & template
- [x] `vault/` skeleton with the layout from [spec](docs/spec.md)
- [x] `minime.md` template (identity + operating manual) with a quality checklist
- [x] frontmatter spec ([docs/spec.md](docs/spec.md)) + a small validator script (`tools/validate.py`), run on push

## v1: Intake
- [x] standard "dump your memory of me" prompt ([prompts/memory-dump.md](prompts/memory-dump.md))
- [x] extraction prompt: raw material → four layers, tagged `[imported:*]` ([prompts/extract.md](prompts/extract.md))
- [x] sanitising prompt for company sources (runs inside the source tenant, D-014)
- [x] self-authored "how I work" prompt (preferred over company exports)
- [ ] interview agent to fill gaps in minime.md
- [ ] first real vault: my own, in a separate private repo ([docs/own-vault.md](docs/own-vault.md), D-015)

## v2: Drop-in exports (main way to serve the vault, D-013)
- [ ] script: minime.md → ChatGPT custom-instructions length
- [ ] script: bundle for Claude project files

## v3: Curation (offboarding-ready by default)
- [ ] weekly curation Action → one PR (dupes, expiry, contradictions, pruning)
- [ ] batch inbox review; proposals expire after 4 weeks (D-012)
- [ ] continuous sanitising of work-context lines, with a "what was stripped" section (D-014)

## v4: MCP server (optional layer, D-013)
- [ ] FTS5 index built from the vault
- [ ] tools: `get_core`, `search`, `read`, `list`, `get_skill`, `propose`, `handoff`
- [ ] per-client scope allowlist
- [ ] runs next to the local LLM setup

## Later
- vectors if FTS recall is poor · temporal graph · offboarding kit as a bridge-work.ai offer
