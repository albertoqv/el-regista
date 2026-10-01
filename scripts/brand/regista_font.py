"""Regista Display: a bespoke squared display face built from stroked centerlines.

Design units: cap height 100, stroke 22, centerline corner fillet 12 (outer radius
23, inner ~1). Every glyph is a set of polylines; strokes are unioned and clipped to
the glyph box so diagonal terminals sit flush on the baseline and cap height.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

from shapely.geometry import LineString, Polygon, box
from shapely.geometry.polygon import orient
from shapely.ops import unary_union

W_STROKE = 22.0
HALF = W_STROKE / 2
FILLET = 12.0
SCALE = 7  # 100 design units -> 700 font units of cap height
SIDE = 8  # side bearing in design units


def fillet(points, radius=FILLET, closed=False, steps=10):
    """Round each interior corner of a polyline with a quadratic curve."""
    pts = [p[:2] for p in points]
    radii = [p[2] if len(p) > 2 else radius for p in points]
    n = len(pts)
    out = []
    idx = range(n) if closed else range(n)
    for i in idx:
        if not closed and (i == 0 or i == n - 1):
            out.append(pts[i])
            continue
        prev, cur, nxt = pts[i - 1], pts[i], pts[(i + 1) % n]
        r = radii[i]
        v1 = (prev[0] - cur[0], prev[1] - cur[1])
        v2 = (nxt[0] - cur[0], nxt[1] - cur[1])
        l1, l2 = math.hypot(*v1), math.hypot(*v2)
        if r <= 0 or l1 == 0 or l2 == 0:
            out.append(cur)
            continue
        t = min(r, l1 / 2, l2 / 2)
        a = (cur[0] + v1[0] / l1 * t, cur[1] + v1[1] / l1 * t)
        b = (cur[0] + v2[0] / l2 * t, cur[1] + v2[1] / l2 * t)
        for k in range(steps + 1):
            s = k / steps
            x = (1 - s) ** 2 * a[0] + 2 * (1 - s) * s * cur[0] + s**2 * b[0]
            y = (1 - s) ** 2 * a[1] + 2 * (1 - s) * s * cur[1] + s**2 * b[1]
            out.append((x, y))
    if closed:
        out.append(out[0])
    return out


def stroke(points, closed=False, radius=FILLET):
    line = LineString(fillet(points, radius, closed))
    return line.buffer(
        HALF, cap_style="flat", join_style="mitre", mitre_limit=4, quad_segs=8
    )


def dot(x, y, size=W_STROKE):
    return box(x - size / 2, y, x + size / 2, y + size)


# Glyph definitions: width (design units) and list of shapes (polylines or ready shapes).
# y grows upwards, baseline 0, cap height 100.
def glyphs():
    g = {}

    def add(name, width, *parts, top=100, bottom=0):
        g[name] = {"width": width, "parts": parts, "top": top, "bottom": bottom}

    L = lambda *pts: ("line", pts)
    C = lambda *pts: ("closed", pts)
    S = lambda shape: ("shape", shape)

    W, A, B = 64, 11, 53  # standard width and the two stem centerlines
    add("A", W, L((A, 0), (A, 89), (B, 89), (B, 0)), L((A, 46), (B, 46)))
    add(
        "B",
        W,
        L((A, 0), (A, 89), (B - 5, 89), (B - 5, 55), (A, 55)),
        L((A, 55), (B, 55), (B, 11), (A, 11)),
        L((A, 11), (A, 0)),
    )
    add("C", W, L((W, 89), (A, 89), (A, 11), (W, 11)))
    add("D", W, C((A, 11, 0), (A, 89, 0), (B, 89), (B, 11)))
    add("E", 60, L((60, 89), (A, 89), (A, 11), (60, 11)), L((A, 50), (51, 50)))
    add("F", 60, L((60, 89), (A, 89), (A, 0)), L((A, 50), (51, 50)))
    add("G", W, L((W, 89), (A, 89), (A, 11), (B, 11), (B, 50), (34, 50)))
    add("H", W, L((A, 0), (A, 100)), L((B, 0), (B, 100)), L((A, 50), (B, 50)))
    add("I", 22, L((11, 0), (11, 100)))
    add("J", 60, L((49, 100), (49, 11), (0, 11)))
    add("K", W, L((A, 0), (A, 100)), L((W - 6, 108), (19, 52), (W - 6, -8)))
    add("L", 58, L((A, 100), (A, 11), (58, 11)))
    add(
        "M",
        84,
        L((A, 0), (A, 100)),
        L((73, 0), (73, 100)),
        L((A, 104), (42, 44), (73, 104)),
    )
    add("N", W, L((A, 0), (A, 100)), L((B, 0), (B, 100)), L((A, 104), (B, -4)))
    add("O", W, C((A, 11), (A, 89), (B, 89), (B, 11)))
    add("P", W, L((A, 0), (A, 89), (B, 89), (B, 48), (A, 48)))
    add("Q", W, C((A, 11), (A, 89), (B, 89), (B, 11)), L((38, 28), (W + 2, -6)))
    add("R", W, L((A, 0), (A, 89), (B, 89), (B, 54), (A, 54)), L((28, 54), (W - 2, -8)))
    add("S", W, L((W, 89), (A, 89), (A, 50), (B, 50), (B, 11), (0, 11)))
    add("T", 62, L((0, 89), (62, 89)), L((31, 89), (31, 0)))
    add("U", W, L((A, 100), (A, 11), (B, 11), (B, 100)))
    add("V", 66, L((2, 114), (33, 0), (64, 114)))
    add(
        "W",
        84,
        L((A, 0), (A, 100)),
        L((73, 0), (73, 100)),
        L((A, -4), (42, 56), (73, -4)),
    )
    add("X", 66, L((0, 106), (66, -6)), L((66, 106), (0, -6)))
    add("Y", 66, L((0, 110), (33, 50), (66, 110)), L((33, 50), (33, 0)))
    add("Z", W, L((0, 89), (W - 2, 89)), L((W - 8, 84), (8, 16)), L((2, 11), (W, 11)))

    add("zero", 58, C((A, 11), (A, 89), (47, 89), (47, 11)))
    add("one", 46, L((6, 89), (35, 89), (35, 0)))
    add("two", 60, L((0, 89), (49, 89), (49, 50), (A, 50), (A, 11), (60, 11)))
    add("three", 60, L((0, 89), (49, 89), (49, 11), (0, 11)), L((18, 50), (49, 50)))
    add("four", 62, L((A, 100), (A, 40), (62, 40)), L((46, 70), (46, 0)))
    add("five", 60, L((60, 89), (A, 89), (A, 52), (49, 52), (49, 11), (0, 11)))
    add("six", 60, L((60, 89), (A, 89), (A, 11), (49, 11), (49, 52), (A, 52)))
    add("seven", 60, L((0, 89), (49, 89), (49, 60)), L((49, 70), (22, -10)))
    add("eight", 60, C((A, 11), (A, 89), (49, 89), (49, 11)), L((A, 52), (49, 52)))
    add("nine", 60, L((49, 50), (A, 50), (A, 89), (49, 89), (49, 11), (0, 11)))

    add(
        "euro",
        64,
        L((W, 89), (22, 89), (22, 11), (W, 11)),
        L((0, 60), (46, 60)),
        L((0, 40), (46, 40)),
    )
    add("period", 22, S(dot(11, 0)))
    add("comma", 22, L((11, 22), (11, 0), (4, -16)), bottom=-20)
    add("colon", 22, S(dot(11, 0)), S(dot(11, 46)))
    add("hyphen", 40, L((2, 45), (38, 45)))
    add("endash", 56, L((2, 45), (54, 45)))
    add("plus", 56, L((4, 45), (52, 45)), L((28, 21), (28, 69)))
    add("slash", 44, L((0, -4), (44, 104)))
    add("periodcentered", 22, S(dot(11, 38)))
    add("quotesingle", 22, L((11, 100), (11, 66)))
    add("exclam", 22, L((11, 100), (11, 36)), S(dot(11, 0)))
    add(
        "question",
        56,
        L((0, 89), (45, 89), (45, 56), (27, 56), (27, 34)),
        S(dot(27, 0)),
    )
    add(
        "questiondown",
        56,
        L((56, 11), (11, 11), (11, 44), (29, 44), (29, 66)),
        S(dot(29, 78)),
        top=100,
    )
    add("exclamdown", 22, L((11, 0), (11, 64)), S(dot(11, 78)))
    add(
        "parenleft",
        32,
        L((30, 110), (11, 110), (11, -10), (30, -10)),
        top=112,
        bottom=-12,
    )
    add(
        "parenright",
        32,
        L((2, 110), (21, 110), (21, -10), (2, -10)),
        top=112,
        bottom=-12,
    )
    add("percent", 70, S(dot(14, 66, 26)), S(dot(56, 8, 26)), L((6, 0), (64, 100)))
    add(
        "ampersand",
        60,
        L((60, 11), (11, 11), (11, 50), (40, 50), (40, 89), (18, 89), (18, 50)),
        L((49, 50), (49, 30)),
    )
    add("space", 30)
    return g


ACCENTS = {
    "Aacute": ("A", "acute"),
    "Eacute": ("E", "acute"),
    "Iacute": ("I", "acute"),
    "Oacute": ("O", "acute"),
    "Uacute": ("U", "acute"),
    "Ntilde": ("N", "tilde"),
    "Udieresis": ("U", "dieresis"),
}


def accent_shape(kind, width):
    cx = width / 2
    if kind == "acute":
        return Polygon([(cx - 9, 108), (cx + 3, 108), (cx + 15, 128), (cx + 3, 128)])
    if kind == "tilde":
        line = LineString(
            fillet([(cx - 22, 112), (cx - 10, 122), (cx + 10, 112), (cx + 22, 122)], 5)
        )
        return line.buffer(5, cap_style="flat", join_style="round")
    if kind == "dieresis":
        return unary_union(
            [box(cx - 19, 110, cx - 6, 123), box(cx + 6, 110, cx + 19, 123)]
        )
    raise ValueError(kind)


def glyph_geometry(defn):
    shapes = []
    for kind, data in defn["parts"]:
        if kind == "line":
            shapes.append(stroke(list(data)))
        elif kind == "closed":
            shapes.append(stroke(list(data), closed=True))
        else:
            shapes.append(data)
    if not shapes:
        return None
    geom = unary_union(shapes)
    clip = box(0, defn["bottom"], defn["width"], defn["top"])
    return geom.intersection(clip)


def polygons(geom):
    if geom is None or geom.is_empty:
        return []
    if geom.geom_type == "Polygon":
        return [geom]
    return [p for p in getattr(geom, "geoms", []) if p.geom_type == "Polygon"]


def build_all():
    defs = glyphs()
    geoms = {name: glyph_geometry(d) for name, d in defs.items()}
    widths = {name: d["width"] for name, d in defs.items()}
    for name, (base, acc) in ACCENTS.items():
        geoms[name] = unary_union([geoms[base], accent_shape(acc, widths[base])])
        widths[name] = widths[base]
    return geoms, widths


def svg_path(geom, dx=0.0, dy_top=100.0, scale=1.0):
    """SVG path data (y down) for a shapely geometry in design units."""
    parts = []
    for poly in polygons(geom):
        for ring in [poly.exterior, *poly.interiors]:
            pts = list(ring.coords)
            cmd = (
                "M"
                + " L".join(
                    f"{(x + dx) * scale:.2f} {(dy_top - y) * scale:.2f}"
                    for x, y in pts[:-1]
                )
                + " Z"
            )
            parts.append(cmd)
    return " ".join(parts)


CHAR_NAMES = {
    **{c: c for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"},
    "0": "zero",
    "1": "one",
    "2": "two",
    "3": "three",
    "4": "four",
    "5": "five",
    "6": "six",
    "7": "seven",
    "8": "eight",
    "9": "nine",
    ".": "period",
    ",": "comma",
    ":": "colon",
    "-": "hyphen",
    "–": "endash",
    "+": "plus",
    "/": "slash",
    "·": "periodcentered",
    "'": "quotesingle",
    "!": "exclam",
    "?": "question",
    "¿": "questiondown",
    "¡": "exclamdown",
    "(": "parenleft",
    ")": "parenright",
    "%": "percent",
    "€": "euro",
    "&": "ampersand",
    " ": "space",
    "Á": "Aacute",
    "É": "Eacute",
    "Í": "Iacute",
    "Ó": "Oacute",
    "Ú": "Uacute",
    "Ñ": "Ntilde",
    "Ü": "Udieresis",
}


def word_svg(text, geoms, widths, tracking=6):
    """Path data for a word, in design units, plus its total width."""
    x = 0.0
    paths = []
    for ch in text:
        name = CHAR_NAMES.get(ch.upper(), "space")
        x += SIDE / 2
        if geoms.get(name) is not None:
            paths.append(svg_path(geoms[name], dx=x))
        x += widths[name] + SIDE / 2 + tracking
    return " ".join(p for p in paths if p), x - tracking


def build_font(geoms, widths, out_dir: Path):
    from fontTools.fontBuilder import FontBuilder
    from fontTools.pens.ttGlyphPen import TTGlyphPen

    order = [".notdef"] + sorted(geoms)
    fb = FontBuilder(1000, isTTF=True)
    fb.setupGlyphOrder(order)
    cmap = {}
    for ch, name in CHAR_NAMES.items():
        cmap[ord(ch)] = name
        if ch.lower() != ch:
            cmap[ord(ch.lower())] = name
    fb.setupCharacterMap(cmap)
    glyf, metrics = {}, {}
    for name in order:
        pen = TTGlyphPen(None)
        if name != ".notdef":
            for poly in polygons(geoms[name]):
                poly = orient(poly, sign=-1.0)
                for ring in [poly.exterior, *poly.interiors]:
                    pts = [
                        (round((x + SIDE / 2) * SCALE), round(y * SCALE))
                        for x, y in ring.coords[:-1]
                    ]
                    clean = [p for i, p in enumerate(pts) if p != pts[i - 1]]
                    if len(clean) < 3:
                        continue
                    pen.moveTo(clean[0])
                    for p in clean[1:]:
                        pen.lineTo(p)
                    pen.closePath()
            adv = round((widths[name] + SIDE) * SCALE)
        else:
            adv = 500
        glyf[name] = pen.glyph()
        metrics[name] = (adv, 0)
    fb.setupGlyf(glyf)
    for name in order:
        g = glyf[name]
        g.recalcBounds(fb.font["glyf"]) if hasattr(g, "recalcBounds") else None
        metrics[name] = (metrics[name][0], getattr(g, "xMin", 0) or 0)
    fb.setupHorizontalMetrics(metrics)
    fb.setupHorizontalHeader(ascent=900, descent=-200)
    fb.setupNameTable(
        {
            "familyName": "Regista Display",
            "styleName": "Regular",
            "uniqueFontIdentifier": "RegistaDisplay-Regular-1.0",
            "fullName": "Regista Display",
            "psName": "RegistaDisplay-Regular",
            "version": "Version 1.000",
        }
    )
    fb.setupOS2(
        sTypoAscender=900,
        sTypoDescender=-200,
        usWinAscent=950,
        usWinDescent=220,
        sCapHeight=700,
        sxHeight=700,
        achVendID="REGI",
    )
    fb.setupPost()
    ttf = out_dir / "RegistaDisplay.ttf"
    fb.save(ttf)
    from fontTools.ttLib import TTFont

    f = TTFont(ttf)
    f.flavor = "woff2"
    f.save(out_dir / "RegistaDisplay.woff2")
    return ttf


if __name__ == "__main__":
    out = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    out.mkdir(parents=True, exist_ok=True)
    geoms, widths = build_all()
    build_font(geoms, widths, out)
    words = {}
    for w in ["REGISTA", "EL", "E", "L", "R"]:
        d, width = word_svg(w, geoms, widths)
        words[w] = {"d": d, "width": width}
    json.dump(words, open(out / "words.json", "w"))
    specimen, sw = word_svg(
        "ABCDEFGHIJKLMNÑOPQRSTUVWXYZ 0123456789 ÁÉÍÓÚ ¿?¡!.,:-+%/()", geoms, widths
    )
    json.dump({"d": specimen, "width": sw}, open(out / "specimen.json", "w"))
    print("ok", out)
