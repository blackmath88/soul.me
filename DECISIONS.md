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

## D-017: Temporal facts: valid time on the line, transaction time from git (2026-09-29), **Proposed**
**Decision:** Lines carry `(valid_from: …)` / `(valid_to: …)` for when a fact is true. When the vault learned it comes from git history, with no extra fields. When a fact changes, the old line gets a `valid_to` and moves to an `# Archive` section; it is never deleted unless it was wrong from the start.
**Why:** This keeps Graphiti's bi-temporal model (research §8) in plain markdown, and git already records the second timeline.

## D-018: SKILL.md follows the Agent Skills spec (2026-09-29), **Proposed**
**Decision:** In `skills/*/SKILL.md`, only spec fields sit at the top level. soul.me's `scope` and `updated` go under `metadata:` as strings, and the validator enforces both.
**Why:** The reference validator `skills-ref` rejects unknown top-level fields, so our skills weren't loadable as standard skills (research §7).

## D-019: The brand kit is the visual north star (2026-09-29)
**Decision:** `brand/brand-kit.html` (round 2) defines soul.me's visual identity: the kitsune fox, sumi greys, and the rule "grey is the world, colour is yours" (colour only on what the person has sealed; shu red only for the seal).
**Why:** The owner chose it. The rule restates D-004 and D-006 visually, so the brand cannot drift from the product's core promise.

## D-020: Source slugs name provider and place (2026-09-29), **Proposed**
**Decision:** `[imported:<source>]` uses `<provider>-<place>`, e.g. `chatgpt-home`, `copilot-work`, or `self`. The validator already accepts it; the spec and prompts now ask for it.
**Why:** The place decides the rules (sanitising, offboarding); the provider only decides the format. Both have to be visible on every imported line.

## D-021: Origin after sealing lives in git (2026-09-29), **Proposed**
**Decision:** No extra syntax on `[stated]` lines. The commit that promotes lines names the inbox file they came from (`seal: inbox/<file>`), so "stated lines that came from work" is a `git log` query.
**Why:** Same principle as D-017: git already keeps the second timeline, so the files stay simple.

## D-022: Serving uses profiles (2026-09-29), **Proposed**
**Decision:** The drop-in export (v2) and the MCP server (v4) take a profile that decides which folders leave the vault: `work` (minime, skills, work areas; never people/, private topics or sessions) and `personal` (everything live).
**Why:** Places are destinations as well as sources. The main serving path (D-013) needs the same protection the MCP server's allowlists were planned to have.

## D-023: Inbox lines carry their evidence (2026-10-02), **Proposed**
**Decision:** Lines written by `tools/extract.py` end with `(quote: "…")`, copied word for word from the person's own message. The validator allows it in `inbox/` only; it is dropped when a line is sealed.
**Why:** The reviewer sees why a line was proposed in one glance, and an invented fact has no quote to show.

## D-024: Redaction happens in code, before any model (2026-10-02), **Proposed**
**Decision:** IDs (AHV), IBANs, card numbers, emails, phone numbers and the terms in `data/denylist.txt` are replaced before text reaches a model. Prompts and the judge are a second layer, not the first. Conversation titles are never stored.
**Why:** A prompt rule asks a model to behave; code guarantees it. The evaluation found a health detail leaking through a vendor-written title.

## D-025: Models return schema-constrained JSON; markdown is written by code (2026-10-02), **Proposed**
**Decision:** Every intake model call asks for JSON matching a schema (falling back to plain JSON); quotes are verified and the inbox file is rendered by the script.
**Why:** Small local models fail at strict markdown first. With the format in code, the validator becomes a check, not a repair loop.

## D-026: Intake asks lenses, iteratively; the person seals a short ranked list (2026-10-02)
**Decision:** Intake asks a list of questions ("lenses": how I work, what I learned, what I built, career, procedures, admin patterns) over the person's own messages. Each run includes what the vault already says and the open questions from the last run, so it reports what's new. A judge pass ranks findings and only the top 12 reach the inbox; the person seals them (review option A). Nothing is auto-accepted.
**Why:** The owner chose option A: minimal manual effort without giving up D-004/D-006. Judgement comes from the lenses and the judge; truth still comes from the person.

## D-027: Bulk imports get staged review (2026-10-05), **Proposed**
**Decision:** Large imports (e.g. a full ChatGPT export) reach `inbox/` in batches, one per cluster, with Operating-manual candidates first. D-012's 4-week expiry starts per batch when it is released for review, not at import.
**Why:** A whole export at once would flood the inbox and expire unread. Small batches keep the weekly review possible, and the Operating manual changes the most for the least reading.

## D-028: Pasted text is never `[imported]` (2026-10-05), **Proposed**
**Decision:** Long pasted user turns are source material, not statements about the person. Converters replace user turns over 2,000 characters with a stub (`[pasted: n chars, starts "…"]`) and count only authored characters.
**Why:** In a real export 84% of user characters were pasted material. Treating it as the person's own words would fill the vault with other people's text.

## D-029: Export input allowlist (2026-10-05), **Proposed**
**Decision:** Converters read only conversation shards (`conversations*.json`) and the asset-name maps (`conversation_asset_file_names.json`, `library_files.json`). Account files (`user.json`, `user_settings.json`) and everything else in the export are never opened; the test fails if they are.
**Why:** `user.json` holds email, phone and birth year. The safest way to keep identifiers out is never to read them.

## D-030: MCP clients propose, tagged by who said it; handoffs stay manual for now (2026-10-10), **Proposed**
**Decision:** The MCP server's `propose` writes to `inbox/<date>-mcp-<client>.md` only. Lines are `[inferred]` unless the client marks them as something the person said in the conversation (`told`), then `[imported:<client>]`, with the client named `<provider>-<place>` (D-020). The server never writes `[stated]`, so `handoff(note)` is not built yet: a session file only allows `[stated]`, and a model writing that tag would be a tool sealing on the person's behalf.
**Why:** Same rule as intake (D-004, D-006): anything a model writes waits for the person. Whether handoffs get their own unreviewed tag or go through the inbox is the owner's call.
