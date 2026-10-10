"""Terminal colour by the brand's one rule (D-019): grey is the world, colour is yours, shu red is the seal.

Only three roles exist: `world` for everything not yet yours (hints, paths), `own` for sealed counts, `seal` for
what waits for your hand. Off when the stream isn't a terminal or NO_COLOR is set (https://no-color.org).
"""
import os
import sys

ROLES = {"world": (122, 123, 124), "own": (143, 240, 220), "seal": (228, 71, 43)}   # namari, kitsunebi, shu


def paint(text, role, stream=sys.stderr):
    if os.environ.get("NO_COLOR") or not getattr(stream, "isatty", lambda: False)():
        return text
    r, g, b = ROLES[role]
    return f"\033[38;2;{r};{g};{b}m{text}\033[0m"


def next_step(*commands, stream=sys.stderr):
    """The one line every tool ends with: what to run or do next, in grey."""
    for c in commands:
        print(paint(f"next: {c}", "world", stream), file=stream)


def cmd(tool, *args):
    """`python <path to tool> args`, with the path as the person would type it from where they are."""
    full = os.path.join(os.path.dirname(os.path.abspath(__file__)), tool)
    path = os.path.relpath(full)
    path = full if path.startswith(os.path.join("..", "..")) else path     # ../soul.me/tools/x.py yes, ../../../ no
    return " ".join(["python", path, *map(str, args)])


def seal_hint(path):
    rel = "/".join(str(path).replace(os.sep, "/").split("/")[-2:])
    return f"read {rel}, move what's true into live files as [stated], delete the rest, commit `seal: {rel}`"


def vault_of(path):
    """<vault>/data/... -> <vault>, for hints; a placeholder when the path isn't inside a vault's data/."""
    parts = os.path.abspath(path).split(os.sep)
    if "data" not in parts:
        return "<vault>"
    full = os.sep.join(parts[:len(parts) - parts[::-1].index("data") - 1])
    rel = os.path.relpath(full)
    return full if rel.startswith(os.path.join("..", "..")) else rel
