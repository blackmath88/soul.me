# Prompts (v1 intake)

Used by hand: copy a prompt into an assistant and save its answer in **your own vault** (see [docs/own-vault.md](../docs/own-vault.md)).
Never paste real material into this repo.

| Prompt | Input | Output |
|---|---|---|
| [how-i-work.md](how-i-work.md) | your own head (preferred source) | `data/<date>-self-note.md` |
| [memory-dump.md](memory-dump.md) | a personal-account assistant's memory | `data/<date>-<source>-dump.md` |
| [sanitise.md](sanitise.md) | an employer-tenant assistant, **after checking policy** | `data/<date>-<source>-sanitised.md` |
| [extract.md](extract.md) | any one of the above | `inbox/<date>-<source>.md`, validator-clean |
| [classify-corrections.md](classify-corrections.md) | JSONL from `tools/chatgpt_corrections.py`, for a local model | `inbox/<date>-chatgpt-corrections.md` with `(seen: n)` ([docs/chatgpt-import.md](../docs/chatgpt-import.md)) |

## Example (fictional)

[`examples/mara-chatgpt-dump.md`](examples/mara-chatgpt-dump.md) is a made-up ChatGPT dump for Mara Keller with
four traps in it: a bank number, a health detail, private details about a colleague, and a contradiction.
[`examples/mara-extract-output.md`](examples/mara-extract-output.md) is the result of applying `extract.md` to it by hand in a
Claude session: the traps are counted in `dropped:`, the contradiction lands under Tensions, and the file passes
`tools/validate.py` when placed in `vault/inbox/`. A real vendor run may differ, so always run the validator.
