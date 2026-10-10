# Intake: corrections (automated)

Used by `tools/classify_corrections.py`, the automated version of [classify-corrections.md](classify-corrections.md):
same judgement, but JSON out, so code counts `seen`, merges batches and writes the inbox file (D-025).
Keep the placeholders and the `TASK:` line.

## Prompt

```text
TASK: corrections
You read short replies a person typed right after an AI assistant answered them, with the assistant's previous
answer for context. Most are throwaway ("thanks"), some correct one answer, and a few reveal how this person
always wants assistants to work. Find those few.

1. Label every line:
   - preference: a stable instruction about HOW to work with this person (length, format, tone, language,
     structure, what to leave out) that would still apply in a different conversation next month
   - one-off: about this particular task or content only
   - noise: thanks, acknowledgements, typos, anything without an instruction
   When unsure between preference and one-off, choose one-off.
2. Turn the preference lines into candidates: one short imperative instruction to an assistant, in English.
   Lines that say the same thing (also across German and English) become ONE candidate listing all their ids.
   If a candidate means the same as one of the previous candidates, set same_as to that P-id; else null.
   Write the pattern, never names of clients, colleagues or projects, numbers, or anything private.

Previous candidates:
{previous}

Lines (id | user reply | assistant's previous answer):
{lines}

Return {"labels": [{"id": "...", "label": "preference" | "one-off" | "noise"}],
        "candidates": [{"line": "...", "ids": ["..."], "same_as": "P1" or null}]}.
```
