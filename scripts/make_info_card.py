#!/usr/bin/env python3
"""
Hand-code a neofetch-style info card SVG: a terminal panel of label/value rows
that fade and slide in one after another, then hold.

The rows come from the "info_card" list in profile.json, so the content is
editable without touching this file. A row with an empty label is a
continuation line, indented to sit under the value above it.

Set STATIC=1 to emit a frozen version with no animation, which is what the
preview page uses.

    python scripts/make_info_card.py [out.svg]
"""
import html
import os
import sys

from config import ROOT, CONFIG, DISPLAY_NAME, SHELL_USER, prompt, BG, BG2, FRAME, TITLE_TEXT, INK

OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "info-card.svg")

ROWS = CONFIG.get("info_card", [])
STATIC = bool(os.environ.get("STATIC"))

LABEL = "#39d353"     # neofetch keys are the accent color
ACCENT = "#22d3ee"
DIM = "#7d8590"

PAD = 22
TITLEBAR_H = 30
LINE_H = 26
HEAD_H = 58           # user@host line plus its underline rule
LABEL_W = 92          # label column width, in px
FONT = 14

# a monospace advance of ~0.6em is close enough to size the panel to its
# longest row without measuring glyphs.
CH = FONT * 0.6
longest = max((len(l) + len(v) for l, v in ROWS), default=40)
ART_W = max(420, int(LABEL_W + longest * CH * 0.72))
CANVAS_W = ART_W + PAD * 2
CANVAS_H = TITLEBAR_H + HEAD_H + len(ROWS) * LINE_H + PAD * 2

# reveal timing: one row after another, then freeze
ROW_DUR = 0.45
STAGGER = 0.13
HEAD_DELAY = 0.25


def row_anim(delay):
    """Fade plus a short slide from the left, played once."""
    if STATIC:
        return ""
    return (f'<animate attributeName="opacity" from="0" to="1" begin="{delay:.2f}s" '
            f'dur="{ROW_DUR:.2f}s" fill="freeze"/>'
            f'<animateTransform attributeName="transform" type="translate" '
            f'from="-10 0" to="0 0" begin="{delay:.2f}s" dur="{ROW_DUR:.2f}s" fill="freeze"/>')


parts = [
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{CANVAS_W}" height="{CANVAS_H}" '
    f'viewBox="0 0 {CANVAS_W} {CANVAS_H}" font-family="ui-monospace, SFMono-Regular, '
    f'Menlo, Consolas, monospace">',
    '<defs><linearGradient id="ibg" x1="0" y1="0" x2="0" y2="1">'
    f'<stop offset="0" stop-color="{BG2}"/><stop offset="1" stop-color="{BG}"/>'
    '</linearGradient></defs>',
    f'<rect width="{CANVAS_W}" height="{CANVAS_H}" rx="12" fill="url(#ibg)"/>',
    f'<rect x="0.5" y="0.5" width="{CANVAS_W-1}" height="{CANVAS_H-1}" rx="12" '
    f'fill="none" stroke="{FRAME}" stroke-width="1"/>',
    f'<line x1="0" y1="{TITLEBAR_H}" x2="{CANVAS_W}" y2="{TITLEBAR_H}" stroke="{FRAME}"/>',
]
for i, dot in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
    parts.append(f'<circle cx="{PAD + i*16}" cy="{TITLEBAR_H/2}" r="5" fill="{dot}"/>')
parts.append(f'<text x="{CANVAS_W/2}" y="{TITLEBAR_H/2 + 4}" fill="{TITLE_TEXT}" font-size="12" '
             f'text-anchor="middle">{html.escape(prompt("~$ neofetch"))}</text>')

# neofetch header: user@host, then a rule the width of that string
head_y = TITLEBAR_H + 34
head_txt = f"{SHELL_USER}@github"
parts.append(f'<g opacity="{1 if STATIC else 0}">'
             f'<text x="{PAD}" y="{head_y}" font-size="{FONT}" font-weight="700" fill="{LABEL}">'
             f'{html.escape(head_txt)}</text>'
             f'{row_anim(HEAD_DELAY)}</g>')
rule_y = head_y + 8
parts.append(f'<g opacity="{1 if STATIC else 0}">'
             f'<line x1="{PAD}" y1="{rule_y}" x2="{PAD + len(head_txt)*CH:.0f}" y2="{rule_y}" '
             f'stroke="{DIM}" stroke-width="1"/>{row_anim(HEAD_DELAY + 0.08)}</g>')

y = TITLEBAR_H + HEAD_H + 14
for i, (label, value) in enumerate(ROWS):
    delay = HEAD_DELAY + 0.3 + i * STAGGER
    parts.append(
        f'<g opacity="{1 if STATIC else 0}">'
        f'<text x="{PAD}" y="{y}" font-size="{FONT}" font-weight="700" fill="{LABEL}">'
        f'{html.escape(label)}</text>'
        f'<text x="{PAD + LABEL_W}" y="{y}" font-size="{FONT}" fill="{INK}">'
        f'{html.escape(value)}</text>'
        f'{row_anim(delay)}</g>'
    )
    y += LINE_H

# a blinking prompt cursor on the last line, so the panel reads as a live shell
cur_y = y - LINE_H + 6
parts.append(f'<text x="{PAD}" y="{cur_y + 14}" font-size="{FONT}" fill="{DIM}">'
             f'{html.escape(SHELL_USER)}@github:~$ </text>')
cur_x = PAD + (len(SHELL_USER) + 12) * CH
blink = "" if STATIC else ('<animate attributeName="opacity" values="1;1;0;0" '
                           'keyTimes="0;0.5;0.51;1" dur="1s" repeatCount="indefinite"/>')
parts.append(f'<rect x="{cur_x:.0f}" y="{cur_y + 2}" width="8" height="15" fill="{ACCENT}">{blink}</rect>')

parts.append("</svg>")
svg = "".join(parts)
with open(OUT, "w", encoding="utf-8") as f:
    f.write(svg)
print("wrote", OUT, len(svg), "bytes;", CANVAS_W, "x", CANVAS_H)
