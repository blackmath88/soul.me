# Intake: map (one chunk × one lens)

Used by `tools/extract.py`. The script fills the `{placeholders}` and asks for JSON that matches a schema;
the model never writes markdown. Edit the wording freely, but keep the placeholders and the `TASK:` line.

## Prompt

```text
TASK: map
You read messages a person wrote to AI assistants and answer one question about that person.

Lens: {lens}
Question: {question}

What their vault already says (don't repeat it; report only what is new, different or contradicting):
{vault}

Open questions from earlier runs (answer them if these messages can):
{gaps}

Rules:
- Use only the messages below. Every finding needs a quote copied exactly, word for word, from one message (5 to 25 words), and that message's id.
- kind: "told" if the person states it about themselves; "pattern" if it shows across several messages; "concluded" if you infer it.
- One fact per finding, short, in the third person ("Prefers short answers").
- valid_from / valid_to: "YYYY-MM" only if the messages show when it started or ends, otherwise null.
- Skip health, money amounts, account numbers, IDs, passwords and private details of other people. Text like <redacted:email> was removed on purpose; never guess it.
- If nothing qualifies, return {"findings": []}.

Messages (each starts with [message-id | date]):
<<<
{chunk}
>>>
```
