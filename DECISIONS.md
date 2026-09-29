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
*Amended by D-014: sanitising runs weekly, not at exit.*

## D-008: Observstory watches this repo (2026-09-29)
**Decision:** The Observstory GitHub Action runs with zero config.
**Why:** Dogfooding. It becomes meaningful once the MCP server is being built in parallel.

## D-009: Unreviewed tags live only in inbox/ (2026-09-29)
**Decision:** `[inferred]` and `[imported:*]` lines are allowed only in `inbox/`. Live files hold `[stated]` only, and the validator fails otherwise.
**Why:** It makes D-004 and D-006 mechanical: nothing unconfirmed can sit where it would be served as fact.

## D-010: Skill steps carry tags too (2026-09-29)
**Decision:** Every step in a `SKILL.md` gets a provenance tag, like any other line. There's no file-level provenance.
**Why:** It keeps D-004 without exceptions. It costs a little noise, but an imported procedure gets reviewed step by step.

## D-011: Strict body format (2026-09-29)
**Decision:** A vault file body contains only headings and tagged list items; `name` equals the file (or skill folder) name.
**Why:** One fact per line becomes checkable, and the future FTS index can return a line with its tag and file without parsing prose.

## D-012: Inbox is reviewed weekly and expires (2026-09-29)
**Decision:** Pending `inbox/` proposals are reviewed as one batch in the weekly curation PR. Proposals unreviewed after 4 weeks expire and are deleted.
**Why:** Without a rhythm and an expiry, the inbox grows into a second, unreviewed memory, which is exactly what D-004 and D-006 prevent.

## D-013: Drop-in export before MCP (2026-09-29)
**Decision:** The paste-able drop-in export is the main way to serve the vault and ships first; the MCP server is an optional later layer.
**Why:** Employer tenants often block MCP connectors, but every assistant accepts custom instructions or project files. The offboarding story has to work without a server.

## D-014: Offboarding-ready by default (2026-09-29), amends D-007
**Decision:** Sanitising runs continuously: work-context material is sanitised before it enters `inbox/`, and every weekly curation PR shows what was stripped. There is no exit-time extraction step. Self-authored descriptions of work style are the preferred source over company chat exports, and the user checks employer policy before extracting anything from a tenant.
**Why:** Access is often cut on the last day. Filtering weekly and flagging lines for review keeps the vault close to exit-ready, so nothing depends on a last-minute export. It reduces the risk; it doesn't guarantee it.

## D-015: The real vault lives in its own private repo (2026-09-29), **Proposed**
**Decision:** A person's vault is a separate private repo. It uses soul.me (spec, validator, prompts) at a pinned git tag, checked out next to it locally and in its CI.
**Why:** Real personal data must never enter this repo (AGENTS.md). Pinning means a spec change can't silently break a real vault.

## D-016: Where extraction runs (2026-09-29), **Proposed**
**Decision:** Extraction runs in the vendor the material came from, on a local model, or in an agent session attached only to the vault repo. It never runs in a session that has soul.me attached.
**Why:** Whatever runs extraction sees the raw material. These options add no new party, or keep it local, and keep real data out of soul.me's PRs and CI logs.
