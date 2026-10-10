# Architecture

The end-to-end view is in [vision.md](vision.md); the visual version is [brand/brand-kit.html](../brand/brand-kit.html).
This page covers the system: what exists today and what is planned.

## Core claim

**The vault is the product boundary.** Everything else (intake, curation, exports, MCP server)
reads from the vault or proposes changes to it. If every tool disappears, the vault is still readable.

## As built today (v0 + v1)

There is no running service. The system is **two git repos, a monthly export, and scripts you run on your own machine
against your own model.** The person's manual work is requesting exports (monthly) and sealing a short list (weekly).

```text
 SOURCES: places × providers                  TOOL: soul.me (public)          VAULT: soul-vault (private, D-015)
 ┌────────────────────────────────────┐       ┌──────────────────────┐        ┌──────────────────────────────┐
 │ work   │ Copilot, ChatGPT Ent. …   │       │ prompts/             │ copied │ vault/data/   raw, gitignored │
 │        │  sanitise.md runs INSIDE ─┼─┐     │  how-i-work, dump,   │ by hand│ vault/inbox/  [imported:*]    │
 │        │  the tenant (D-014)       │ │     │  sanitise, extract   │───────►│               [inferred]      │
 │ home   │ ChatGPT, Claude, local    │ ├────►│ docs/spec.md         │        │   ↓ you review, seal          │
 │ self   │ your own "how I work" note│ │ you │ tools/validate.py    │ pinned │ live files    [stated]        │
 └────────────────────────────────────┘ │     │ vault/ (fictional,   │ tag    │ .github/…/validate.yml ──────►│
                                        └─────┤  CI fixture)         │───────►│   runs soul.me's validator    │
                                  paste in,   └──────────────────────┘        └──────────────────────────────┘
                                  paste out
```

| Component | Lives in | Status | How it runs |
|---|---|---|---|
| spec | soul.me `docs/spec.md` | built (v0) | read by people and prompts |
| validator | soul.me `tools/validate.py` | built (v0) | `python tools/validate.py <vault> [--summary]`; PyYAML only |
| CI, tool repo | soul.me `.github/workflows/validate.yml` | built | on push, against the fictional `vault/` |
| fictional vault | soul.me `vault/` | built | example and CI fixture; never real data |
| intake prompts | soul.me `prompts/` | built (v1) | copied by hand into assistants (manual path) |
| automated intake | soul.me `tools/extract.py` + `prompts/lenses.md`, `intake-*.md` | built (v1) | on your machine, against your own model via any OpenAI-compatible endpoint; see below |
| intake evaluation | soul.me `tools/eval_extract.py` + `tests/fixtures/` | built | scores a model on fictional exports; CI runs it against a stub model |
| vault repo + its CI | `soul-vault` (per person) | documented in [own-vault.md](own-vault.md) | Action checks out soul.me at a pinned tag and validates. **Tag `v0.1` is not published yet**, so that Action can't run until it is. |
| brand kit | soul.me `brand/` | built | static HTML (D-019) |
| drop-in export | soul.me `tools/export.py` | built (v2) | `--profile work` or `personal`, `--target system`, `chatgpt` or `claude`; tested in CI |
| curation | soul.me `tools/curate.py` + `templates/vault-curate.yml` | built (v3, partly) | weekly Action in the vault repo opens one PR: expiry, archive, pruning; duplicates and budget report-only. `tools/conflicts.py` flags contradictions locally with your own model |
| MCP server | soul.me `tools/mcp_server.py` | built (v4, first cut) | stdio, one process per client and profile; see below |
| bulk imports | soul.me `tools/chatgpt_export.py`, `chatgpt_corrections.py`, `classify_corrections.py`, `release.py` | built (v1) | converter → corrections and per-cluster intake, staged in `data/staged/`, released one batch at a time (D-027) |
| interview | soul.me `tools/interview.py` + `prompts/interview.md` | built (v1) | your model picks questions from open gaps; only your answers are saved, to `data/`, then intake as `self` |
| Observstory workflow | – | not built | |

## Sources have two axes

Material comes from **places** (work, home, your own head) through **providers** (Copilot, ChatGPT, Claude, a local model).
The place decides the rules; the provider only decides the format.

- **Source slugs** carry both: `[imported:<provider>-<place>]`, e.g. `chatgpt-home`, `copilot-work`, or `self` for your own note (D-020).
- **Work** material is sanitised inside the tenant before it crosses (D-014). Everything else goes straight to `inbox/`.
- **Origin after sealing** stays in git: the commit that promotes lines names the inbox file it came from,
  so "every stated line that came from work" is a `git log` query, not extra syntax in the file (D-021).

## Automated intake (as built)

```text
 export ZIPs / notes ─► 1 parse   only your own messages, only since the last run (timestamps in data/.intake-state.json)
 (vault/data/)          2 redact  IDs, IBAN, cards, emails, phones, data/denylist.txt  — code, before any model (D-024)
                        3 map     each chunk × each lens (prompts/lenses.md) → JSON findings with quotes (D-025)
                        4 verify  quote must appear word for word in your message, else dropped
                        5 merge   same fact across chunks/lenses → one finding, with recurrence across conversations
                        6 known   already in the vault or waiting in inbox/ → dropped
                        7 judge   second pass: keep? confidence · stability · sensitive · target · contradicts
                        8 gaps    up to 3 open questions → next run's prompts and the inbox frontmatter (D-026)
                        9 write   inbox/<date>-<source>.md (top 12, ranked, with quotes) + data/reports/*.json
```

The prompts are markdown in `prompts/`, so lenses and wording change without code. Nothing writes to live files:
the person seals a short ranked list (review option A, D-006 unchanged). Conversation titles are never stored: vendors
write them from the content, and the evaluation caught one leaking a health detail.

## Vault and file format

Defined in [spec.md](spec.md) and checked by `tools/validate.py`: one subject per file, one fact per line,
a provenance tag on every line, a validity window on anything that can expire. `data/` is never committed.

## Planned: serving the vault

Places are destinations too. Whatever serves the vault takes a **profile** that decides which folders leave it (D-022):

| Profile | Includes | Typical target |
|---|---|---|
| `work` | `minime.md`, `skills/`, work `areas/` | an employer tenant: never `people/`, private `topics/` or `sessions/` |
| `personal` | everything live | your own accounts, local models |

| Component | Input | Output | Roadmap |
|---|---|---|---|
| drop-in export | vault + profile | paste-able text per target (custom instructions, project files) | v2, the main serving path (D-013) |
| curation | vault + `inbox/` | one weekly PR | v3 |
| MCP server | vault + per-client profile | the tools below | v4, optional |

### MCP server (v4, `tools/mcp_server.py`)

| Tool | Does |
|---|---|
| `get_core()` | minime.md plus every `always`-scoped file |
| `search(query, scope?)` | SQLite FTS5 over the vault; matching lines + file |
| `read(path)` / `list(prefix?)` | one file / file index with descriptions |
| `get_skill(name)` | one procedure |
| `propose(path, lines, told?)` | writes to `inbox/<date>-mcp-<client>.md` only, `[inferred]` or `[imported:<client>]` (D-030). **Never to live files.** |
| `last_handoff()` | latest session note, personal profile only. `handoff(note)` is not built (D-030) |

The FTS5 index is rebuilt from the vault and can always be thrown away (D-005). It runs locally first.

### Curation pass (weekly, v3)

One Action run opens one PR that batches inbox review (proposals expire after 4 weeks, D-012), sanitises new work-context lines
and shows what it stripped (D-014), merges duplicates, archives facts past `valid_to` (D-017), flags contradictions,
prunes sessions older than 14 days and checks `minime.md` against its budget.

## Status numbers

`validate.py --summary` prints the counts that any status display needs (stated lines, inbox lines, expired inbox
files, expired sessions). The brand's favicon seal, tails and incense are drawn from these numbers, never decoratively.

## Non-goals (v1)

No running service, no vector database, no knowledge graph, no multi-user support, no UI beyond GitHub itself. Prototype scale.
