# Research: landscape (as of 2026-09-29)

Three schools of work exist. Nobody combines them into a *human-owned, portable self*.

> **Link check, 2026-09-29.** Every link below was fetched. Unmarked links resolved.
> ❌ = dead · ↪ = moved (new URL given) · ⚠️ = blocks automated clients (HTTP 403), not verified by hand.
> GitHub repos were checked with `git ls-remote` (the API was not reachable from the check environment).

## 1. Identity files ("SOUL.md" as a format)

| Project | What | Borrow |
|---|---|---|
| [kevinpinscoe/soul.md](https://github.com/kevinpinscoe/soul.md): a fork of **upstream [aaronjmars/soul.md](https://github.com/aaronjmars/soul.md)**. [aeonfun/soul.md](https://github.com/aeonfun/soul.md) points at the same commit as upstream. | SOUL.md (worldview), STYLE.md (voice), SKILL.md (modes), MEMORY.md; `data/` for raw material; built by agent interview or by analysing exports | intake modes, the "predict my take" quality bar, keep contradictions |
| [rokoss21/soul.md](https://github.com/rokoss21/soul.md) | provider-agnostic persona spec | spec discipline |
| [AntonioTF5/soul-spec](https://github.com/AntonioTF5/soul-spec) | SOUL.md spec + JSON schema + validator | validate the frontmatter |
| [thedaviddias/souls-directory](https://github.com/thedaviddias/souls-directory), [madhvantyagi/SOUL.md](https://github.com/madhvantyagi/SOUL.md), [arpatek/ai-soul](https://github.com/arpatek/ai-soul) | personalities for *agents* (OpenClaw etc.) | shows the gap: agent persona ≠ human self |
| [SOUL.md template guide (dev.to)](https://dev.to/tomleelive/the-complete-soulmd-template-guide-give-your-ai-agent-a-personality-3php) | template walkthrough | – |

## 2. Memory served over MCP (the portability layer)

| Project | What | Borrow |
|---|---|---|
| [openport](https://github.com/theodorexli/openport) ([Glama listing](https://glama.ai/mcp/servers/theodorexli/openport)) | three layers: Memory, Skill, Session; scopes `_important`/`_protected` (always), `_global`, per-project, `_session` (14-day retention); markdown in SQLite; runs on local Node or Cloudflare D1 | **closest architectural match**: layers, scopes, handoffs. ❌ **Repo dead** (404 on 2026-09-29, also private or deleted for git clone). No fork or mirror found (searched GitHub, gitlab.com, Software Heritage, Wayback, npm; the npm package `openport` is an unrelated 2012 port finder). The Glama listing mentions a GitLab mirror, but it is not public. **Glama is now the only source.** |
| [vault-mcp](https://github.com/wakita181009/vault-mcp) ([TNW article](https://thenextweb.com/news/llms-remember-code-not-life-portable-context-layer)) | markdown in a user-owned GitHub repo (Obsidian vault), served over MCP, every write is a git commit (overwrite and delete are allowed, so it's revertable rather than append-only), edge-deployed | **storage model**: git + md, migrating = `git clone`, audit trail |
| [OpenMemory MCP (mem0)](https://mem0.ai/blog/introducing-openmemory-mcp) | local-first; vector DB; tools `add_memories`, `search_memory`, `list_memories`, `delete_all_memories`; dashboard with per-client access control | the per-client access dashboard |
| [alphaonedev/ai-memory-mcp](https://github.com/alphaonedev/ai-memory-mcp) | SQLite FTS5, no cloud; claims **97.0% R@5 on LongMemEval-S with pure FTS5, no LLM** (the older 97.8% figure used Gemma 3 query expansion and was retired as the headline in July 2026) | **full-text search may be enough**; vectors later |
| [cunicopia-dev/local-memory-mcp](https://github.com/cunicopia-dev/local-memory-mcp) | memories saved locally on your own hardware | local option |
| [akitaonrails/ai-memory](https://github.com/akitaonrails/ai-memory) | long-term memory + handoff between coding-agent vendors | session handoff |
| [awesome-mcp-servers: memory](https://github.com/TensorBlock/awesome-mcp-servers/blob/main/docs/knowledge-management--memory.md) | index of memory MCP servers | keep watching |

## 3. Memory frameworks (theory to adopt)

- [Graphlit: AI Agent Memory Frameworks 2026](https://www.graphlit.com/blog/survey-of-ai-agent-memory-frameworks)
  - memory types: working, session, **semantic** (facts, preferences), **episodic** (events with timestamps), **procedural** (how-to), **temporal graph** (facts with validity windows)
  - *"The model does not use memory directly. It uses context."* Context engineering is the edge, not storage.
  - separate the agent runtime from the context layer
- **Letta / MemGPT** ([memory blocks](https://www.letta.com/blog/memory-blocks/), sleep-time agents ↪ now ["Memory & dreaming"](https://docs.letta.com/configuration/memory), core memory ↪ [redirects to the deprecated ADE page](https://docs.letta.com/v1-sdk/ade))
  - small always-in-context core blocks that the agent edits itself, plus a large archival store
  - **sleep-time agents** consolidate memory between sessions, which is our curation pass
- **Zep / Graphiti**: temporal knowledge graphs; facts have `valid_from` / `valid_to`
- Comparisons: [Wasowski (Medium)](https://medium.com/@wasowski.jarek/i-compared-5-ai-agent-memory-systems-across-6-dimensions-none-wins-6a658335ed0a) ⚠️, [Mnemoverse Q3 2026](https://mnemoverse.com/docs/library/ai-memory-solutions-2026-q3), [dev.to](https://dev.to/plur9/mem0-vs-letta-vs-zep-which-should-you-use-for-agent-memory-1n8m), [GeniOS](https://thegenios.com/blog/open-source-memory-layers-2026/), [particula](https://particula.tech/blog/agent-memory-frameworks-tested-mem0-zep-letta-cognee-2026). Consensus: no single system wins; pick by use case.

## 4. What vendors offer

- **Claude**: memory import/export ([help article](https://support.claude.com/en/articles/12123587-import-and-export-your-memory-from-claude)). You export with a prompt and paste it into the import flow. Labelled *experimental*.
- Guides for moving ChatGPT memory to Claude: [Tom's Guide](https://www.tomsguide.com/ai/you-can-move-your-chatgpt-memory-to-claude-in-60-seconds-heres-how), [Will Francis](https://willfrancis.com/move-memory-from-chatgpt-to-claude/), [Medium](https://medium.com/@unicodeveloper/how-to-import-memory-into-claude-from-chatgpt-gemini-or-grok-step-by-step-guide-c78ac8f7e4a4) ⚠️.
- **Gap:** vendors move flat facts only. There are no procedures, no episodic layer and no provenance, and it's one-shot rather than a living source.

## 5. Governance: offboarding and ownership

- [Forbes: "Your employee just resigned. Who inherits their AI?"](https://www.forbes.com/councils/forbestechcouncil/2026/08/11/your-employee-just-resigned-who-inherits-their-ai/): agents built by employees are enterprise assets and need succession planning.
- [Yale SOM: Who owns your AI memory?](https://som.yale.edu/story/2026/who-owns-your-ai-memory): organisations are locked into vendor memory silos.
- Also: [Adaptive Recall](https://www.adaptiverecall.com/enterprise-memory/employee-leaves.php), [vdf.ai](https://vdf.ai/blog/offboarding-people-enterprise-ai-platform/).
- **Gap:** the debate is framed from the employer's side. The *employee's* portable self (patterns travel, content stays) is unclaimed territory, and a positioning opportunity for bridge-work.ai.

## Synthesis: what we adopt

| Concept | From |
|---|---|
| human-self files, intake by interview + exports | kevinpinscoe/soul.md |
| three runtime layers + scopes + expiring handoffs | openport |
| git + markdown vault, append-only, migration = clone | vault-mcp |
| always-loaded core + archive; background consolidation | Letta |
| facts with validity windows | Zep / Graphiti |
| full-text search before vectors | ai-memory-mcp |
| per-client access control | OpenMemory |
| observed / derived / declared distinction | Observstory (own) |
