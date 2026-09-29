# soul.me

**A portable, human-owned "me" for any LLM.**

The longer you work with an assistant, the more it knows how you roll: your role, your standards,
your habits, the projects you carry. That aggregated experience is locked inside one vendor
account, and when you change jobs it often stays with your employer's tenant.

soul.me gets the "me" *out* of an account and lets you drop it *into* any new one.

> SOUL.md files give agents a personality. soul.me describes a **human**.

## The idea in one picture

```text
  ChatGPT ─┐                                   ┌─► Claude
  Claude  ─┼─► extract ─► curate ─► soul.me ──►├─► ChatGPT
  Copilot ─┤   (interview,  (you     (git repo  ├─► local Qwen
  exports ─┘    exports)    review)   of .md)   └─► any MCP client
```

## What "me" is: four layers

| Layer | Contents | Size | How it reaches the model |
|---|---|---|---|
| **Core**: `minime.md` | identity + operating manual (how to work with me) | 1–2 pages | always loaded |
| **Procedures**: `skills/` | workflows I repeat | small files | loaded on demand |
| **Episodic**: `areas/`, `people/`, `topics/` | projects, decisions, context, all dated | grows | searched (the RAG part) |
| **Session**: `sessions/` | handoff notes between tools | expires | read at start, pruned |

Only the episodic layer needs retrieval. The rest is small enough to load directly, and the core
alone gets a new account about 70% of the way to "knowing me".

## Principles

1. **Human-owned storage.** Plain markdown in git. Migrating is a `git clone`.
2. **Stated, not inferred.** Every line is marked with where it came from. The model's guesses never pass as facts.
3. **Patterns travel, content stays.** On offboarding, how you work goes with you; employer data stays behind.
4. **Curation over retrieval.** Memory goes stale. A regular pass merges, retires and flags contradictions.
5. **Context, not storage.** The model never "uses memory", it uses context. Choosing what enters it is the work.

## Repo map

| File | What |
|---|---|
| [docs/vision.md](docs/vision.md) | the vision, end to end |
| [docs/concept.md](docs/concept.md) | the concept in depth |
| [docs/research.md](docs/research.md) | who else is doing this, what to borrow (with sources) |
| [docs/architecture.md](docs/architecture.md) | the solution architecture |
| [docs/spec.md](docs/spec.md) | vault file format, checked by `tools/validate.py` |
| [vault/](vault/) | a **fictional** example vault (Mara Keller) |
| [prompts/](prompts/) | v1 intake prompts, with a fictional worked example |
| [docs/own-vault.md](docs/own-vault.md) | set up your real vault in its own private repo |
| [DECISIONS.md](DECISIONS.md) | decision log |
| [ROADMAP.md](ROADMAP.md) | what gets built, in what order |
| [AGENTS.md](AGENTS.md) | orientation for agents working in this repo |

Status: **v0**. A spec, a validator and a fictional example vault.
