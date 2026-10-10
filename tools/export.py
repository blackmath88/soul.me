#!/usr/bin/env python3
"""Drop-in export (v2, D-013): turn a vault into text an assistant can use, per profile and target.

Usage:
  python tools/export.py <vault> --profile work|personal --target system|chatgpt [--budget N] [--today YYYY-MM-DD]
  python tools/export.py <vault> --profile work|personal --target claude --out <dir>

What leaves the vault:
  - only [stated] lines from live files; inbox/, data/ and sessions/ are never read for export
  - nothing past its valid_to, nothing before its valid_from
  - files allowed by the profile (D-022): minime.md and skills/ go everywhere; areas/ and topics/ are personal
    unless their frontmatter lists `profiles: [work, personal]` (skills: metadata.profiles: "work personal");
    people/ never goes into the work profile
Targets:
  - system  one prompt for a local model (stdout); --budget caps the whole text
  - chatgpt the two custom-instruction fields (stdout); --budget caps each field (default 1500 chars,
            check the current limit in ChatGPT's settings)
  - claude  project files in --out: core.md, procedures.md, context.md
Over budget, lines are dropped lowest priority first (context, procedures, tensions, identity, operating
manual last) and every dropped line is reported on stderr. Nothing is ever shortened or rewritten.
"""
import argparse
import datetime
import re
import sys
from calendar import monthrange
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate import ITEM_RE, TAG_RE, VALIDITY_RE, split_frontmatter  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
PROFILES = ("work", "personal")
DEFAULT = {"minime.md": PROFILES, "skills": PROFILES, "areas": ("personal",), "topics": ("personal",),
           "people": ("personal",)}


def valid_now(item, today):
    """False if the line's validity window excludes today."""
    for field, value in VALIDITY_RE.findall(item):
        v = value.strip()
        if re.fullmatch(r"\d{4}-\d{2}", v):
            y, m = map(int, v.split("-"))
            start, end = datetime.date(y, m, 1), datetime.date(y, m, monthrange(y, m)[1])
        elif re.fullmatch(r"\d{4}-\d{2}-\d{2}", v):
            start = end = datetime.date.fromisoformat(v)
        else:
            continue
        if field == "valid_to" and today > end:
            return False
        if field == "valid_from" and today < start:
            return False
    return True


def render_line(item):
    """'[stated] (valid_to: 2026-12) Text' -> 'Text (until 2026-12)'."""
    text = TAG_RE.sub("", item, count=1)
    notes = [("since " if f == "valid_from" else "until ") + v.strip() for f, v in VALIDITY_RE.findall(text)]
    text = re.sub(r"\s+", " ", VALIDITY_RE.sub("", text)).strip()
    return text + (f" ({', '.join(notes)})" if notes else "")


def file_profiles(rel, fm):
    top = rel.split("/")[0]
    listed = fm.get("profiles")
    if rel.endswith("SKILL.md"):
        listed = (fm.get("metadata") or {}).get("profiles")
    if isinstance(listed, str):
        listed = listed.replace(",", " ").split()
    allowed = tuple(p for p in (listed or DEFAULT.get(top, ())) if p in PROFILES)
    if top == "people":
        allowed = tuple(p for p in allowed if p != "work")      # D-022: never people/ at work
    return allowed


def collect(vault, profile, today):
    """Read the vault into sections; return (sections, report)."""
    vault = Path(vault)
    report = {"files": 0, "lines": 0, "expired_or_not_yet": 0, "not_stated": 0, "files_excluded_by_profile": []}
    sec = {"identity": [], "manual": [], "tensions": [], "procedures": [], "context": []}
    for p in sorted(vault.rglob("*.md")):
        rel = p.relative_to(vault).as_posix()
        if rel.split("/")[0] in ("inbox", "data", "sessions"):
            continue
        parts = split_frontmatter(p.read_text(encoding="utf-8"))
        if not parts:
            continue
        fm = yaml.safe_load(parts[0]) or {}
        if rel != "minime.md" and rel.split("/")[0] not in DEFAULT:
            continue
        if profile not in file_profiles(rel, fm):
            report["files_excluded_by_profile"].append(rel)
            continue
        report["files"] += 1
        top, heading, raw, lines = "", "", "", []
        for line in parts[1]:
            if line.lstrip().startswith("#"):
                raw = line.strip().lstrip("#").strip()
                heading = raw.lower()
                if not line.lstrip().startswith("##"):
                    top = heading
                continue
            m = ITEM_RE.match(line)
            if not m:
                continue
            item = m.group(1)
            tag = TAG_RE.match(item)
            if not tag or tag.group(1) != "stated":
                report["not_stated"] += 1
                continue
            if not valid_now(item, today):
                report["expired_or_not_yet"] += 1
                continue
            report["lines"] += 1
            lines.append(((top, heading, raw), render_line(item)))
        if rel == "minime.md":
            for (top, h, raw), t in lines:
                key = "tensions" if "tension" in h else "manual" if "operating manual" in top else "identity"
                # keep the sub-heading's meaning: "What I push back on: frameworks nobody uses"
                sub = raw if h and h != top and key != "tensions" else ""
                sec[key].append(f"{sub}: {t}" if sub else t)
        elif rel.startswith("skills/"):
            name = p.parent.name
            sec["procedures"].append(f"{name}: {fm.get('description', '')}".strip())
            sec["procedures"] += [f"  {i}. {t}" for i, (_, t) in enumerate(lines, 1)]
        else:
            sec["context"].append(f"{p.stem}: {fm.get('description', '')}".strip())
            sec["context"] += [f"  - {t}" for _, t in lines]
    return sec, report


ORDER = ["manual", "identity", "tensions", "procedures", "context"]        # highest priority first
TITLES = {"identity": "Who I am", "manual": "How to work with me", "tensions": "Tensions (both are true)",
          "procedures": "Procedures I use", "context": "Current context"}


def as_text(blocks):
    out = []
    for key, lines in blocks:
        if lines:
            out += [f"## {TITLES[key]}", *[l if l.startswith("  ") else f"- {l}" for l in lines], ""]
    return "\n".join(out).strip() + "\n"


def fit(blocks, budget, dropped):
    """Drop whole lines, lowest priority section first, last line first, until the text fits."""
    blocks = [(k, list(v)) for k, v in blocks]
    while budget and len(as_text(blocks)) > budget:
        for k, v in sorted(blocks, key=lambda b: -ORDER.index(b[0])):
            if v:
                dropped.append((k, v.pop()))
                break
        else:
            break
    return blocks


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("vault")
    ap.add_argument("--profile", required=True, choices=PROFILES)
    ap.add_argument("--target", required=True, choices=("system", "chatgpt", "claude"))
    ap.add_argument("--budget", type=int, help="characters (system: whole text; chatgpt: per field, default 1500)")
    ap.add_argument("--out", help="folder for --target claude")
    ap.add_argument("--today", help="YYYY-MM-DD, for validity windows (default: today)")
    a = ap.parse_args()
    today = datetime.date.fromisoformat(a.today) if a.today else datetime.date.today()
    sec, report = collect(a.vault, a.profile, today)
    dropped = []
    head = f"(soul.me export · profile {a.profile} · {today.isoformat()} · only lines the person confirmed)"

    if a.target == "system":
        blocks = fit([(k, sec[k]) for k in ["identity", "manual", "tensions", "procedures", "context"]], a.budget, dropped)
        sys.stdout.write(f"# About the person you are working with\n{head}\n\n" + as_text(blocks))
    elif a.target == "chatgpt":
        budget = a.budget or 1500
        about = fit([("identity", sec["identity"]), ("tensions", sec["tensions"]), ("context", sec["context"])], budget, dropped)
        how = fit([("manual", sec["manual"]), ("procedures", sec["procedures"])], budget, dropped)
        sys.stdout.write("=== What would you like ChatGPT to know about you? ===\n" + as_text(about) +
                         "\n=== How would you like ChatGPT to respond? ===\n" + as_text(how))
    else:
        if not a.out:
            sys.exit("--target claude needs --out <dir>")
        out = Path(a.out).resolve()
        if out == REPO or REPO in out.parents:
            sys.exit(f"refusing to write inside the soul.me repo ({out}); choose a folder outside it")
        out.mkdir(parents=True, exist_ok=True)
        files = {"core.md": [("identity", sec["identity"]), ("manual", sec["manual"]), ("tensions", sec["tensions"])],
                 "procedures.md": [("procedures", sec["procedures"])], "context.md": [("context", sec["context"])]}
        for name, blocks in files.items():
            if any(v for _, v in blocks):
                (out / name).write_text(f"# soul.me · {name[:-3]}\n{head}\n\n" + as_text(blocks), encoding="utf-8")
        print(f"wrote {', '.join(n for n, b in files.items() if any(v for _, v in b))} to {out}")

    r = report
    print(f"export: profile {a.profile}, {r['files']} files, {r['lines']} lines; skipped {r['expired_or_not_yet']} "
          f"outside their validity window, {r['not_stated']} not [stated], {len(r['files_excluded_by_profile'])} files "
          f"not in this profile; {len(dropped)} lines dropped for the budget", file=sys.stderr)
    for k, line in dropped:
        print(f"  dropped ({TITLES[k]}): {line.strip()}", file=sys.stderr)


if __name__ == "__main__":
    main()
