"""El Regista icon set, drawn with the same stroke system as Regista Display."""

import json

import regista_font as rf
from shapely.geometry import LineString, Polygon, box
from shapely.ops import unary_union

STROKE = 12.0
FILLET = 10.0


def line(*pts, closed=False, radius=FILLET):
    geom = LineString(rf.fillet(list(pts), radius, closed))
    return geom.buffer(
        STROKE / 2, cap_style="flat", join_style="mitre", mitre_limit=4, quad_segs=8
    )


def sq(cx, cy, size):
    return box(cx - size / 2, cy - size / 2, cx + size / 2, cy + size / 2)


ICONS = {
    "search": [
        line((14, 42), (14, 86), (60, 86), (60, 42), closed=True),
        line((56, 46), (90, 10)),
    ],
    "filter": [
        line((8, 80), (92, 80)),
        line((24, 50), (76, 50)),
        line((40, 20), (60, 20)),
    ],
    "twins": [
        line((16, 60), (16, 88), (42, 88), (42, 60), closed=True),
        line((58, 60), (58, 88), (84, 88), (84, 60), closed=True),
        line((8, 4), (8, 40), (50, 40, 0), (50, 4)),
        line((50, 40, 0), (92, 40), (92, 4)),
    ],
    "scale": [
        line((10, 68), (82, 68)),
        line((66, 86), (84, 68, 0), (66, 50)),
        line((90, 32), (18, 32)),
        line((34, 50), (16, 32, 0), (34, 14)),
    ],
    "flame": [
        Polygon(
            [
                (28, 6),
                (72, 6),
                (88, 26),
                (88, 50),
                (72, 76),
                (64, 60),
                (56, 82),
                (48, 96),
                (36, 72),
                (26, 84),
                (12, 58),
                (12, 26),
            ]
        ).difference(
            Polygon(
                [(40, 18), (60, 18), (68, 30), (62, 46), (52, 38), (46, 50), (34, 32)]
            )
        ),
    ],
    "calendar": [
        line((10, 10), (10, 80), (90, 80), (90, 10), closed=True),
        line((10, 58), (90, 58)),
        line((30, 70), (30, 96)),
        line((70, 70), (70, 96)),
        sq(32, 32, 14),
        sq(58, 32, 14),
    ],
    "checks": [
        line((10, 96), (10, 10), (96, 10)),
        line((28, 46), (48, 28, 0), (88, 76)),
    ],
    "shield": [line((12, 92), (88, 92), (88, 52), (50, 8, 0), (12, 52), closed=True)],
    "trophy": [
        line((20, 94), (20, 60), (80, 60), (80, 94)),
        line((20, 84), (6, 84)),
        line((80, 84), (94, 84)),
        line((50, 60), (50, 28)),
        line((24, 12), (76, 12)),
        line((34, 26), (66, 26)),
    ],
    "attack": [
        line((8, 18), (36, 48), (56, 32), (90, 70)),
        line((64, 76), (92, 76, 0), (92, 48)),
    ],
    "create": [
        sq(18, 50, 22),
        sq(82, 84, 22),
        sq(82, 16, 22),
        line((18, 50), (82, 84), radius=0),
        line((18, 50), (82, 16), radius=0),
    ],
    "defense": [
        line((8, 14), (8, 86), (92, 86), (92, 14), closed=True),
        line((8, 50), (92, 50)),
        line((50, 86), (50, 50)),
        line((30, 50), (30, 14)),
        line((70, 50), (70, 14)),
    ],
    "card": [line((26, 8), (26, 92), (74, 92), (74, 8), closed=True), sq(50, 50, 14)],
    "value": [
        line((84, 86), (30, 86), (30, 14), (84, 14)),
        line((10, 60), (60, 60)),
        line((10, 40), (60, 40)),
    ],
    "target": [
        line((8, 8), (8, 92), (92, 92), (92, 8), closed=True),
        line((30, 30), (30, 70), (70, 70), (70, 30), closed=True),
        sq(50, 50, 12),
    ],
    "menu": [line((8, 80), (92, 80)), line((8, 50), (92, 50)), line((8, 20), (92, 20))],
    "close": [line((6, 94), (94, 6), radius=0), line((6, 6), (94, 94), radius=0)],
    "chevron": [line((12, 70), (50, 32), (88, 70))],
    "arrow": [line((8, 50), (86, 50)), line((60, 80), (90, 50, 0), (60, 20))],
}


def to_path(geom):
    geom = geom.intersection(box(0, 0, 100, 100))
    return rf.svg_path(geom, dx=0, dy_top=100)


out = {name: to_path(unary_union(parts)) for name, parts in ICONS.items()}
json.dump(out, open("out/icons.json", "w"))
print(len(out), "icons")
