# Architecture

## Core claim

**The vault is the product boundary.** Everything else (intake, MCP server, curation, exports)
reads from or proposes changes to a git repo of markdown. If every tool disappears, the vault is still readable.

```text
            INTAKE                         VAULT (git, private)                 SERVE
 ┌─────────────────────────┐       ┌──────────────────────────────┐   ┌──────────────────────┐
 │ interview agent         │       │ minime.md          always    │   │ static drop-in        │
 │ vendor memory dumps     │─────► │ skills/*.md        on demand │──►│  (custom instructions,│
 │ chat exports (JSON)     │ PR /  │ areas/ people/     searched  │   │   project files)      │
 │ own writing (data/)     │ review│ topics/                      │   ├──────────────────────┤
 └─────────────────────────┘       │ sessions/          expires   │──►│ soul.me MCP server    │
                                   │ inbox/             unreviewed│   │  → Claude, ChatGPT,   │
                                   └──────────────┬───────────────┘   │    local Qwen, Cursor │
                                                  │                   └──────────────────────┘
                                          ┌───────▼────────┐
                                          │ CURATE (cron)  │  merge dupes · date facts ·
                                          │ "sleep-time"   │  flag contradictions · prune sessions
                                          └────────────────┘  → opens a PR, never writes to main
```

## Vault layout

```text
vault/
  minime.md                 core: identity + operating manual (≤ ~1,500 words)
  skills/<name>/SKILL.md    procedures
  areas/<name>.md           ongoing involvements
  people/<name>.md          relationship context only
  topics/<domain>.md        facts by domain
  sessions/<date>-<slug>.md handoffs, auto-pruned after 14 days
  inbox/                    imported / inferred lines awaiting review
  data/                     raw source material (exports), gitignored or encrypted
```

## File format

```markdown
---
name: bridge-work
description: my AI adoption consultancy; read before work on its site, tools or offers
scope: global            # always | global | project | session
aliases: [bridge-work.ai]
updated: 2026-09-29
---
- [stated] Runs bridge-work.ai, AI adoption & governance consultancy
- [stated] (valid_to: 2026-12) Leads the Copilot pilot
- [inferred] Prefers short loops over big plans   ← stays in inbox/ until confirmed
```

Rules: one subject per file · one fact per line · a provenance tag on every line · dates for anything that can expire.

## MCP server (v1 tool surface)

| Tool | Does |
|---|---|
| `get_core()` | returns minime.md plus every `always`-scoped file |
| `search(query, scope?)` | full-text search (SQLite FTS5) over the vault; returns matching lines + file |
| `read(path)` | one file |
| `list(prefix?)` | file index with descriptions |
| `get_skill(name)` | one procedure |
| `propose(path, lines, source)` | writes to `inbox/` or opens a PR. **Never writes to live files directly.** |
| `handoff(note)` / `last_handoff()` | session layer |

- Index: a SQLite FTS5 index rebuilt from the vault on every commit. Vectors only if recall turns out poor.
- Access: per-client tokens with a scope allowlist (e.g. a work laptop gets no `people/`).
- Hosting: local first (fits morrow-local-llm); remote (Cloudflare Worker) optional later.

## Intake pipeline

1. **Collect.** Vendor memory dumps (ChatGPT, Claude, Copilot) via a standard prompt; chat exports; own writing.
2. **Extract.** An LLM sorts material into the four layers and tags every line `[imported:<source>]`.
3. **Sanitise.** For company sources, a filter strips client/internal content; only patterns remain.
4. **Interview.** An agent fills the gaps in minime.md by asking questions.
5. **Review.** A human confirms each line. Confirmed lines become `[stated]`, and a PR is merged.

## Curation pass ("sleep-time")

Runs weekly as a GitHub Action or local cron. It opens a PR with:

- duplicates merged
- facts past `valid_to` moved to an archive section
- contradictions flagged (e.g. two different roles, both current)
- sessions older than 14 days pruned
- minime.md checked against its size budget

## Drop-in modes (no server needed)

| Target | How |
|---|---|
| ChatGPT custom instructions | `minime.md` condensed to the character limit (export script) |
| Claude project / memory import | minime.md + relevant areas as project files |
| Local LLM | system prompt = minime.md; MCP for the rest |

## Relation to Observstory

Observstory watches this repo's in-flight work (see `.github/workflows/observstory.yml`).
The design principle is shared: typed state first, projections second, and provenance is never mixed.

## Non-goals (v1)

No vector database, no knowledge graph, no multi-user support, no UI beyond GitHub itself. Prototype scale.
