"""Join the open pieces of a rail: an octilinear A* on a 0.2 mm grid over In2.Cu, F.Cu and B.Cu
(In2 preferred; a via pair, at a cost, hops over another rail), clear of every other net's copper,
written as 0/45/90 segments of the rail width. One connection per run; rerun until the net is whole.

Usage: python3 rail.py +5V
"""
import os, sys, uuid, heapq, io, contextlib
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from shapely.geometry import Polygon, LineString, Point
from shapely.strtree import STRtree
import kpcb, check, nets

LAYERS = ['In2.Cu', 'F.Cu', 'B.Cu']
STEP = 0.2
EDGE = 0.5
TURN = 3            # cells per change of direction
VIA_COST = 40       # cells per layer change
OFF_IN2 = 0.5       # extra cost per cell on F/B: keep the rail on In2 where it can
DIRS = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)]


def fmt(v):
    return ('%.4f' % v).rstrip('0').rstrip('.')


def main(net):
    text, tree, fps, pads = kpcb.load()
    segs, vias = check.tracks(tree)
    w = nets.width(net)
    clr = nets.CLEAR[nets.kind(net)]
    vd = nets.VIA[0]
    o = kpcb.outline(tree)
    xs = [x for x, y in o]; ys = [y for x, y in o]
    x0, y0 = min(xs), min(ys)
    W, H = int((max(xs) - x0) / STEP) + 2, int((max(ys) - y0) / STEP) + 2
    gx, gy = np.meshgrid(np.arange(W) * STEP + x0, np.arange(H) * STEP + y0)
    pts = [Point(gx[i, j], gy[i, j]) for i in range(H) for j in range(W)]
    grid_tree = STRtree(pts)

    def mask(geoms, d):
        """Cells within d of any geometry."""
        m = np.zeros(H * W, bool)
        for g in geoms:
            for k in grid_tree.query(g.buffer(d)):
                if not m[k] and g.distance(pts[k]) < d:
                    m[k] = True
        return m.reshape(H, W)

    other = {L: [] for L in LAYERS}
    holes = []                               # (geom) hole-bearing copper on every layer
    for s in segs:
        if s['net'] != net and s['layer'] in other:
            other[s['layer']].append(LineString([s['a'], s['b']]).buffer(s['w'] / 2))
    for v in vias:
        if v['net'] != net:
            holes.append(Point(v['x'], v['y']).buffer(v['d'] / 2))
    for p in pads:
        if p['net'] == net: continue
        g = Polygon(kpcb.pad_polygon(p))
        if p['drill']:
            holes.append(g)
        else:
            for L in p['layers']:
                if L in other: other[L].append(g)
    inside = Polygon(o).buffer(-(EDGE + w / 2))
    edge = ~mask([inside.exterior], 0) & mask([inside], 0)   # placeholder, replaced below
    edge = np.array([inside.contains(p) for p in pts]).reshape(H, W)
    free = {}
    for L in LAYERS:
        free[L] = edge & ~mask(other[L] + holes, clr + w / 2)
    via_ok = edge & ~mask(holes, clr + vd / 2 + 0.1)
    for L in LAYERS:
        via_ok &= ~mask(other[L], clr + vd / 2)

    with contextlib.redirect_stdout(io.StringIO()):
        unrouted, _ = check.run()
    if net not in unrouted:
        print(net, 'is whole'); return
    # the net's pieces: union-find over all its copper, touching => joined
    own = [(LineString([s['a'], s['b']]).buffer(s['w'] / 2), s['layer']) for s in segs if s['net'] == net]
    own += [(Point(v['x'], v['y']).buffer(v['d'] / 2), 'via') for v in vias if v['net'] == net]
    own += [(Polygon(kpcb.pad_polygon(p)), 'via' if p['drill'] else p['layers'][0]) for p in pads if p['net'] == net]
    parent = list(range(len(own)))
    def f(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]; i = parent[i]
        return i
    ot = STRtree([g for g, _ in own])
    for i, (g, L) in enumerate(own):
        for j in ot.query(g.buffer(1e-3)):
            if j <= i: continue
            L2 = own[j][1]
            if (L == L2 or 'via' in (L, L2)) and g.distance(own[j][0]) < 1e-3:
                parent[f(i)] = f(j)
    groups = {}
    for k in range(len(own)):
        groups.setdefault(f(k), []).append(k)
    groups = sorted(groups.values(), key=len)
    print(net, 'pieces:', [len(g) for g in groups])
    small, big = groups[0], [k for gr in groups[1:] for k in gr]

    def cells(ks):
        m = {L: np.zeros((H, W), bool) for L in LAYERS}
        for k in ks:
            g, L = own[k]
            for q in grid_tree.query(g):
                if g.contains(pts[q]):
                    for LL in (LAYERS if L == 'via' else [L] if L in m else []):
                        m[LL][q // W, q % W] = True
        return m
    start, goal = cells(small), cells(big)
    for L in LAYERS:
        free[L] |= start[L] | goal[L]
    LI = {L: i for i, L in enumerate(LAYERS)}
    gi = np.argwhere(goal['In2.Cu'] | goal['F.Cu'] | goal['B.Cu'])
    def h(i, j):
        return np.abs(gi - [i, j]).max(1).min()
    pq, best, came = [], {}, {}
    for L in LAYERS:
        for i, j in np.argwhere(start[L]):
            heapq.heappush(pq, (h(i, j), 0, i, j, LI[L], -1, None))
    end = None
    while pq:
        _, cost, i, j, l, d, prev = heapq.heappop(pq)
        key = (i, j, l, d)
        if key in best: continue
        best[key] = cost; came[key] = prev
        L = LAYERS[l]
        if goal[L][i, j] and not start[L][i, j]:
            end = key; break
        for nd, (dj, di) in enumerate(DIRS):
            ni, nj = i + di, j + dj
            if not (0 <= ni < H and 0 <= nj < W) or not free[L][ni, nj]: continue
            if di and dj and not (free[L][i, nj] and free[L][ni, j]): continue
            c = cost + (1.4 if di and dj else 1) + (TURN if d not in (-1, nd) else 0) + (OFF_IN2 if l else 0)
            if (ni, nj, l, nd) not in best:
                heapq.heappush(pq, (c + h(ni, nj), c, ni, nj, l, nd, key))
        if via_ok[i, j]:
            for l2 in range(len(LAYERS)):
                if l2 != l and free[LAYERS[l2]][i, j] and (i, j, l2, -1) not in best:
                    c = cost + VIA_COST
                    heapq.heappush(pq, (c + h(i, j), c, i, j, l2, -1, key))
    if end is None:
        print('no path'); return
    path = []
    k = end
    while k:
        path.append(k); k = came[k]
    path.reverse()
    body = []
    runs = []          # (layer, [points])
    for i, j, l, d in path:
        p = (round(gx[i, j], 4), round(gy[i, j], 4))
        if runs and runs[-1][0] == l:
            runs[-1][1].append(p)
        else:
            runs.append((l, [p]))
    for n, (l, ps) in enumerate(runs):
        if n:
            x, y = ps[0]
            body.append('\t(via\n\t\t(at %s %s)\n\t\t(size %s)\n\t\t(drill %s)\n\t\t(layers "F.Cu" "B.Cu")\n\t\t(net "%s")\n\t\t(uuid "%s")\n\t)'
                        % (fmt(x), fmt(y), fmt(nets.VIA[0]), fmt(nets.VIA[1]), net, uuid.uuid4()))
        out = [ps[0]]
        for a, b, c in zip(ps, ps[1:], ps[2:]):
            if (round(b[0] - a[0], 3), round(b[1] - a[1], 3)) != (round(c[0] - b[0], 3), round(c[1] - b[1], 3)):
                out.append(b)
        if len(ps) > 1: out.append(ps[-1])
        for (x1, y1), (x2, y2) in zip(out, out[1:]):
            body.append('\t(segment\n\t\t(start %s %s)\n\t\t(end %s %s)\n\t\t(width %s)\n\t\t(layer "%s")\n\t\t(net "%s")\n\t\t(uuid "%s")\n\t)'
                        % (fmt(x1), fmt(y1), fmt(x2), fmt(y2), fmt(w), LAYERS[l], net, uuid.uuid4()))
        print(LAYERS[l], out)
    t = open(kpcb.PCB).read()
    k = t.find('\n\t(gr_')
    t = t[:k] + '\n' + '\n'.join(body) + t[k:]
    open(kpcb.PCB, 'w').write(t)
    print('added', sum(b.startswith('\t(segment') for b in body), 'segments and', sum(b.startswith('\t(via') for b in body), 'vias')


if __name__ == '__main__':
    main(sys.argv[1])
