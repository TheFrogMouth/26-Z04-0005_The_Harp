"""Analog and digital regions, per copper layer, from where the pads are.

Each point on F.Cu (or B.Cu) belongs to the audio side if the nearest audio pad on that layer is
closer, by more than MARGIN, than the nearest digital pad; to the digital side the other way
round; within MARGIN of the midline it is neutral and both may use it. Through-hole pads count
on both layers. Power, GND and control pads count for neither. A region reaches at most REACH
from its own SMD pads and REACH_TH from its through-hole pins, so open copper far from either,
and the jack bodies, stay neutral.
"""
import numpy as np
from scipy.spatial import cKDTree
from shapely.geometry import box, Polygon, MultiPolygon, LineString
from shapely.ops import unary_union, split
import kpcb, nets

STEP = 0.25
MARGIN = 0.75
REACH = 5.0       # a region reaches this far from its own SMD pads; beyond that the board is neutral
REACH_TH = 1.5    # and this far from through-hole pins (jack and pot pins have no circuit round them)


def pad_points(pads, layer, kind, th=None):
    """Outline points of the pads of `kind` on `layer`; th=True only through-hole, False only SMD."""
    pts = []
    for p in pads:
        if layer not in p['layers'] or not p['net'] or p['net'].startswith('unconnected'):
            continue
        if nets.kind(p['net']) != kind or (th is not None and (p['kind'] != 'smd') != th):
            continue
        pts += kpcb.pad_polygon(p) + [(p['x'], p['y'])]
    return np.array(pts) if pts else np.zeros((0, 2))


def nearest(grid, pts):
    if not len(pts):
        return np.full(grid.shape[0], 1e9)
    return cKDTree(pts).query(grid)[0]


def territory(pads, outline, layer, side, margin=MARGIN, reach=REACH):
    """Polygons (hole-free) of the board area on `layer` that belongs to `side` ('AUDIO' or 'DIGITAL')."""
    xs = [p[0] for p in outline]; ys = [p[1] for p in outline]
    gx = np.arange(min(xs), max(xs) + STEP, STEP); gy = np.arange(min(ys), max(ys) + STEP, STEP)
    X, Y = np.meshgrid(gx + STEP / 2, gy + STEP / 2)
    grid = np.stack([X.ravel(), Y.ravel()], 1)
    other = 'DIGITAL' if side == 'AUDIO' else 'AUDIO'
    d_smd = nearest(grid, pad_points(pads, layer, side, th=False))
    d_th = nearest(grid, pad_points(pads, layer, side, th=True))
    d_own = np.minimum(d_smd, d_th)
    d_oth = nearest(grid, pad_points(pads, layer, other))
    mine = ((d_own + margin < d_oth) & ((d_smd < reach) | (d_th < REACH_TH))).reshape(X.shape)
    rects = []
    for j in range(mine.shape[0]):
        row = mine[j]; i = 0
        while i < len(row):
            if row[i]:
                k = i
                while k < len(row) and row[k]:
                    k += 1
                rects.append(box(gx[i], gy[j], gx[k - 1] + STEP, gy[j] + STEP))
                i = k
            else:
                i += 1
    g = unary_union(rects).intersection(Polygon(outline).buffer(1.0))
    g = g.simplify(0.05)
    return holefree(g)


def holefree(g):
    """Split polygons with holes into hole-free pieces (DSN keepout polygons cannot have holes)."""
    out = []
    todo = list(g.geoms) if isinstance(g, MultiPolygon) else [g]
    while todo:
        p = todo.pop()
        if p.is_empty or p.area < 0.05:
            continue
        if p.geom_type == 'MultiPolygon' or p.geom_type == 'GeometryCollection':
            todo += [q for q in p.geoms if q.geom_type == 'Polygon']
            continue
        if not p.interiors:
            out.append(p)
            continue
        hx = p.interiors[0].centroid.x
        x0, y0, x1, y1 = p.bounds
        parts = split(p, LineString([(hx, y0 - 1), (hx, y1 + 1)]))
        todo += [q for q in parts.geoms if q.geom_type == 'Polygon']
    return out
