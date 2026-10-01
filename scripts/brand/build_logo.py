"""Builds the El Regista logo SVGs (pure paths) from the Regista Display glyphs."""

import base64
import json
from pathlib import Path

out = Path("out")
words = json.load(open(out / "words.json"))
R, E, L, RR = words["REGISTA"], words["E"], words["L"], words["R"]

# Claret, bone and sky blue: an old football club, nothing like a betting brand.
SLATE, CHALK, YELLOW, GRASS = "#26131A", "#F3EBE3", "#9CCFEA", "#F28C6B"
LABEL_W = 44
GAP = 12


def lockup(fg, label_bg, label_fg, outline=False):
    """Horizontal logo: yellow label with stacked EL + REGISTA."""
    width = LABEL_W + GAP + R["width"]
    s = 0.43
    label = (
        f'<rect x="0" y="0" width="{LABEL_W}" height="100" rx="6" fill="{label_bg}"/>'
        if not outline
        else f'<rect x="3" y="3" width="{LABEL_W - 6}" height="94" rx="5" fill="none" stroke="{fg}" stroke-width="6"/>'
    )
    e_x = (LABEL_W - E["width"] * s) / 2
    l_x = (LABEL_W - L["width"] * s) / 2
    body = (
        label
        + f'<path transform="translate({e_x:.2f} 6) scale({s})" d="{E["d"]}" fill="{label_fg}"/>'
        + f'<path transform="translate({l_x:.2f} 51) scale({s})" d="{L["d"]}" fill="{label_fg}"/>'
        + f'<path transform="translate({LABEL_W + GAP} 0)" d="{R["d"]}" fill="{fg}"/>'
    )
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="-2 -2 {width + 4:.1f} 104">{body}</svg>'


def stacked(fg, label_bg, label_fg):
    """Compact version: label on top reading EL, REGISTA below."""
    width = R["width"]
    s = 0.46
    el_w = (E["width"] + L["width"]) * s + 6
    x0 = 0
    body = (
        f'<rect x="{x0}" y="0" width="{el_w + 16:.1f}" height="62" rx="6" fill="{label_bg}"/>'
        + f'<path transform="translate({x0 + 8} 8) scale({s})" d="{E["d"]}" fill="{label_fg}"/>'
        + f'<path transform="translate({x0 + 8 + E["width"] * s + 6:.2f} 8) scale({s})" d="{L["d"]}" fill="{label_fg}"/>'
        + f'<path transform="translate(0 72)" d="{R["d"]}" fill="{fg}"/>'
    )
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="-2 -2 {width + 4:.1f} 176">{body}</svg>'


def icon(bg, fg, accent, rounded=True):
    """App icon / favicon: the R with a yellow bar underneath, like a captain's band."""
    size = 120
    s = 0.74
    r_w = RR["width"] * s
    x = (size - r_w) / 2
    y = 14
    rx = 26 if rounded else 0
    body = (
        f'<rect width="{size}" height="{size}" rx="{rx}" fill="{bg}"/>'
        + f'<path transform="translate({x:.2f} {y}) scale({s})" d="{RR["d"]}" fill="{fg}"/>'
        + f'<rect x="{x:.2f}" y="{y + 100 * s + 8:.2f}" width="{r_w:.2f}" height="11" rx="2" fill="{accent}"/>'
    )
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size} {size}">{body}</svg>'


files = {
    "logo-dark.svg": lockup(CHALK, YELLOW, SLATE),
    "logo-light.svg": lockup(SLATE, YELLOW, SLATE),
    "logo-on-yellow.svg": lockup(SLATE, SLATE, YELLOW),
    "logo-mono.svg": lockup(CHALK, None, CHALK, outline=True),
    "logo-stacked-dark.svg": stacked(CHALK, YELLOW, SLATE),
    "icon.svg": icon(SLATE, CHALK, YELLOW),
    "icon-yellow.svg": icon(YELLOW, SLATE, SLATE),
    "icon-light.svg": icon(CHALK, SLATE, YELLOW),
}
brand = out / "brand"
brand.mkdir(exist_ok=True)
for name, svg in files.items():
    (brand / name).write_text(svg, encoding="utf-8")


def uri(svg):
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode()


json.dump({k: uri(v) for k, v in files.items()}, open(out / "logo_uris.json", "w"))
print("ok", list(files))
