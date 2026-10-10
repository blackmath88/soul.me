# Try it with your own model (fictional data, 20 minutes)

Every tool, in the order you'd use it, on a scratch copy of the fictional vault (Mara Keller) and the fictional
ChatGPT export. Nothing real is involved, so this is safe in any session. When it all works, set up your real
vault in its own repo ([own-vault.md](own-vault.md)).

```bash
git clone https://github.com/blackmath88/soul.me && cd soul.me
pip install pyyaml

# any OpenAI-compatible endpoint: Ollama, LM Studio, llama.cpp, vLLM
export SOULME_LLM_BASE=http://localhost:11434/v1 SOULME_LLM_MODEL=qwen2.5:14b

T=$(mktemp -d) && cp -r vault "$T/vault" && V="$T/vault"     # outside the repo: the tools refuse to write into it
rm "$V"/inbox/*.md                                            # start with an empty inbox
```

## 1 Is your model good enough? (5 min)

```bash
python tools/eval_extract.py
```

It runs the whole intake on fictional exports with traps in them (an IBAN, a health detail, a client name, …).
`leaks` must be 0. `recall` tells you how much your model finds; below about 6 of 9, try a larger model.

## 2 Bulk import: ChatGPT export → staged batches → inbox

```bash
python tools/chatgpt_export.py tests/fixtures/chatgpt-mara "$V/data/chatgpt/conversations"
python tools/chatgpt_corrections.py tests/fixtures/chatgpt-mara "$V/data/chatgpt/corrections.jsonl"
python tools/classify_corrections.py "$V/data/chatgpt/corrections.jsonl" --vault "$V" --stage
python tools/extract.py "$V/data/chatgpt/conversations" --source chatgpt-home --vault "$V" --stage
python tools/release.py "$V" --list          # the queue, corrections first
python tools/release.py "$V"                 # one batch into inbox/
python tools/validate.py "$V" --summary
```

Read `$V/inbox/*.md`. Each line has a tag, how often it was seen or a quote: that's what you'd seal.
To seal, rewrite a line as `[stated]` in a live file and delete it from the inbox. No tool does that for you.

## 3 Fill gaps

```bash
python tools/interview.py "$V"               # five questions; only your answers are saved, to data/
python tools/extract.py "$V"/data/*-interview.md --source self --vault "$V" --stage
```

## 4 Weekly curation

```bash
python tools/curate.py "$V"                  # what the weekly PR would say; changes nothing
python tools/curate.py "$V" --apply --today 2027-02-01   # what it would change four months from now
python tools/conflicts.py "$V"               # contradictions and duplicates, judged by your model
```

## 5 Use it

```bash
python tools/export.py "$V" --profile personal --target system     # system prompt for your local model
python tools/export.py "$V" --profile work --target chatgpt         # the two custom-instruction fields
python tools/status.py "$V" > "$T/status.svg"                       # the mask: grey, colour, seal
```

Paste the `system` output into your local model's system prompt and ask it something Mara would care about
("plan my Friday"). That's the weak-model test from the [spec](spec.md#quality-checklist).

## 6 Live, over MCP (optional)

Add this to your client's MCP config (Claude Desktop, Claude Code, …), with absolute paths:

```json
{"mcpServers": {"soul-mara": {"command": "python",
  "args": ["/path/to/soul.me/tools/mcp_server.py", "/tmp/…/vault", "--profile", "personal", "--client", "claude-home"]}}}
```

Ask the assistant to "read my core first" and then to remember something new: the new line shows up in
`$V/inbox/<date>-mcp-claude-home.md`, never in a live file.
