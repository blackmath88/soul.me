# Vault spec (v0)

What a valid soul.me vault looks like. `tools/validate.py` checks the rules marked **(checked)**.

```bash
pip install pyyaml
python tools/validate.py            # validates ./vault
python tools/validate.py path/to/vault
```

It prints `path:line: message` for each problem and exits 1 if there are any.

## Layout

```text
vault/
  minime.md                 core: identity + operating manual (≤ 1,500 words)
  skills/<name>/SKILL.md    procedures
  areas/<name>.md           ongoing involvements
  people/<name>.md          relationship context only
  topics/<domain>.md        facts by domain
  sessions/<date>-<slug>.md handoffs, pruned after 14 days
  inbox/                    imported / inferred lines awaiting review
  data/                     raw source material, gitignored
```

Every `.md` file under `vault/` is validated, except anything in `data/`.

## Frontmatter

Every file starts with a YAML frontmatter block. **(checked)**

| Field | Required | Rule |
|---|---|---|
| `name` | yes | equals the file name without `.md`; for skills, the folder name. Lowercase, digits, hyphens. |
| `description` | yes | one line: what this is and when to read it (≤ 1,024 chars, same limit as the Agent Skills spec) |
| `scope` | yes | `always` \| `global` \| `project` \| `session` |
| `updated` | yes | ISO date `YYYY-MM-DD` |
| `aliases` | no | list of other names |
| `profiles` | no | which exports may include the file: `[work, personal]`. Defaults: `minime.md` and `skills/` both, `areas/` and `topics/` personal only; `people/` is never in `work` (D-022). Skills put it under `metadata:` as a string, e.g. `profiles: "work personal"`. |

Other fields are allowed in vault files.

**`SKILL.md` exception (D-018).** Skills follow the [Agent Skills spec](https://agentskills.io/specification), so they
load as standard skills. Only `name`, `description`, `license`, `compatibility`, `metadata` and `allowed-tools` may sit at the
top level. `scope` and `updated` go under `metadata:` as quoted strings. **(checked)**

```yaml
---
name: run-a-retro
description: how I run a 60-minute retro; use when asked to plan or run one
metadata:
  scope: global
  updated: "2026-09-20"
---
```
`minime.md` must have `scope: always`, and files in `sessions/` must have `scope: session`. **(checked)**

## Body

One fact per line. Outside the frontmatter, every non-blank line is one of the following:

- a heading (`# ...`)
- a list item (`- ...` or `1. ...`) that starts with **exactly one** provenance tag **(checked)**

Anything else (paragraphs, quotes, tables, code blocks) is an error. It's strict on purpose: a
line without a tag is a line whose origin nobody knows.

### Provenance tags

| Tag | Meaning | Allowed in |
|---|---|---|
| `[stated]` | the person said it, or confirmed it | everywhere |
| `[inferred]` | a model concluded it | `inbox/` only **(checked)** |
| `[imported:<source>]` | pulled from an export, not yet reviewed; `<source>` is `<provider>-<place>` in lowercase, e.g. `chatgpt-home`, `copilot-work`, or `self` for your own note (D-020) | `inbox/` only **(checked)** |

Inbox lines written by `tools/extract.py` end with the evidence they came from, e.g. `(quote: "keep answers short")`.
The quote is allowed in `inbox/` only **(checked)**: drop it when you seal the line (D-023).

### Seen count (inbox only)

Imported lines that were merged from several conversations may carry how many distinct conversations they
were seen in, right after the tag: `- [imported:chatgpt] (seen: 4) Lead with the recommendation`.
It helps the review and is only allowed in `inbox/` **(checked)**, just as D-009 limits unreviewed tags:
drop it when you seal the line. `n` is a whole number, at least 1 **(checked)**.

Promotion is manual: a human rewrites an inbox line as `[stated]` and moves it to a live file.
A tool never turns `[inferred]` into `[stated]`.

### Validity

Anything that can expire carries a window right after the tag. Months or days are both fine. **(checked: format)**

```markdown
- [stated] (valid_from: 2026-06) Leads onboarding for three pilot cohorts
- [stated] (valid_to: 2026-12) Contract runs until the end of December
```

## minime.md

Two sections, `# Identity` and `# Operating manual` **(checked)**, at most **1,500 words** of body text,
not counting frontmatter and tags **(checked)**. An optional `## Tensions` section keeps contradictions;
they are part of who someone is.

- **Identity**: role, domain, background, what they're working toward, a few firm beliefs. Only facts that stay true for months.
- **Operating manual**: written to the assistant. Covers language and format, how they plan, what they push back on, what they don't want.

### Quality checklist

Run this by hand before merging a change to `minime.md`. It isn't automated.

- [ ] **Predict my take.** Pick a topic the file doesn't mention. Could a reader guess the person's position from it? If not, it's too vague.
- [ ] **Weak-model test.** Paste it into a small model and ask for the person's view on that topic. Does it land close?
- [ ] **Actionable manual.** Would each operating-manual line change what an assistant does? Cut lines that wouldn't.
- [ ] **Months, not weeks.** Is everything true for months? Move short-lived items to `areas/` with a `valid_to`.
- [ ] **No secrets.** No IDs, health details, client or employer data, or other people's sensitive data.
- [ ] **Tensions kept.** Are real contradictions recorded rather than smoothed over?
- [ ] **Fits the budget.** Is it at most 1,500 words? The validator checks this.
- [ ] **All stated.** Is every line `[stated]`? The validator checks this too.

The first two checks come from aaronjmars/soul.md (see [research](research.md#2a-deep-dives-the-four-closest-matches-checked-2026-09-29)).

## Not checked yet

- Sessions older than 14 days (curation pass, v3)
- Facts past `valid_to` (curation pass, v3)
- `inbox/` files older than 4 weeks (curation pass, v3, D-012)
- Duplicates and contradictions across files (v3)
