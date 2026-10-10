#!/usr/bin/env python3
"""Status mark (brand kit, D-019): the kitsune mask drawn from the vault's own numbers, as an SVG.

Usage: python tools/status.py <vault> [--today YYYY-MM-DD] > status.svg

Grey mask: nothing sealed yet. Colour: at least one [stated] line. Shu seal in the corner: lines wait in inbox/.
The label always says the same thing in words ("12 sealed · 3 to seal"): pictures never replace a label.
Computed from the files, never decorative. Pixel grid and colours copied from brand/brand-kit.html.
"""
import argparse
import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate import counts, validate  # noqa: E402

HALVES = ["........", ".s......", ".ss.....", ".sts....", ".stts...", ".ssssssf", "sssssssf", "sskkssss",
          ".sttssss", ".sssssss", "..ssssss", "...sssss", "....ssss", ".....sss", "......sk", "........"]
MASK = [h + h[::-1] for h in HALVES]
OWN = {"s": "#F1EBDD", "t": "#2FB39D", "f": "#8FF0DC", "k": "#0A0A0B", "d": "#C8BFAA"}      # washi, tama, void
GREY = {"s": "#C3C4BF", "t": "#5F5E5B", "f": "#A2A5A8", "k": "#0A0A0B", "d": "#B9B7B0"}     # the world: greys
SHU, SHU_LO, WASHI = "#E4472B", "#9E2A18", "#F1EBDD"
BG, INK = "#121110", "#C3C4BF"                                                            # koge, shiro


def mask(grey, seal):
    pal = GREY if grey else OWN
    px = {}
    for y, row in enumerate(MASK):
        for x, ch in enumerate(row):
            if ch != ".":
                px[x, y] = pal[ch]
    for y in range(6, 14):                                     # shaded right edge, as in the kit
        x = 15 - max(0, y - 8)
        if px.get((x, y)) == pal["s"]:
            px[x, y] = pal["d"]
    if seal:
        for y in range(12, 16):
            for x in range(12, 16):
                px[x, y] = SHU
        px[13, 13], px[14, 14], px[12, 12] = WASHI, SHU_LO, SHU_LO
    return px


def svg(stated, inbox, scale=2):
    words = f"{stated} sealed" + (f" · {inbox} to seal" if inbox else "")
    px = mask(grey=stated == 0, seal=inbox > 0)
    w, h = 16 * scale + 18 + round(7.3 * len(words)), 16 * scale + 8
    rects = "".join(f'<rect x="{4 + x * scale}" y="{4 + y * scale}" width="{scale}" height="{scale}" fill="{c}"/>'
                    for (x, y), c in sorted(px.items()))
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
            f'shape-rendering="crispEdges" role="img" aria-label="soul.me: {words}">'
            f'<title>soul.me: {words}</title><rect width="{w}" height="{h}" rx="3" fill="{BG}"/>{rects}'
            f'<text x="{16 * scale + 10}" y="{h / 2 + 4:.0f}" fill="{INK}" font-family="ui-monospace,Menlo,monospace" '
            f'font-size="12">{words}</text></svg>\n')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("vault")
    ap.add_argument("--today")
    a = ap.parse_args()
    vault = Path(a.vault)
    today = datetime.date.fromisoformat(a.today) if a.today else None
    files, _ = validate(vault)
    c = counts(vault, files, today)
    sys.stdout.write(svg(c["stated"], c["inbox"]))


if __name__ == "__main__":
    main()
