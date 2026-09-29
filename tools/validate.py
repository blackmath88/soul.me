#!/usr/bin/env python3
"""Validate a soul.me vault against docs/spec.md.

Usage: python tools/validate.py [vault_dir]   (default: vault)
Prints path:line: message per problem; exits 1 if any.
"""
import datetime
import re
import sys
from pathlib import Path

import yaml

SCOPES = {"always", "global", "project", "session"}
REQUIRED = ("name", "description", "scope", "updated")
SKILL_FIELDS = {"name", "description", "license", "compatibility", "metadata", "allowed-tools"}
MINIME_WORD_BUDGET = 1500

NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
TAG_RE = re.compile(r"\[(stated|inferred|imported:[a-z0-9_-]+)\]")
TAGLIKE_RE = re.compile(r"\[(stated|inferred|imported)[^\]]*\]")
ITEM_RE = re.compile(r"^\s*(?:[-*]|\d+\.)\s+(.*)$")
VALIDITY_RE = re.compile(r"\((valid_from|valid_to):\s*([^)]*)\)")
VALIDITY_DATE_RE = re.compile(r"^\d{4}-\d{2}(-\d{2})?$")


def split_frontmatter(text):
    """Return (frontmatter_text, body_lines, body_start_lineno) or None if missing."""
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        return None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return "\n".join(lines[1:i]), lines[i + 1:], i + 2
    return None


def check_frontmatter(fm, path, rel, errors):
    if path.name == "SKILL.md":
        # Agent Skills spec: only spec fields at top level; soul.me fields live in metadata (D-018)
        extra = set(fm) - SKILL_FIELDS
        if extra:
            errors.append(f"{rel}:1: fields {sorted(extra)} not allowed in SKILL.md; put them under metadata:")
        meta = fm.get("metadata") or {}
        if not isinstance(meta, dict):
            errors.append(f"{rel}:1: metadata must be a mapping")
            meta = {}
        for k, v in meta.items():
            if not isinstance(v, str):
                errors.append(f"{rel}:1: metadata.{k} must be a quoted string, e.g. \"{v}\"")
        fm = {**fm, **{k: str(meta[k]) for k in ("scope", "updated") if k in meta}}

    for key in REQUIRED:
        if key not in fm or fm[key] in (None, ""):
            errors.append(f"{rel}:1: missing frontmatter field '{key}'")

    expected = path.parent.name if path.name == "SKILL.md" else path.stem
    name = fm.get("name")
    if name is not None:
        if not isinstance(name, str) or not NAME_RE.match(name):
            errors.append(f"{rel}:1: name '{name}' must be lowercase letters, digits and hyphens")
        elif name != expected:
            errors.append(f"{rel}:1: name '{name}' must match '{expected}'")

    desc = fm.get("description")
    if isinstance(desc, str) and len(desc) > 1024:
        errors.append(f"{rel}:1: description longer than 1024 characters")

    scope = fm.get("scope")
    if scope is not None and scope not in SCOPES:
        errors.append(f"{rel}:1: scope '{scope}' must be one of {sorted(SCOPES)}")
    if rel == "minime.md" and scope != "always":
        errors.append(f"{rel}:1: minime.md must have scope: always")
    if rel.startswith("sessions/") and scope != "session":
        errors.append(f"{rel}:1: files in sessions/ must have scope: session")

    updated = fm.get("updated")
    # PyYAML parses an unquoted ISO date into a datetime.date
    if updated is not None and not isinstance(updated, datetime.date):
        if not (isinstance(updated, str) and DATE_RE.match(updated)):
            errors.append(f"{rel}:1: updated '{updated}' must be a YYYY-MM-DD date")


def check_body(lines, start, rel, errors):
    in_inbox = rel.startswith("inbox/")
    words = 0
    headings = set()
    for offset, line in enumerate(lines):
        lineno = start + offset
        if not line.strip():
            continue
        if line.lstrip().startswith("#"):
            headings.add(line.strip().lstrip("#").strip().lower())
            continue

        m = ITEM_RE.match(line)
        if not m:
            errors.append(f"{rel}:{lineno}: not a heading or list item; one tagged fact per line")
            continue
        item = m.group(1)

        taglike = TAGLIKE_RE.findall(item)
        tags = TAG_RE.findall(item)
        if len(taglike) != 1:
            errors.append(f"{rel}:{lineno}: needs exactly one provenance tag, found {len(taglike)}")
            continue
        if len(tags) != 1:
            errors.append(f"{rel}:{lineno}: malformed tag; use [stated], [inferred] or [imported:<source>]")
            continue
        if not item.startswith(f"[{tags[0]}]"):
            errors.append(f"{rel}:{lineno}: provenance tag must come first")
        if tags[0] != "stated" and not in_inbox:
            errors.append(f"{rel}:{lineno}: [{tags[0]}] only allowed in inbox/ until confirmed")

        for field, value in VALIDITY_RE.findall(item):
            if not VALIDITY_DATE_RE.match(value.strip()):
                errors.append(f"{rel}:{lineno}: {field} '{value}' must be YYYY-MM or YYYY-MM-DD")

        words += len(TAG_RE.sub("", item).split())
    return words, headings


def validate(vault):
    errors = []
    files = sorted(p for p in vault.rglob("*.md") if "data" not in p.relative_to(vault).parts)
    if not (vault / "minime.md").exists():
        errors.append("minime.md: missing")

    for path in files:
        rel = path.relative_to(vault).as_posix()
        parts = split_frontmatter(path.read_text(encoding="utf-8"))
        if parts is None:
            errors.append(f"{rel}:1: missing frontmatter block (--- ... ---)")
            continue
        fm_text, body, start = parts
        try:
            fm = yaml.safe_load(fm_text) or {}
        except yaml.YAMLError as e:
            errors.append(f"{rel}:1: frontmatter is not valid YAML: {e}")
            continue
        if not isinstance(fm, dict):
            errors.append(f"{rel}:1: frontmatter must be a mapping")
            continue

        check_frontmatter(fm, path, rel, errors)
        words, headings = check_body(body, start, rel, errors)

        if rel == "minime.md":
            for section in ("Identity", "Operating manual"):
                if section.lower() not in headings:
                    errors.append(f"{rel}:1: missing section '# {section}'")
            if words > MINIME_WORD_BUDGET:
                errors.append(f"{rel}:1: {words} words, budget is {MINIME_WORD_BUDGET}")

    return files, errors


if __name__ == "__main__":
    vault = Path(sys.argv[1] if len(sys.argv) > 1 else "vault")
    if not vault.is_dir():
        sys.exit(f"no vault directory at {vault}")
    files, errors = validate(vault)
    for e in errors:
        print(e)
    print(f"{len(files)} files checked, {len(errors)} problems")
    sys.exit(1 if errors else 0)
