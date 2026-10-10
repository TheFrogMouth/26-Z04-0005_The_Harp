"""Straighten the grid router's staircase tracks (fill.py) into the fewest straight segments.

For each multi-point track, from each corner it jumps to the furthest later corner it can reach
in one straight piece that keeps the class clearance (exact geometry, not the grid) to every
other net's copper on that layer and stays 0.5 mm inside the board edge. Endpoints never move,
so connections are untouched. Two-point segments (Freerouting's) are left alone.

Usage: python3 smooth.py [routes.json]
"""
import os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from shapely.geometry import Polygon, Point, LineString
from shapely.strtree import STRtree
import kpcb, nets

EDGE = 0.5


def clear_of(n):
    return nets.CLEAR[nets.kind(n)] if n and not n.startswith('unconnected') else 0.15


def main(path):
    items = json.load(open(path))
    text, tree, fps, pads = kpcb.load()
    inner = Polygon(kpcb.outline(tree)).buffer(-EDGE)
    fixed = {l: [] for l in kpcb.CU}                 # (geom, net) that never change
    for p in pads:
        g = Polygon(kpcb.pad_polygon(p)) if p['kind'] != 'np_thru_hole' else Point(p['x'], p['y']).buffer(p['w'] / 2)
        n = p['net'] if p['kind'] != 'np_thru_hole' else None
        for l in p['layers']:
            fixed[l].append((g, n))
    for w in items:
        if w['type'] == 'via':
            for l in kpcb.CU:
                fixed[l].append((Point(w['x'], w['y']).buffer(nets.VIA[0] / 2), w['net']))

    tg = {k: LineString(w['pts']).buffer(w['w'] / 2) for k, w in enumerate(items) if w['type'] == 'wire'}

    before = after = 0
    for k, w in enumerate(items):
        if w['type'] != 'wire' or len(w['pts']) <= 2:
            continue
        L, net, half = w['layer'], w['net'], w['w'] / 2
        obs = [o for o in fixed[L] if o[1] != net] + \
              [(tg[m], items[m]['net']) for m in tg if m != k and items[m]['layer'] == L and items[m]['net'] != net]
        tree_ = STRtree([o[0] for o in obs])
        need_net = clear_of(net)

        def ok(a, b):
            seg = LineString([a, b]).buffer(half)
            if not inner.contains(seg):
                return False
            for i in tree_.query(seg.buffer(0.2)):
                g, n = obs[i]
                if seg.distance(g) < max(need_net, clear_of(n)) - 1e-4:
                    return False
            return True

        pts = [tuple(p) for p in w['pts']]
        out = [pts[0]]
        i = 0
        while i < len(pts) - 1:
            j = len(pts) - 1
            while j > i + 1 and not ok(pts[i], pts[j]):
                j -= 1
            out.append(pts[j])
            i = j
        before += len(pts) - 1; after += len(out) - 1
        w['pts'] = [list(p) for p in out]
        tg[k] = LineString(out).buffer(half)
    json.dump(items, open(path, 'w'))
    print('segments in multi-point tracks: %d -> %d' % (before, after))


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(kpcb.BUILD, 'routes.json'))
