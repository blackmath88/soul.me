# Curation: contradictions and duplicates

Used by `tools/conflicts.py`, on your own machine and against your own model. It sees every live `[stated]` line
except `## Tensions` (contradictions the person chose to keep) and `# Archive`. It answers with line ids only;
ids that don't exist are dropped, so it can't invent a conflict. Nothing is changed: the person decides.
Keep the placeholder and the `TASK:` line.

## Prompt

```text
TASK: conflicts
Below are the confirmed facts in one person's vault, one per line, each with an id and the file it is in.
Find pairs that need the person's attention:
- contradiction: both cannot be true at the same time (e.g. two different employers "now", "always X" vs "never X")
- duplicate: they say the same thing, so one of them can go

Do not report lines that merely differ in topic, or that are both true at once (a preference and an exception to it,
a goal and a constraint). Report each pair once. When unsure, leave it out: the person reads every pair you report.

Facts:
{lines}

Return {"pairs": [{"a": "<id>", "b": "<id>", "kind": "contradiction" | "duplicate", "why": "<one short sentence>"}]}.
Return {"pairs": []} if there is nothing.
```
