#!/usr/bin/env python3
"""Weekly curation report (v3, first cut): what needs the person's attention. Read-only: it never edits the vault.

Usage: python tools/curate.py <vault> [--today YYYY-MM-DD] [--apply]

Prints a markdown report (meant as the body of the weekly curation PR) with:
  - inbox files past 4 weeks (D-012), counted from `released:` in their frontmatter if present (D-027), else `updated:`
  - sessions past 14 days
  - live [stated] lines past their valid_to, to move to an `# Archive` section (D-017), never to delete
  - near-duplicate [stated] lines across live files
  - minime.md against its word budget
Contradictions need judgement and are not detected here.

--apply makes the mechanical changes, for the weekly Action to put in one PR the person merges or closes:
deletes the old inbox files (D-012) and sessions, and moves expired lines to `# Archive` in the same file (D-017),
word for word. Duplicates and the minime budget need judgement and stay report-only. Never runs a model.
"""
import argparse
import datetime
import re
import sys
from calendar import monthrange
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate import ITEM_RE, MINIME_WORD_BUDGET, TAG_RE, VALIDITY_RE, check_body, split_frontmatter  # noqa: E402

STOP = set("the a an and or of to in on for with is are was be it its this that as at by from not no "
           "i me my you your they them their he she his her".split())


def as_date(v):
    if isinstance(v, datetime.date):
        return v
    if isinstance(v, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", v):
        return datetime.date.fromisoformat(v)
    return None


def end_of(v):
    v = v.strip()
    if re.fullmatch(r"\d{4}-\d{2}", v):
        y, m = map(int, v.split("-"))
        return datetime.date(y, m, monthrange(y, m)[1])
    return as_date(v)


def tokens(s):
    return {w for w in re.findall(r"[a-zäöüéèàß0-9]+", s.lower()) if len(w) > 2 and w not in STOP}


def jaccard(a, b):
    a, b = tokens(a), tokens(b)
    return len(a & b) / len(a | b) if a and b else 0.0


def archive(path, idx, today):
    """Move body lines idx (0-based, after the frontmatter) under `# Archive`, unchanged; bump `updated`."""
    lines = path.read_text(encoding="utf-8").split("\n")
    start = split_frontmatter("\n".join(lines))[2] - 1          # first body line
    moved = [lines[start + i] for i in idx]
    for i in reversed(idx):
        del lines[start + i]
    head = next((k for k in range(start, len(lines)) if re.fullmatch(r"#+\s*archive\s*", lines[k].strip(), re.I)), None)
    if head is None:
        while lines and not lines[-1].strip():
            lines.pop()
        lines += ["", "# Archive", *moved, ""]
    else:
        lines[head + 1:head + 1] = moved
    for k in range(1, start - 1):                                 # frontmatter: updated / metadata.updated
        m = re.match(r'^(\s*updated:\s*)("?)\d{4}-\d{2}-\d{2}("?)\s*$', lines[k])
        if m:
            lines[k] = f"{m.group(1)}{m.group(2)}{today.isoformat()}{m.group(3)}"
            break
    path.write_text("\n".join(lines), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("vault")
    ap.add_argument("--today")
    ap.add_argument("--apply", action="store_true", help="delete old inbox files and sessions, archive expired lines")
    a = ap.parse_args()
    vault = Path(a.vault)
    today = datetime.date.fromisoformat(a.today) if a.today else datetime.date.today()

    old_inbox, old_sessions, expired, live = [], [], [], []
    to_archive = {}                                  # path -> body line indexes
    inbox_lines = 0
    for p in sorted(vault.rglob("*.md")):
        rel = p.relative_to(vault).as_posix()
        top = rel.split("/")[0]
        if top == "data":
            continue
        text = p.read_text(encoding="utf-8")
        parts = split_frontmatter(text)
        fm = (yaml.safe_load(parts[0]) if parts else None) or {}
        body = parts[1] if parts else []
        if top == "inbox":
            n = sum(1 for l in body if ITEM_RE.match(l))
            inbox_lines += n
            since = as_date(fm.get("released")) or as_date(fm.get("updated"))
            if since and (today - since).days > 28:
                old_inbox.append((rel, (today - since).days, n, "released" if fm.get("released") else "updated"))
            continue
        if top == "sessions":
            d = as_date(p.stem[:10])
            if d and (today - d).days > 14:
                old_sessions.append((rel, (today - d).days))
            continue
        in_archive = False
        for i, line in enumerate(body):
            if line.lstrip().startswith("#"):
                in_archive = "archive" in line.lower()
                continue
            m = ITEM_RE.match(line)
            if not m or not m.group(1).startswith("[stated]"):
                continue
            item = m.group(1)
            clean = re.sub(r"\s+", " ", VALIDITY_RE.sub("", TAG_RE.sub("", item, count=1))).strip()
            if not in_archive:
                for field, value in VALIDITY_RE.findall(item):
                    end = end_of(value)
                    if field == "valid_to" and end and today > end:
                        expired.append((rel, clean, value.strip()))
                        to_archive.setdefault(p, []).append(i)
                live.append((rel, clean))

    dupes = []
    for i in range(len(live)):
        for j in range(i + 1, len(live)):
            if jaccard(live[i][1], live[j][1]) >= 0.7:
                dupes.append((live[i], live[j]))

    words = 0
    mp = vault / "minime.md"
    if mp.exists():
        parts = split_frontmatter(mp.read_text(encoding="utf-8"))
        if parts:
            words, _ = check_body(parts[1], parts[2], "minime.md", [])

    if a.apply:
        for rel, *_ in old_inbox + old_sessions:
            (vault / rel).unlink()
        for p, idx in to_archive.items():
            archive(p, sorted(set(idx)), today)

    done = " (applied in this PR)" if a.apply else ""
    out = [f"# Curation report · {today.isoformat()}", ""]
    out += [f"**Inbox:** {inbox_lines} lines waiting. **minime.md:** {words} of {MINIME_WORD_BUDGET} words.", ""]

    def section(title, rows, empty):
        out.append(f"## {title}")
        out.extend(rows or [f"- {empty}"])
        out.append("")
    section(f"Inbox files past 4 weeks (D-012): review or let them go{' · deleted' + done if done else ''}",
            [f"- `{r}`: {d} days since {k}, {n} lines" for r, d, n, k in old_inbox], "none")
    section(f"Sessions past 14 days: prune{' · deleted' + done if done else ''}",
            [f"- `{r}`: {d} days old" for r, d in old_sessions], "none")
    section(f"Facts past valid_to: move to `# Archive` in the same file (D-017), don't delete{' · moved' + done if done else ''}",
            [f"- `{r}`: {t} (valid_to {v})" for r, t, v in expired], "none")
    section("Possible duplicates: merge or keep both",
            [f"- `{a[0]}`: {a[1]}\n  `{b[0]}`: {b[1]}" for a, b in dupes], "none")
    if words > MINIME_WORD_BUDGET:
        section("minime.md over budget", [f"- {words} words; budget {MINIME_WORD_BUDGET}: move detail to areas/ or topics/"], "")
    sys.stdout.write("\n".join(out))


if __name__ == "__main__":
    main()
