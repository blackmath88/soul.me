# Architecture

The end-to-end view is in [vision.md](vision.md). This page covers the components.

## Core claim

**The vault is the product boundary.** Everything else (intake, curation, exports, MCP server)
reads from the vault or proposes changes to it. If every tool disappears, the vault is still readable.

```text
            INTAKE                         VAULT (git, private)                 SERVE
 ┌─────────────────────────┐       ┌──────────────────────────────┐   ┌──────────────────────┐
 │ self-written work notes │       │ minime.md          always    │   │ drop-in export (v2)   │
 │ vendor memory dumps     │─────► │ skills/*/SKILL.md  on demand │──►│  custom instructions, │
 │ interview agent         │ inbox/│ areas/ people/     searched  │   │  project files        │
 │ (work sources sanitised │       │ topics/                      │   ├──────────────────────┤
 │  before they cross)     │       │ sessions/          expires   │──►│ MCP server (v4)       │
 └─────────────────────────┘       │ inbox/             unreviewed│   │  read + propose only  │
                                   └──────────────┬───────────────┘   └──────────────────────┘
                                          ┌───────▼────────┐
                                          │ CURATE (weekly)│  inbox review · sanitise · dupes ·
                                          │  → one PR      │  expiry · contradictions · pruning
                                          └────────────────┘
```

## Vault and file format

The layout and file format are defined in [spec.md](spec.md) and checked by `tools/validate.py`. In short:
one subject per file, one fact per line, a provenance tag on every line, and a validity window on anything that can expire.
`data/` holds raw exports and is never committed.

## Components

| Component | Input | Output | Interface | Roadmap |
|---|---|---|---|---|
| validator | vault | `path:line` errors | `tools/validate.py` | v0 ✓ |
| intake prompts | vendor dumps, own notes, interview | `inbox/*.md` tagged `[imported:*]` / `[inferred]` | `prompts/` | v1 |
| sanitising prompt | work-context material | patterns only | `prompts/`, run *inside* the source tenant | v1 |
| drop-in export | `minime.md` (+ chosen areas) | paste-able text per target | script | v2 |
| curation | vault + `inbox/` | one PR | GitHub Action | v3 |
| MCP server | vault | tools below | MCP (stdio first) | v4 |

The drop-in export is the main way to serve the vault because it works in tenants that block MCP (D-013).

## MCP server (v4 tool surface)

| Tool | Does |
|---|---|
| `get_core()` | minime.md plus every `always`-scoped file |
| `search(query, scope?)` | SQLite FTS5 over the vault; matching lines + file |
| `read(path)` / `list(prefix?)` | one file / file index with descriptions |
| `get_skill(name)` | one procedure |
| `propose(path, lines, source)` | writes to `inbox/` only. **Never to live files.** |
| `handoff(note)` / `last_handoff()` | session layer |

The FTS5 index is rebuilt from the vault and can always be thrown away (D-005). Each client token carries a scope
allowlist, e.g. a work laptop gets no `people/`. The server runs locally first; a remote host is optional later.

## Curation pass (weekly)

One Action run opens one PR. That PR does the following:

- **inbox review:** batches all pending proposals for approval; proposals older than 4 weeks expire (D-012)
- **sanitising:** checks new work-context lines for client names, internal numbers or documents, and shows what it stripped (D-014)
- merges duplicates, moves facts past `valid_to` to an archive section, flags contradictions
- prunes sessions older than 14 days and checks `minime.md` against its budget

## Relation to Observstory

Observstory (D-008) will watch this repo's in-flight work; its workflow isn't added yet. It shares one principle with soul.me:
typed state first, projections second, and provenance is never mixed.

## Non-goals (v1)

No vector database, no knowledge graph, no multi-user support, no UI beyond GitHub itself. Prototype scale.
