# ChatGPT import

How to turn a ChatGPT data export into reviewable inbox lines. Everything below runs **on your own machine,
inside your private vault repo** (D-015, D-016): real conversations never enter this repo, and the tools refuse
to write into it.

## What the export contains, and what it doesn't

| In the export | Used? |
|---|---|
| `conversations-000.json … -NNN.json` (sharded): `id`, `title`, `create_time`, `current_node`, a `mapping` tree with branches from edits and regenerations | **yes**, active branch only |
| `conversation_asset_file_names.json` (dat name → original filename), `library_files.json` (newer `file_000…` assets) | **yes**, only to name attachments |
| uploads as `.dat` files | no: the converter writes `[attachment: <name>]` |
| `user.json` (email, phone, birth year), `user_settings.json`, `chat.html`, `export_manifest.json`, everything else | **never opened** (D-029) |
| **memories** and **custom instructions** | **not in the export**: copy them by hand from Settings → Personalization, and run [`prompts/memory-dump.md`](../prompts/memory-dump.md) |

Most "user" text in an export isn't the person's own words: in one real export, 84% of user characters sat in turns over
2,000 characters, i.e. pasted material. Pasted text is source material, not a statement about you (D-028), so the
converter replaces it with a stub such as `[pasted: 14,200 chars, starts "…"]` and filters on **authored** characters.

## Run order

```bash
cd soul-vault                                   # your private vault repo; soul.me is cloned next to it
E=~/Downloads/chatgpt-export                    # the unzipped export, outside both repos

# 1 convert: one markdown file per conversation + _stats.json (kept if ≥2 user turns and ≥300 authored chars)
python ../soul.me/tools/chatgpt_export.py "$E" vault/data/chatgpt/conversations

# 2 corrections: short replies after an assistant answer, one JSON line each (no model, just a keyword hint)
python ../soul.me/tools/chatgpt_corrections.py "$E" vault/data/chatgpt/corrections.jsonl
```

3. **Classify** the corrections with your local model, batch by batch, using
   [`prompts/classify-corrections.md`](../prompts/classify-corrections.md) → `vault/inbox/<date>-chatgpt-corrections.md`
   (Operating-manual candidates with `(seen: n)`). Review this batch **first** (D-027).
4. **Extract per cluster**: group the converted conversations by theme (a folder per cluster is enough: one project,
   one client, one hobby), then run [`prompts/extract.md`](../prompts/extract.md) over one cluster at a time.
5. **Sanitise** clusters from work contexts with [`prompts/sanitise.md`](../prompts/sanitise.md) before their lines go
   anywhere near the inbox (D-014).
6. **Inbox**: release one batch at a time (D-027). Its 4-week expiry (D-012) starts when you release it, not at import.
   Run `tools/validate.py` after every file; seal what's true as `[stated]` and drop the `(seen: n)` markers.

`vault/data/` is gitignored: the converted conversations, the JSONL and `_stats.json` stay on your machine.
