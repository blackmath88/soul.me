#!/usr/bin/env python3
"""Convert a ChatGPT data export into one markdown file per conversation, for local review and extraction.

Usage: python tools/chatgpt_export.py <export_dir> <out_dir>

Runs on your own machine, inside your private vault repo (D-015/D-016). It reads ONLY the conversation
shards (conversations*.json) and the two asset-name maps (D-021); account files such as user.json are never
opened. out_dir must not be inside this repo: real data never lands here.

Per conversation it follows the active branch (current_node -> parents), keeps user and assistant text
(assistant cut to 600 chars), stubs user turns over 2,000 chars as pasted material (D-020), resolves
attachments to their original names, and keeps the conversation only if the person wrote at least 2 turns
and 300 characters of their own (pasted stubs don't count). Writes <date>_<slug>_<id8>.md and _stats.json.
"""
import datetime
import json
import re
import sys
import unicodedata
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ASSET_MAPS = ("conversation_asset_file_names.json", "library_files.json")
PASTE_LIMIT = 2000
ASSISTANT_LIMIT = 600
MIN_USER_TURNS = 2
MIN_AUTHORED = 300
TEXT_TYPES = ("text", "multimodal_text")   # skips code, execution_output, thoughts, user_editable_context …


def refuse_repo_output(path):
    """Real data must never land in this repo."""
    p = Path(path).resolve()
    if p == REPO or REPO in p.parents:
        sys.exit(f"refusing to write inside the soul.me repo ({p}); choose a folder in your private vault, "
                 f"e.g. ../soul-vault/vault/data/chatgpt")


# ---------- reading: the allowlist (D-021) ----------

def shard_paths(export_dir):
    paths = sorted(Path(export_dir).glob("conversations*.json"))
    if not paths:
        sys.exit(f"no conversations*.json in {export_dir}")
    return paths


def read_conversations(export_dir):
    convs = []
    for p in shard_paths(export_dir):
        data = json.loads(p.read_text(encoding="utf-8"))
        convs += data if isinstance(data, list) else data.get("conversations", [])
    return convs


def read_asset_names(export_dir):
    """asset id -> original filename, from the two maps; unknown schemas are read defensively."""
    names = {}

    def name_of(v):
        if isinstance(v, str):
            return v
        if isinstance(v, dict):
            for k in ("name", "file_name", "filename", "original_name", "title"):
                if isinstance(v.get(k), str):
                    return v[k]
        return None

    for fname in ASSET_MAPS:
        p = Path(export_dir) / fname
        if not p.exists():
            continue
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict):
            items = data.items()
        elif isinstance(data, list):
            items = []
            for d in data:
                if isinstance(d, dict):
                    key = next((d[k] for k in ("id", "file_id", "asset_id", "library_file_id") if isinstance(d.get(k), str)), None)
                    if key:
                        items.append((key, d))
        else:
            items = []
        for key, v in items:
            n = name_of(v)
            if n:
                names[re.sub(r"\.dat$", "", key)] = n
    return names


def resolve_asset(pointer, names):
    """file-service://file-ABC -> 'file-ABC'; sediment://file_000… -> 'file_000…'; then look it up."""
    aid = re.sub(r"^[a-z-]+://", "", pointer or "")
    if aid in names:
        return names[aid]
    for key, n in names.items():        # dat names may carry a suffix after the id
        if aid and key.startswith(aid):
            return n
    return None


# ---------- the active branch ----------

def active_path(conv):
    mapping = conv.get("mapping") or {}
    node = conv.get("current_node")
    if node not in mapping:             # no current_node: fall back to the newest leaf
        leaves = [n for n, v in mapping.items() if not v.get("children")]
        node = max(leaves, key=lambda n: ((mapping[n].get("message") or {}).get("create_time") or 0), default=None)
    out = []
    while node and node in mapping:
        out.append(mapping[node])
        node = mapping[node].get("parent")
    return list(reversed(out))


def stamp(ts, fallback=None):
    ts = ts if isinstance(ts, (int, float)) else fallback
    if not isinstance(ts, (int, float)):
        return None
    return datetime.datetime.fromtimestamp(ts, datetime.timezone.utc)


def turns(conv, names):
    """Visible user/assistant turns on the active branch: [{role, text, authored, pasted, when}]."""
    out = []
    for node in active_path(conv):
        msg = node.get("message") or {}
        role = (msg.get("author") or {}).get("role")
        content = msg.get("content") or {}
        if role not in ("user", "assistant") or content.get("content_type") not in TEXT_TYPES:
            continue
        if (msg.get("metadata") or {}).get("is_visually_hidden_from_conversation"):
            continue
        pieces, attach = [], []
        for part in content.get("parts") or []:
            if isinstance(part, str):
                pieces.append(part)
            elif isinstance(part, dict) and part.get("asset_pointer"):
                n = resolve_asset(part["asset_pointer"], names)
                attach.append(f"[attachment: {n}]" if n else "[attachment]")
            elif isinstance(part, dict) and isinstance(part.get("text"), str):
                pieces.append(part["text"])
        text = "\n".join(p for p in pieces if p).strip()
        when = stamp(msg.get("create_time"), conv.get("create_time"))
        authored = pasted = 0
        if role == "user":
            if len(text) > PASTE_LIMIT:
                pasted = len(text)
                head = re.sub(r"\s+", " ", text[:120]).strip()
                text = f'[pasted: {len(text):,} chars, starts "{head}…"]'
            else:
                authored = len(text)
        elif len(text) > ASSISTANT_LIMIT:
            text = text[:ASSISTANT_LIMIT].rstrip() + "…"
        text = "\n".join(attach + ([text] if text else []))
        if text:
            out.append({"role": role, "text": text, "authored": authored, "pasted": pasted, "when": when})
    return out


# ---------- writing ----------

def slug(title):
    t = unicodedata.normalize("NFKD", (title or "").replace("ß", "ss")).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")[:50].strip("-") or "untitled"


def render(conv, ts, date):
    user = [t for t in ts if t["role"] == "user"]
    lines = [f"# {conv.get('title') or 'Untitled'}", "",
             f"date: {date} · id: {conv.get('id') or conv.get('conversation_id')} · user turns: {len(user)} · "
             f"authored: {sum(t['authored'] for t in user):,} chars · pasted: {sum(t['pasted'] for t in user):,} chars", ""]
    for t in ts:
        when = t["when"].strftime(" · %Y-%m-%d %H:%M") if t["when"] and t["role"] == "user" else ""
        lines += [f"## {t['role']}{when}", "", t["text"], ""]
    return "\n".join(lines)


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    export_dir, out_dir = Path(sys.argv[1]), Path(sys.argv[2])
    refuse_repo_output(out_dir)
    names = read_asset_names(export_dir)
    convs = read_conversations(export_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    stats = {"inputs": [p.name for p in shard_paths(export_dir)] + [m for m in ASSET_MAPS if (export_dir / m).exists()],
             "conversations": len(convs), "kept": 0,
             "skipped": {"fewer_than_2_user_turns": 0, "under_300_authored_chars": 0},
             "date_range": None, "kept_per_year": {},
             "chars": {"authored": 0, "pasted": 0, "authored_kept": 0, "pasted_kept": 0}, "top_20_by_authored": []}
    used, kept_rows, dates = set(), [], []
    for conv in convs:
        ts = turns(conv, names)
        user = [t for t in ts if t["role"] == "user"]
        authored, pasted = sum(t["authored"] for t in user), sum(t["pasted"] for t in user)
        stats["chars"]["authored"] += authored
        stats["chars"]["pasted"] += pasted
        if len(user) < MIN_USER_TURNS:
            stats["skipped"]["fewer_than_2_user_turns"] += 1
            continue
        if authored < MIN_AUTHORED:
            stats["skipped"]["under_300_authored_chars"] += 1
            continue
        created = stamp(conv.get("create_time")) or next((t["when"] for t in ts if t["when"]), None)
        date = created.strftime("%Y-%m-%d") if created else "0000-00-00"
        cid = str(conv.get("id") or conv.get("conversation_id") or "noid")
        name = f"{date}_{slug(conv.get('title'))}_{cid[:8]}.md"
        k = 2
        while name in used:              # same date, title and id prefix: never overwrite
            name = f"{date}_{slug(conv.get('title'))}_{cid[:8]}-{k}.md"
            k += 1
        used.add(name)
        (out_dir / name).write_text(render(conv, ts, date), encoding="utf-8")
        stats["kept"] += 1
        stats["chars"]["authored_kept"] += authored
        stats["chars"]["pasted_kept"] += pasted
        stats["kept_per_year"][date[:4]] = stats["kept_per_year"].get(date[:4], 0) + 1
        dates.append(date)
        kept_rows.append({"file": name, "title": conv.get("title") or "", "authored": authored})
    stats["date_range"] = [min(dates), max(dates)] if dates else None
    stats["top_20_by_authored"] = sorted(kept_rows, key=lambda r: -r["authored"])[:20]
    (out_dir / "_stats.json").write_text(json.dumps(stats, ensure_ascii=False, indent=1), encoding="utf-8")
    total = stats["chars"]["authored"] + stats["chars"]["pasted"]
    share = f"{100 * stats['chars']['pasted'] / total:.0f}%" if total else "n/a"
    print(f"{stats['conversations']} conversations, kept {stats['kept']}, skipped {sum(stats['skipped'].values())} "
          f"{stats['skipped']}; pasted share of user chars: {share}; written to {out_dir}")


if __name__ == "__main__":
    main()
