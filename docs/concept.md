# Concept

## The problem

- **Lock-in.** Each assistant (ChatGPT, Claude, Copilot) builds its own picture of you. None of those pictures travel.
- **Offboarding.** When you leave an employer, the experience you built in the company's LLM tenant stays in that tenant. Nobody offboards the *person's* AI self.
- **Cold starts.** Every new account, tool or local model starts from zero, and you re-explain yourself.

## The four layers of "me"

### 1. Core: `minime.md` (always loaded)

Two sections, 1–2 pages in total. It has to fit into custom instructions or a project file.

- **Identity**: role, domain, background, what I'm working toward. Only facts that stay true for months.
- **Operating manual**: how to work with me. Language, format, depth, planning style, what I push back on, what I don't want.

Quality bar (borrowed from kevinpinscoe/soul.md): *someone reading it should be able to predict
my take on a new topic.* Contradictions stay in; they are part of who someone is.

### 2. Procedures: `skills/` (loaded on demand)

Workflows I repeat: how I run a design sprint, onboard a Copilot cohort, review a draft.
One markdown file per procedure, in a skill format that most agent tools can read.

### 3. Episodic knowledge: `areas/`, `people/`, `topics/` (searched)

- `areas/`: ongoing involvements (projects, roles, communities), with decisions, status and constraints.
- `people/`: relationship context, not dossiers.
- `topics/`: facts by domain (tools, hardware, interests).

Every fact carries a date. Facts have validity windows: "leads X" is true *until* it isn't.

### 4. Session: `sessions/` (expires)

Handoff notes, such as "was working on Y in Claude, continue in ChatGPT". Pruned after about 14 days.

## Provenance: stated vs inferred

Every line carries a tag:

| Tag | Meaning |
|---|---|
| `[stated]` | I said it, or confirmed it |
| `[inferred]` | a model concluded it; not trusted until confirmed |
| `[imported:<source>]` | pulled from an export; waiting for review |

Observstory draws the same line between observed, derived, heuristic and declared data. soul.me applies it to a person.

## Scopes (when something is loaded)

| Scope | Loaded | Example |
|---|---|---|
| `always` | every session | minime.md, hard rules |
| `global` | when relevant, across projects | tool preferences |
| `project` | only inside that project | area files |
| `session` | current handoff | sessions/ |

## Lifecycle

```text
 intake ──► review ──► live ──► curate ──► retire
 (interview,  (human    (served   (merge,     (archived with
  exports,     confirms) to LLMs)  date, flag  a validity end,
  chats)                           conflicts)  never silently deleted)
```

## Offboarding: patterns vs content

| Travels with you | Stays with the employer |
|---|---|
| operating manual, working style | client and internal data |
| generic procedures (how I facilitate) | internal process specifics, names, numbers |
| skills and domain competence | confidential decisions, documents |
| the fact that you did the work (role-level) | the work product itself |

Extraction from a company account therefore needs a **sanitising pass**: a filter prompt plus human review.
This is also a governance offering: *portable professional self* as part of AI-era offboarding.

## Privacy defaults

- Never store: government or financial IDs, health details, other people's sensitive data.
- `people/` holds relationship context only.
- The repo is private by default. MCP access is scoped per client.
