# Extraction prompt: raw material → inbox

Turns one raw source (a memory dump, a self-written note, an interview transcript) into one
`inbox/` file that passes `tools/validate.py`. Run it once per source. Replace the three
`{placeholders}` before pasting.

- `{source}`: lowercase short name used in the tag, e.g. `self`, `chatgpt`, `claude`, `copilot-work`
- `{date}`: today, `YYYY-MM-DD`
- `{raw}`: the source text

Save the answer as `vault/inbox/{date}-{source}.md` and run the validator. If it fails, fix the
lines by hand or paste the errors back and ask for a corrected file.

## Prompt

````text
You are converting raw notes about a person into lines for their personal knowledge vault.
The person reviews every line afterwards. Your job is faithful sorting, not writing.

Output ONE markdown file and nothing else, in exactly this shape:

---
name: {date}-{source}
description: unreviewed lines extracted from {source} on {date}
scope: global
updated: {date}
dropped: {}
---
## → minime.md: Identity
- [imported:{source}] ...
## → minime.md: Operating manual
- [imported:{source}] ...
## → minime.md: Tensions
## → skills/<procedure-name>
## → areas/<involvement-name>.md
## → people/<first-last>.md
## → topics/<domain>.md

Rules:
1. Every non-heading line is a list item starting with exactly one tag, then the fact.
   Use [imported:{source}] for things the person said or wrote ("[told]" in a dump, or anything
   in a self-written note). Use [inferred] for things a model concluded ("[concluded]" in a dump)
   and for anything you are unsure the person actually said.
2. One fact per line, short, in the third person for Identity and as an instruction to the
   assistant for Operating manual ("Lead with the answer, then the reasoning").
3. Anything that can expire gets a validity marker right after the tag:
   (valid_from: YYYY-MM) or (valid_to: YYYY-MM). Use "last seen" dates as valid_from only if nothing better exists.
4. Don't invent, merge away or soften anything. Keep contradictions; put them under Tensions.
5. Procedures: one heading per procedure, steps as numbered items, each step tagged.
6. People: role in relation to the person only. No personal details about them.
7. Never copy government or financial identifiers, health information, passwords, or sensitive
   details about other people. Record only the category and a count in the frontmatter,
   e.g. dropped: {health: 1, other-people: 2}. Never the content itself.
8. Leave out any heading that would have no lines.
9. No other text before or after the file: no tables, no paragraphs, no code fences.

Raw material from {source}:
<<<
{raw}
>>>
````

## After extraction

Review happens in your vault, not in the assistant:

1. Move each line you agree with into the target file and change its tag to `[stated]`. Reword it if needed; it's yours now.
2. Delete lines you don't agree with. `[inferred]` lines are never promoted just because they sound right.
3. The inbox file is gone when you're done, or it expires after 4 weeks (D-012).
