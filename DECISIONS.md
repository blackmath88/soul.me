# Decisions

## D-001: Name: soul.me (2026-09-29)
**Decision:** The project is called **soul.me**. The always-loaded core file is `minime.md`.
**Why:** SOUL.md is the common name for *agent* persona files. soul.me echoes it while saying the subject is a human.
`.me` is not a file extension, so the files themselves stay `.md`.

## D-002: Storage is markdown in git (2026-09-29)
**Decision:** The vault is plain markdown in a private git repo, compatible with Obsidian.
**Why:** Human-readable, vendor-neutral, versioned. Migration is a clone. Adopted from vault-mcp.

## D-003: Four layers + scopes (2026-09-29)
**Decision:** Core (always) · Procedures (on demand) · Episodic (searched) · Session (expires).
**Why:** Only the episodic layer needs retrieval; the rest is loaded directly. From openport + Letta.

## D-004: Provenance on every line (2026-09-29)
**Decision:** Tags `[stated]`, `[inferred]`, `[imported:<source>]`. Only `[stated]` is served as fact.
**Why:** Model guesses must never pass as the person's own statements. Mirrors Observstory's observed/derived/declared split.

## D-005: Full-text search before vectors (2026-09-29)
**Decision:** v1 search uses SQLite FTS5.
**Why:** Simpler and local, and ai-memory-mcp reports strong recall without embeddings. Add vectors only if recall is measurably poor.

## D-006: Writes go through review (2026-09-29)
**Decision:** Neither the MCP server nor the curation pass writes to live files; both propose into `inbox/` or a PR.
**Why:** Curation is the product. A human stays the author of their own self.

## D-007: Offboarding means patterns travel, content stays (2026-09-29)
**Decision:** Extraction from employer accounts runs a sanitising pass; only working style, procedures and competence leave.
**Why:** Legally and ethically clean, and it's the positioning gap in the governance debate.

## D-008: Observstory watches this repo (2026-09-29)
**Decision:** The Observstory GitHub Action runs with zero config.
**Why:** Dogfooding. It becomes meaningful once the MCP server is being built in parallel.

## D-009: Unreviewed tags live only in inbox/ (2026-09-29), **Proposed**
**Decision:** `[inferred]` and `[imported:*]` lines are allowed only in `inbox/`. Live files hold `[stated]` only, and the validator fails otherwise.
**Why:** It makes D-004 and D-006 mechanical: nothing unconfirmed can sit where it would be served as fact.

## D-010: Skill steps carry tags too (2026-09-29), **Proposed**
**Decision:** Every step in a `SKILL.md` gets a provenance tag, like any other line. There's no file-level provenance.
**Why:** It keeps D-004 without exceptions. It costs a little noise, but an imported procedure gets reviewed step by step.

## D-011: Strict body format (2026-09-29), **Proposed**
**Decision:** A vault file body contains only headings and tagged list items; `name` equals the file (or skill folder) name.
**Why:** One fact per line becomes checkable, and the future FTS index can return a line with its tag and file without parsing prose.
