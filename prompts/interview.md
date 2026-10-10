# Interview: pick the next questions

Used by `tools/interview.py`, on your own machine and against your own model. The model only chooses and phrases
questions; your answers are saved word for word as a self note in `data/` and go through the normal intake
(`tools/extract.py --source self`). The questions themselves are never saved into the note.
Keep the placeholders and the `TASK:` line.

## Prompt

```text
TASK: interview
You help a person keep a short, accurate file about how they work. Below is what their file says today,
the questions earlier runs could not answer, and a standard question list.
Choose the {n} questions whose answers would most improve how an assistant works with this person.
Prefer open gaps and thin sections over things the file already answers well. Ask about patterns and
preferences, never about health, money, IDs or other people's private details.
Each question: one sentence, plain words, answerable in two or three sentences.

Their file today:
{vault}

Open questions from earlier runs:
{gaps}

Standard questions:
{standard}

Return {"questions": ["...", "..."]}.
```
