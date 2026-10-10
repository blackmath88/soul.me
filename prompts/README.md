# Prompts (v1 intake)

Used by hand: copy a prompt into an assistant and save its answer in **your own vault** (see [docs/own-vault.md](../docs/own-vault.md)).
Never paste real material into this repo.

| Prompt | Input | Output |
|---|---|---|
| [how-i-work.md](how-i-work.md) | your own head (preferred source) | `data/<date>-self-note.md` |
| [memory-dump.md](memory-dump.md) | a personal-account assistant's memory | `data/<date>-<source>-dump.md` |
| [sanitise.md](sanitise.md) | an employer-tenant assistant, **after checking policy** | `data/<date>-<source>-sanitised.md` |
| [extract.md](extract.md) | any one of the above | `inbox/<date>-<source>.md`, validator-clean (manual path) |
| [lenses.md](lenses.md), [intake-map.md](intake-map.md), [intake-judge.md](intake-judge.md), [intake-gaps.md](intake-gaps.md) | read by `tools/extract.py` | the automated path: edit lenses and wording here, no code change needed |
| [interview.md](interview.md) | read by `tools/interview.py` | the next few questions, from the open gaps and thin sections |
| [curate-conflicts.md](curate-conflicts.md) | read by `tools/conflicts.py` | contradiction and duplicate pairs, by line id, for the weekly review |
| [intake-corrections.md](intake-corrections.md) | read by `tools/classify_corrections.py` | the automated version: JSON by line id; code counts `seen` |
| [classify-corrections.md](classify-corrections.md) | JSONL from `tools/chatgpt_corrections.py`, for a local model | `inbox/<date>-chatgpt-corrections.md` with `(seen: n)` ([docs/chatgpt-import.md](../docs/chatgpt-import.md)) |

## Example (fictional)

[`examples/mara-chatgpt-dump.md`](examples/mara-chatgpt-dump.md) is a made-up ChatGPT dump for Mara Keller with
four traps in it: a bank number, a health detail, private details about a colleague, and a contradiction.
[`examples/mara-extract-output.md`](examples/mara-extract-output.md) is the result of applying `extract.md` to it by hand in a
Claude session: the traps are counted in `dropped:`, the contradiction lands under Tensions, and the file passes
`tools/validate.py` when placed in `vault/inbox/`. A real vendor run may differ, so always run the validator.
