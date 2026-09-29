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

## Where the extraction runs (D-016)

Extraction sends your raw material to whichever model runs it. In order of preference:

1. **The same vendor the dump came from.** It already holds that material.
2. **A local model** (e.g. Qwen). Nothing leaves your machine, but quality may be lower; the validator catches format errors.
3. **A Claude Code session attached only to `soul-vault`.**

Never use a session or agent that has this soul.me repo attached. Real vault data must not end up in a public-facing repo,
its PRs or its CI logs.
