# Intake: gaps (end of a run)

Used by `tools/extract.py` to make the next run smarter: the questions go into the next run's map
prompts, and the top three are shown to the person in the digest. Keep the placeholders and the `TASK:` line.

## Prompt

```text
TASK: gaps
Below are the lenses soul.me uses, what the person's vault says today, and what this run found.
List up to three questions the vault still can't answer and that would most improve how an
assistant works with this person. Ask about patterns and preferences, never about sensitive details.

Lenses:
{lenses}

Vault today:
{vault}

Found in this run:
{findings}
```
