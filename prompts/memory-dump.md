# Memory dump prompt

Paste this into an assistant you use **with a personal account**. Save its answer as
`vault/data/<date>-<source>-dump.md` in your own vault (never in this repo). That file is raw material;
`extract.md` turns it into inbox lines.

**Don't use this in an employer tenant.** Check your employer's policy first, then use [`sanitise.md`](sanitise.md) instead (D-014).

## Vendor notes

| Vendor | Where it looks | Tip |
|---|---|---|
| ChatGPT | saved memories + chat history reference | Settings → Personalization → Memory lists saved items; paste that list below the answer too |
| Claude | memory + past chats | Claude also has an official export flow for memory ([help article](https://support.claude.com/en/articles/12123587-import-and-export-your-memory-from-claude)); this prompt asks for the same content, plus where each item came from |
| Other (Gemini, Copilot personal, …) | whatever it retains | run as is; if it says it has no memory, stop there |

## Prompt

```text
I'm moving my context into a file I own. List everything you know or have concluded about me
from your memory and our past conversations. Don't add anything new and don't summarise it away.

Output a markdown list, one item per line, grouped under these headings:
## Identity (role, work, background, location, languages)
## How I like to work with you (format, tone, length, language, planning style, what I push back on)
## Ongoing projects and responsibilities (with dates or time frames if known)
## Recurring procedures (things I do repeatedly, step by step if you know them)
## Tools and setup
## People (only their role in relation to me; no personal details about them)
## Other

Start every line with exactly one of:
[told]     – I said this to you directly
[concluded] – you inferred it from how I behave or what I asked about
Then add (last seen: YYYY-MM) if you know roughly when it came up.

Leave out: government or financial identifiers, health information, and anything sensitive
about other people. If you're unsure whether something is still true, keep it and say so.
```

`[told]` and `[concluded]` aren't soul.me tags on purpose. The extraction step maps them to
`[imported:<source>]` and `[inferred]`, so nothing in a raw dump can pass as a vault line.
