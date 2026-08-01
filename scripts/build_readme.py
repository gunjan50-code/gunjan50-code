#!/usr/bin/env python3
"""
Generate README.md from profile.json.

The README is plain HTML-in-markdown on purpose. GitHub sanitizes READMEs hard:
no <script>, no inline style= worth relying on, no JS at all. What survives is
centered <div>s, a <table> for the two-up hero, <img> (which *does* run SVG SMIL
and CSS animations), and shields.io badges. Everything animated lives inside the
committed SVGs.

    python scripts/build_readme.py
"""
import os
import re
import urllib.parse

from config import ROOT, CONFIG, DISPLAY_NAME, ROLE_LINE, LINKS, SHELL_USER

# what fills the right half of the hero: "info_card", "wordmark", or "none"
# ("none" centres the portrait on its own).
HERO_RIGHT = CONFIG.get("hero_right", "info_card")

RIGHT_PANEL = {
    "info_card": ("info-card.svg", (464.0, 340.0), "Profile info card"),
    "wordmark": ("wordmark.svg", (486.0, 387.0), "3D ASCII wordmark"),
}

OUT_PATH = os.path.join(ROOT, "README.md")

# The two hero panels sit in one table row, so a height mismatch shows up as
# dead space under the shorter one. Their aspect ratios depend on the photo crop
# and on how many letters the wordmark has, so the widths are solved for rather
# than hard-coded: split HERO_W between them such that both render the same
# height. The heatmap below then spans exactly that width.
HERO_W = 860


def svg_size(name, fallback):
    """(width, height) from an SVG's root attributes, or fallback if not built yet."""
    path = os.path.join(ROOT, name)
    if not os.path.exists(path):
        return fallback
    head = open(path, encoding="utf-8").read(600)
    w = re.search(r'\bwidth="([\d.]+)"', head)
    h = re.search(r'\bheight="([\d.]+)"', head)
    return (float(w.group(1)), float(h.group(1))) if w and h else fallback


def hero_widths():
    """Split HERO_W between the portrait and the right panel so both render the
    same height. With no right panel the portrait takes a centred 55%."""
    pw, ph = svg_size("portrait-ascii.svg", (840.0, 875.0))
    if HERO_RIGHT not in RIGHT_PANEL:
        return round(HERO_W * 0.55), 0
    name, fallback, _ = RIGHT_PANEL[HERO_RIGHT]
    rw, rh = svg_size(name, fallback)
    # equal rendered height: portrait_w * ph/pw == right_w * rh/rw
    ratio = (rh / rw) / (ph / pw)          # portrait_w == right_w * ratio
    right_w = HERO_W / (1.0 + ratio)
    return round(HERO_W - right_w), round(right_w)


PORTRAIT_W, RIGHT_W = hero_widths()
HEATMAP_W = HERO_W


def shell(cmd):
    """<h3><code>you@github ~ $ cmd</code></h3> -- h3 because h1/h2 get an
    underline rule from GitHub's stylesheet that breaks the terminal look."""
    return f"<h3><code>{SHELL_USER}@github ~ $ {cmd}</code></h3>"


def badge(link):
    """shields.io badge. Underscores render as spaces, so real underscores in a
    handle have to be doubled, and the whole label needs URL-escaping."""
    def esc(s):
        return urllib.parse.quote(s.replace("_", "__").replace("-", "--"), safe="")

    img = (f"https://img.shields.io/badge/{esc(link['label'])}-{esc(link['value'])}-"
           f"{link.get('color', '0d1117')}?style=for-the-badge"
           f"&logo={link.get('logo', 'github')}&logoColor={link.get('logo_color', 'white')}")
    return f"[![{link['label']}]({img})]({link['url']})"


def section_whoami():
    portrait_img = (f'<img src="./portrait-ascii.svg" width="{PORTRAIT_W}" '
                    f'alt="{DISPLAY_NAME}, ASCII portrait" />')
    out = [
        "<!-- hero: monochrome ASCII portrait that types itself in, beside the",
        "     neofetch-style info card whose rows fade in one by one.",
        "     portrait:  python scripts/prep_photo.py <photo> && python scripts/make_ascii_svg.py",
        "     info card: python scripts/make_info_card.py -->",
        "",
        shell("whoami"),
        "",
    ]
    if HERO_RIGHT in RIGHT_PANEL:
        name, _, alt = RIGHT_PANEL[HERO_RIGHT]
        out += [
            "<table>",
            "<tr>",
            f'<td valign="top">{portrait_img}</td>',
            f'<td valign="top"><img src="./{name}" width="{RIGHT_W}" alt="{alt}" /></td>',
            "</tr>",
            "</table>",
        ]
    else:
        out.append(portrait_img)
    return out


def section_contributions():
    return [
        "<!-- animated contribution graph: real data, boxes reveal cell by cell",
        "     (regenerated daily by .github/workflows/update-profile-art.yml) -->",
        "",
        shell("./contributions.sh"),
        "",
        f'<img src="./contrib-heatmap.svg" width="{HEATMAP_W}" '
        f'alt="{DISPLAY_NAME}\'s GitHub contribution graph, auto-refreshed daily" />',
    ]


def section_links():
    out = [shell("./links.sh"), ""]
    if ROLE_LINE:
        out += [f"<p><b>{ROLE_LINE}</b></p>", ""]
    if LINKS:
        out.append(" ".join(badge(l) for l in LINKS))
    return out


SECTIONS = {
    "whoami": section_whoami,
    "contributions": section_contributions,
    "links": section_links,
}
ORDER = CONFIG.get("section_order", ["whoami", "contributions", "links"])

parts = ["<div align=\"center\">", ""]
for i, key in enumerate(ORDER):
    if key not in SECTIONS:
        continue
    if i:
        # blank lines collapse in markdown, so vertical space needs literal <br>
        parts += ["", "<br>", "<br>", ""]
    parts += SECTIONS[key]()

parts += ["", "<br>", "", "</div>", ""]

readme = "\n".join(parts)
with open(OUT_PATH, "w", encoding="utf-8") as f:
    f.write(readme)
print(f"wrote {OUT_PATH} ({len(readme)} bytes)")
