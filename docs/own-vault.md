# Your own vault

Your real vault lives in **its own private repo**, never in this one (D-015). soul.me is the tool:
spec, validator and prompts, used at a pinned tag.

## Set up (once)

```bash
mkdir soul-vault && cd soul-vault && git init -b main
mkdir -p vault/{skills,areas,people,topics,sessions,inbox,data} .github/workflows
touch vault/{skills,areas,people,topics,sessions,inbox}/.gitkeep
printf '*\n!.gitignore\n' > vault/data/.gitignore          # raw dumps never get committed
cat > vault/minime.md <<'EOF'
---
name: minime
description: my core; identity and how to work with me; always load
scope: always
updated: 2026-09-29
---
# Identity

# Operating manual
EOF
python ../soul.me/tools/validate.py vault                   # soul.me cloned next to it
```

Add `.github/workflows/validate.yml`:

```yaml
name: validate
on: push
jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/checkout@v4
        with:
          repository: blackmath88/soul.me
          ref: v0.1                                # pinned: spec changes never surprise the vault
          path: soul.me
          token: ${{ secrets.SOULME_READ_TOKEN }}  # only if soul.me is private; delete this line if it's public
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install pyyaml
      - run: python soul.me/tools/validate.py vault
```

To move to a newer spec, bump `ref`, run the validator locally, fix what it reports, and commit both together.

## First intake session (about 2 hours, personal accounts only)

1. **Self note** (20 min): answer [`prompts/how-i-work.md`](../prompts/how-i-work.md) → `vault/data/<date>-self-note.md`.
2. **Memory dumps**: [`prompts/memory-dump.md`](../prompts/memory-dump.md) in your personal ChatGPT and Claude → `vault/data/`.
3. **Extract**, one source at a time, with [`prompts/extract.md`](../prompts/extract.md) → `vault/inbox/<date>-<source>.md`.
   Run the validator after each file.
   Name each source `<provider>-<place>`, e.g. `chatgpt-home` (D-020).
4. **Review, minime.md first.** Move the lines you agree with into live files as `[stated]`, reworded as you like;
   delete the rest. Empty the inbox in the same session.
   Commit with the inbox file in the message, e.g. `seal: inbox/2026-09-29-chatgpt-home.md`, so origin stays findable (D-021).
5. **Fill the gaps** by answering the questions again where `minime.md` is thin, then run the quality checklist in
   [spec.md](spec.md#quality-checklist), including the weak-model test.
6. **Commit and tag** the vault `v0.1`.

**Not in session 1:** anything from an employer tenant. Later, after checking your employer's policy, use
[`prompts/sanitise.md`](../prompts/sanitise.md) inside the tenant (D-014).

## Automated intake (after session 1)

Once a month, about two minutes of clicking; everything else runs on your machine against your own model.

1. **Request the exports** (manual): ChatGPT → Settings → Data controls → Export; Claude → Settings → Privacy → Export data.
   Drop the ZIPs into `vault/data/` when the emails arrive. This can't be automated: neither vendor offers an export API.
2. **Run the intake** (automatic) against any OpenAI-compatible endpoint (Ollama, LM Studio, llama.cpp, vLLM):

   ```bash
   export SOULME_LLM_BASE=http://localhost:11434/v1 SOULME_LLM_MODEL=<your model>
   python ../soul.me/tools/eval_extract.py                        # once per model: is it good enough?
   python ../soul.me/tools/extract.py vault/data/chatgpt-export.zip --source chatgpt-home
   python ../soul.me/tools/extract.py vault/data/claude-export.zip  --source claude-home
   ```

   It keeps only your own messages, only those since the last run, redacts IDs, IBANs, emails, phone numbers and the
   names in `vault/data/denylist.txt` in code, asks each lens in `prompts/lenses.md`, checks every quote, drops what's
   already in your vault or inbox, lets a judge pass rank the rest, and writes the top 12 to `vault/inbox/`.
   The full report and the run state stay in `vault/data/` (never committed).
   Between exports, `python ../soul.me/tools/interview.py vault` asks you five questions where the vault is thin
   (the open `questions:` first). Only your answers are saved, to `vault/data/<date>-interview.md`; run the intake on it
   with `--source self`.
3. **Seal** (manual, about 5 minutes a week): read the inbox file, keep what's true as `[stated]` (drop the `(quote: …)`),
   delete the rest, commit `seal: inbox/<file>`. The `questions:` in the inbox frontmatter are optional prompts for your
   next "how I work" note; the next run asks the lenses about them too.

## Use it (drop-in export, D-013)

```bash
python ../soul.me/tools/export.py vault --profile personal --target system  > /tmp/minime.txt   # local model system prompt
python ../soul.me/tools/export.py vault --profile personal --target chatgpt                     # the two custom-instruction fields
python ../soul.me/tools/export.py vault --profile work --target claude --out ~/soulme-claude    # project files for a work account
```

Only `[stated]` lines inside their validity window leave the vault; `inbox/`, `data/` and `sessions/` never do. `work` leaves out
`people/` and anything not marked `profiles: [work, …]`. If a target has a size limit, whole lines are dropped lowest priority
first (context, procedures, tensions, identity, operating manual last) and listed on stderr: nothing is shortened silently.

## Use it live (MCP server, optional, v4)

One server process per client, so each client gets exactly one profile. Example for Claude Desktop or Claude Code:

```json
{"mcpServers": {"soul": {"command": "python",
  "args": ["/path/to/soul.me/tools/mcp_server.py", "/path/to/soul-vault/vault", "--profile", "personal", "--client", "claude-home"]}}}
```

It serves the same lines as the export (confirmed, inside their validity window, never inbox or sessions; `work` never sees
`people/`). The assistant can `propose` new facts: they land in `inbox/<date>-mcp-<client>.md` for your weekly review, never in a
live file. Add `--read-only` for clients that shouldn't propose at all, e.g. an employer's tenant.

## Weekly curation (v3)

Copy [`templates/vault-curate.yml`](../templates/vault-curate.yml) to `.github/workflows/curate.yml` and allow Actions to open
pull requests (Settings → Actions → General). Every Monday it runs `tools/curate.py --apply` and, if anything changed, opens one PR
on `curate/weekly`: inbox files past 4 weeks and sessions past 14 days deleted, expired lines moved word for word to `# Archive`.
The report is the PR body. Merge to accept, close to reject; your validate Action checks the branch first.
Duplicates and the minime budget need your judgement, so they are listed (in the PR, or in the run summary) but never changed.
Locally: `python ../soul.me/tools/curate.py vault` shows the same report without changing anything.
Contradictions need a model, so they run on your machine, never in the Action: `python ../soul.me/tools/conflicts.py vault`
(same `SOULME_LLM_*` settings as the intake) prints the pairs to look at; paste them into the PR if you like. `## Tensions` is skipped.

## Where the extraction runs (D-016)

Extraction sends your raw material to whichever model runs it. In order of preference:

1. **The same vendor the dump came from.** It already holds that material.
2. **A local model** (e.g. Qwen). Nothing leaves your machine, but quality may be lower; the validator catches format errors.
3. **A Claude Code session attached only to `soul-vault`.**

Never use a session or agent that has this soul.me repo attached. Real vault data must not end up in a public-facing repo,
its PRs or its CI logs.
