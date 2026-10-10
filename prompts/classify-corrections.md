# Classify corrections: short replies → Operating-manual candidates

For a **local model** (e.g. Qwen) on your own machine, inside your private vault repo (D-015/D-016).
Input: lines from `tools/chatgpt_corrections.py` (`{conv_id, date, title, user, prev_assistant, hint}`).
Output: one inbox file that passes `tools/validate.py`. Nothing here is a fact until you seal it.

**How to run it**
- Paste batches of about 80–150 JSONL lines, the size depends on your model's context. `hint` is only a keyword hint: judge every line.
- For the 2nd and later batches, paste the candidates from the previous output into `{previous}`. The model then
  merges into them and adds up `seen`, so the last batch's output holds the whole picture.
- Replace `{date}`, `{batch}` (e.g. `1 of 4`), `{previous}` (or `none`) and `{lines}`, save the answer as
  `vault/inbox/{date}-chatgpt-corrections.md`, and run the validator.

## Prompt

````text
You read short replies a person typed right after an AI assistant answered them, with the assistant's
previous answer for context. Most are throwaway ("thanks"), some correct one answer, and a few reveal how
this person always wants assistants to work. Your job is to find those few.

Step 1: label every line as exactly one of:
- preference: a stable instruction about HOW to work with this person: length, format, tone, language,
  structure, what to leave out. It would still apply in a different conversation next month.
- one-off: about this particular task or content only ("move the welcome before the agenda").
- noise: thanks, acknowledgements, typos, anything without an instruction.
When unsure between preference and one-off, choose one-off.

Step 2: merge the preference lines that say the same thing, across languages (German and English count as
the same preference), and across this batch and the previous candidates below. For each merged candidate
count the DISTINCT conv_id values it appeared in, and add up the previous counts.

Step 3: output ONE markdown file and nothing else, in exactly this shape:

---
name: {date}-chatgpt-corrections
description: Operating-manual candidates from short corrections in the ChatGPT export, batch {batch}
scope: global
updated: {date}
labels: {preference: <n>, one-off: <n>, noise: <n>}
---
## → minime.md: Operating manual
- [imported:chatgpt-home] (seen: <distinct conversations>) <the preference as an instruction to an assistant>

Rules:
- Each line is an instruction to an assistant, in English, imperative, short: "Lead with one recommendation, not options."
- Order the lines by seen, highest first. A preference seen in only 1 conversation still counts, but keep it if it is stable.
- Never copy names of clients, colleagues or projects, numbers, or anything private into a line. Write the
  pattern, not the content ("No bullet points in sponsor updates", not the sponsor's name).
- The labels line counts this batch only.
- No other text before or after the file, and no code fences.

Previous candidates (merge into these and keep their seen counts):
{previous}

Lines (JSONL):
<<<
{lines}
>>>
````

## Worked example (fictional)

[`examples/mara-corrections.jsonl`](examples/mara-corrections.jsonl) is the real output of
`tools/chatgpt_corrections.py` on the fictional export in `tests/fixtures/chatgpt-mara/`.
[`examples/mara-corrections-inbox.md`](examples/mara-corrections-inbox.md) applies this prompt by hand:

| Line | Label | Why |
|---|---|---|
| "Kürzer bitte, und ohne Einleitung." | preference | length and no intro: holds in any conversation |
| "Again: lead with the recommendation, then the steps…" | preference | structure; "under ten lines" is a one-off detail and is left out |
| "Don't add icebreakers, I never use them with this group…" | one-off | about workshop content for one group, not about how to work with an assistant |
| "…Summarise both in my weekly format, shorter than last time…" | preference | shorter again; open decisions first is part of her weekly-note format, a skill rather than the manual |
| "Shorter, and don't use bullet points in sponsor updates." | preference | two: shorter, and a format rule for one recurring document type |
| "Nicht drei Optionen, nur eine Empfehlung bitte." | preference | one recommendation, not options; same as "lead with the recommendation" |
| "Thanks, perfect." | noise | |

"Shorter" is seen in 3 distinct conversations (Retro format, Weekly notes, New chat aa11…), and
"one recommendation first" in 2 (Retro format, New chat bb22…).
