# Intake: judge (all candidates of one run)

Used by `tools/extract.py` after the map pass. The judge decides what is worth the person's time:
they will only see the top-ranked lines. Keep the placeholders and the `TASK:` line.

## Prompt

```text
TASK: judge
You review candidate facts about a person before they reach their personal vault. Be strict:
the person reviews only a short list, so keep what is true, lasting and useful to an assistant.

Their vault today:
{vault}

Candidates (JSON; recurrence = in how many conversations it appeared):
{candidates}

For every candidate return:
- id
- keep: false for trivia, one-off moods, things the vault already says, and anything sensitive
- confidence: 0 to 1, how sure you are it is true and still holds
- stability: "months" if it will likely hold for months, "weeks" if short-lived, "unclear"
- sensitive: true for health, money, IDs, or private details of other people
- target: the vault file it belongs in, e.g. "minime.md#Operating manual", "skills/", "topics/admin.md"
- contradicts: the exact vault line it conflicts with, or null
- line: the fact rewritten as one short line in the third person
```
