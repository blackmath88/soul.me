# Test fixtures (fictional)

Everything here is made up: Mara Keller, Nordhafen and every number are fictional, shaped like real exports.

| File | Shape |
|---|---|
| `chatgpt-conversations.json` | ChatGPT export (`mapping` tree, `current_node`), including an edited-away branch that must be ignored |
| `claude-conversations.json` | Claude export (`chat_messages`, `sender: human`), one message with text only in `content[]` |
| `denylist.txt` | the client name the redaction must remove |
| `gold.json` | findings a good model should produce (`expect`) and strings that must never reach the inbox or report (`traps`) |
