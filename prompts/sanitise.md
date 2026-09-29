# Sanitising prompt: work contexts → patterns only

For assistants inside an **employer tenant** (M365 Copilot, ChatGPT Enterprise, Claude for Work, …).
It runs **inside** the tenant, so only the sanitised answer ever leaves (D-014).

**Before you use it:**
- **Check your employer's AI and data policy.** Even a sanitised summary may be restricted by policy or contract. If in doubt, don't run it; write a [`how-i-work.md`](how-i-work.md) note from your own head instead, which is the preferred source anyway.
- Read the answer before copying it out. You are the filter of last resort; this prompt only lowers the risk.
- Use it weekly (the curation rhythm), not in a rush on your last day.

Save the answer as `vault/data/<date>-<source>-sanitised.md` (e.g. source `copilot-work`) and run
[`extract.md`](extract.md) on it with the same source name.

## Prompt

```text
I want to keep a record of HOW I work: my working style, the procedures I use and my
role-level experience. It must contain NO company content. Based on your memory and our
conversations, list what you know about me, following these rules strictly.

Keep only patterns that would be true at any employer:
- how I like to work with you (format, tone, language, planning style, what I push back on)
- generic procedures I use, written so they'd work at another company
- skills and domain competence, stated at role level ("facilitated onboarding for three cohorts")

Remove completely, and don't paraphrase them either:
- names of clients, customers, partners, colleagues, projects, products and internal systems
- numbers: revenue, budgets, prices, headcounts, KPIs, dates tied to internal events
- document titles, file names, links, quotes from internal messages
- decisions, strategy, incidents, anything confidential or not public
- anything about other people beyond their generic role ("my manager", "a sponsor")

Output a markdown list grouped under: ## How I like to work, ## Procedures, ## Skills and experience.
Start each line with [told] if I said it directly, or [concluded] if you inferred it.

Then add a section ## Removed with only the categories and counts of what you left out,
e.g. "- client names: 4". Never the content itself.

Then add a section ## Borderline with any line you kept but aren't sure is generic enough,
so I can check it.
```

The `## Removed` counts go into the weekly curation PR as "what was stripped"; the `## Borderline`
lines are where the human review starts.
