# Roadmap

## v0: Schema & template
- [x] `vault/` skeleton with the layout from [spec](docs/spec.md)
- [x] `minime.md` template (identity + operating manual) with a quality checklist
- [x] frontmatter spec ([docs/spec.md](docs/spec.md)) + a small validator script (`tools/validate.py`), run on push
- [x] `validate.py --summary`: status counts for badges and the brand's live states

## v1: Intake
- [x] standard "dump your memory of me" prompt ([prompts/memory-dump.md](prompts/memory-dump.md))
- [x] extraction prompt: raw material → four layers, tagged `[imported:*]` ([prompts/extract.md](prompts/extract.md))
- [x] sanitising prompt for company sources (runs inside the source tenant, D-014)
- [x] self-authored "how I work" prompt (preferred over company exports)
- [x] automated intake: `tools/extract.py` (parse exports, redact, lenses, verify quotes, judge, ranked inbox)
- [x] `tools/eval_extract.py`: score your model on fictional exports before real data
- [x] ChatGPT export converter + corrections pass ([docs/chatgpt-import.md](docs/chatgpt-import.md))
- [ ] classify corrections on real export
- [ ] per-cluster extraction
- [ ] interview agent to fill gaps in minime.md (partly: gap questions per run)
- [ ] publish soul.me tag `v0.1` (the vault repo's Action pins to it)
- [ ] first real vault: my own, in a separate private repo ([docs/own-vault.md](docs/own-vault.md), D-015)

## v2: Drop-in exports (main way to serve the vault, D-013)
- [ ] export profiles `work` / `personal` (D-022)
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

## Optional ecosystem evaluations (2026-10-06; proposed)

Details and acceptance checks: [ecosystem fit](docs/ecosystem-fit-2026-10.md). These do not replace the v1–v4 order or change settled decisions.

- [ ] v2: measure export size and preserve provenance/validity/hard rules under destination profiles; optional context compression must not erase required facts.
- [ ] v1 evaluation only: compare Strands Decider with current classification on fictional, redacted, quote-verified findings; shadow output suggests a layer, never seals or filters live facts.
- [ ] v4 evaluation only: compare native FTS5 with a read-only agent-memory recall view; profile filtering precedes ranking and whole-file reads; disable lifecycle writes and retain direct-file fallback.
- [ ] Later, only if review usability warrants it: borrow OpenDots' exact-draft review card pattern using the existing brand and Git vault; assess conversation-service dependency before any stack adoption.

Defer vectors/graphs, autonomous memory management, automatic learning and new agent workspaces until measured need justifies a separate proposal.
