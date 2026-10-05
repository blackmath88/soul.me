# Vision

> **Your working self is a file you own. Any assistant, at any employer, starts from it.
> You're the only one who approves changes to it, and it leaves with you.**

Today every assistant builds its own picture of you, and none of those pictures travel.
soul.me makes the picture a private git repo of markdown, and every assistant reads from that repo.
Assistants can *propose* changes. Only you merge them.

The visual north star is [`brand/brand-kit.html`](../brand/brand-kit.html): many sources, one self, and
*grey is the world, colour is yours*.

## End to end: one year of Mara's working life

Mara Keller is the fictional example in [`vault/`](../vault/). Here is the whole loop, stage by stage.

| # | Stage | What happens | Component | Writes to | Approves |
|---|---|---|---|---|---|
| 1 | **Day 0: intake** | memory dumps from ChatGPT and Claude, a self-written "how I work" note, a short interview | intake prompts (v1) | `inbox/` as `[imported:*]` | Mara, line by line → `[stated]` |
| 2 | **Daily use** | Claude, ChatGPT and a local Qwen all start from `minime.md`; handoffs between them go to `sessions/` | drop-in export (v2), MCP later (v4) | `sessions/`; proposals to `inbox/` | nobody: reads only |
| 3 | **Weekly curation** | one PR that batches inbox review, merges dupes, retires expired facts, prunes sessions, **and runs the sanitising pass** | curation Action (v3) | a PR, never `main` | Mara merges |
| 4 | **Job change** | a short final check of the latest curation PR; no bulk extraction | curation PR (v3) | none | Mara |
| 5 | **New tenant** | drops the export into the new assistant; productive on day 1 | drop-in export (v2) | none | none |

### 1 · Intake

Material comes from the vendors' own "tell me what you know about me" answers, from what Mara has written herself,
and from an interview that fills gaps in `minime.md`. An LLM sorts it into the four layers and tags every line
`[imported:<source>]` or `[inferred]`. Nothing is live until she confirms it.

### 2 · Daily use

The core is small enough to paste, so the default path is **drop-in files**: custom instructions and project files.
That works in any tenant, including ones that block MCP connectors. The MCP server comes later and adds search over
the episodic layer plus a `propose` tool. When an assistant notices something new about her, it proposes; it never writes.

### 3 · Weekly curation: offboarding-ready by default

Employer access is often cut on the last day, sometimes without notice. **So nothing depends on an exit-time extraction.**
Sanitising runs every week inside the curation PR:

- New material from work contexts goes through the sanitising prompt **before** it reaches `inbox/`. The aim is that
  only patterns survive: working style, generic procedures, role-level facts, and not client names, internal numbers or documents.
- The curation PR shows what was stripped and flags anything that still looks like employer content, so Mara reviews it.
- Employer content is filtered weekly and flagged for review, so the vault stays close to exit-ready.
  **This reduces the risk; it doesn't guarantee it.** A prompt filter can miss things, and Mara's review is the real control.

The inbox gets a batch review in the same PR. Proposals nobody reviews expire after four weeks (D-012),
so the inbox can't grow into a second, unreviewed memory.

### 4 · Job change

Because of stage 3, there's no bulk extraction to rush on the way out. Mara does one last check of the vault for flagged
or borderline lines, removes anything doubtful, and takes the rest with her.

### 5 · New tenant

On day 1 she pastes the drop-in export into the new employer's assistant. The operating manual (language, format,
how she plans, what she pushes back on) takes effect immediately, while the old employer's content stays behind.

## Trust boundaries

```text
 ┌──────────────── EMPLOYER TENANT ───────────────┐      ┌──────────── MINE ─────────────┐
 │ M365 Copilot / ChatGPT Enterprise / ...        │      │ private git repo (the vault)  │
 │ client data · internal docs · chat history     │      │ laptop: validator, local LLM, │
 │                                                │      │         MCP server (later)    │
 │   sanitising prompt runs HERE ── patterns ─────┼─────►│ inbox/ → review → live        │
 │   (never raw content)                          │      │                               │
 │                                   ◄────────────┼──────┤ drop-in export (read-only)    │
 └────────────────────────────────────────────────┘      └───────────────┬───────────────┘
                                                                         │ drop-in / MCP
                                                        ┌────────────────▼───────────────┐
                                                        │ VENDOR CLOUDS (personal)       │
                                                        │ Claude, ChatGPT: read core,    │
                                                        │ propose only                   │
                                                        └────────────────────────────────┘
```

- **Into the employer tenant:** only the drop-in export, which Mara chooses and which is read-only.
- **Out of the employer tenant:** only patterns, after sanitising. Raw chat exports from an employer tenant never cross.
- **Check your employer's policy first.** Extracting anything from an employer tenant, even a sanitised summary,
  may be restricted by policy or contract. soul.me can't decide that for you. The preferred source is a
  **self-authored description of your work style**, written by you on your own time. It carries the same patterns
  without touching company data, and company chat exports should be the exception.
- **Vendor clouds** get the core and whatever scopes a client is allowed (per-client allowlist). They can propose
  changes but never write.

## North star, in stages

1. **Files that travel (v0–v2).** A validated vault and a paste-able export. This alone solves the cold start.
2. **A self that stays current (v3).** Weekly curation keeps it true and offboarding-ready.
3. **A self you can query (v4).** An MCP server for search, handoffs and proposals.
4. **Later.** An offboarding kit as a bridge-work.ai offer: employee-side guidance, the sanitising prompt,
   and a policy template employers can sign off.

## What we won't do

- Hold anything the person hasn't approved in a live file.
- Store employer content, even temporarily "until cleaned".
- Make the model speak *as* the person. soul.me describes a human to an assistant working *with* them.
- Build a UI, a graph database or multi-user support before the files have proved themselves.
