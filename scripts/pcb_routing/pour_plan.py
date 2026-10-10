"""In2 pours as big blocks with 45 degree corners, joined by short bus-bar links.

pours.py grows each rail from its autorouted tracks, which gives organic outlines. This one draws them:

1. +9V: a band across the top (buck input and DC jack), plus a block round each pin that is far
   away (the relay coil, the two LEDs).
2. +3V3 and +5V: every cell of a 1 mm grid takes the net of its nearest supply pin (square metric, so
   boundaries run at 0, 45 and 90 degrees), the map is smoothed with a majority filter so small mixed
   patches go to their neighbours, and every pin keeps a small disc of its own net. The blocks are
   rounded with bevelled buffers: every corner becomes a 45 degree chamfer and slivers thinner than
   2 mm are dropped.
3. Where a rail's blocks are not joined (the fill is imitated), the shortest path along the rail's old
   In2 tracks (a planar layout from Freerouting) between two groups is added as a bus bar, cutting the
   other rails' blocks with the usual gap. Repeated until the rails are whole.
4. What is still cut off after that gets a short jumper on F.Cu or B.Cu (pours.jumpers), or is reported.

Usage: git show origin/main:'kicad/the_harp/The Harp.kicad_pcb' > the board file, then python3 pour_plan.py
(the board must still have the rails' In2 tracks; they are removed).
"""
import os, sys, math, heapq
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np
from scipy import ndimage as ndi
from shapely.geometry import Polygon, Point, LineString, box
from shapely.ops import unary_union
from skimage.graph import MCP_Geometric
import kpcb, check, pours

C = 1.0                       # coarse grid, mm
SMOOTH = 4                    # majority filter passes
WIN = 9                       # and its window, cells
CHAMFER = 1.2                 # bevel size, mm
BEVEL = 3                     # shapely join_style: bevel
STRAY = 1.8                   # every pin keeps a disc of this radius of its own net
BLOCK9 = 2.6                  # +9V block half size round a far pin (relay, LEDs)
EDGE_BAR = 1.0                # width of a link that had to be routed afresh (hugs the board edge)
EDGE_PEN = 0.9                # cost per mm of distance from the board edge: such links stay at the edge
# links to draw first, between two pins of a rail (the router otherwise takes the cheapest way)
HINTS = [('+5V', (175.2, 57.0), (167.2, 127.7))]     # the LDO output, down the right edge, to U701
BAR = 0.5                     # bus-bar link width, mm (at least; the old tracks were 0.5 and 0.6)

# +9V: the top band; the buck's +3V3 output pins (y 57..59.5, x < 131.5) and the +3V3 pin at
# (138.5, 59.5) stay out of it
NINE = [
    box(120.5, 53.5, 131.5, 56.0),
    box(131.5, 53.5, 137.5, 62.5),
    box(137.5, 53.5, 139.5, 58.0),
    box(139.5, 48.5, 157.5, 62.5),
    box(157.5, 56.5, 162.5, 62.5),
]


def bevel(poly, d=CHAMFER):
    """Open (drop what is thinner than 2d), then close (fill gaps narrower than 2d), with bevelled corners."""
    p = poly.buffer(-d, join_style=BEVEL).buffer(d, join_style=BEVEL)
    return p.buffer(d, join_style=BEVEL).buffer(-d, join_style=BEVEL)


class Backbone:
    """A rail's old In2 tracks as a graph; shortest path between two sets of points."""
    def __init__(self, segs, net):
        self.edges = {}
        self.node = {}
        for s in segs:
            if s['layer'] == 'In2.Cu' and s['net'] == net:
                a, b = self.key(s['a']), self.key(s['b'])
                L = math.dist(s['a'], s['b'])
                self.edges.setdefault(a, []).append((b, L, s['w'], s['a'], s['b']))
                self.edges.setdefault(b, []).append((a, L, s['w'], s['b'], s['a']))
                self.node[a] = s['a']; self.node[b] = s['b']

    @staticmethod
    def key(p):
        return (round(p[0], 2), round(p[1], 2))

    def nearest(self, p):
        if not self.node:
            return None
        best = min(self.node, key=lambda k: math.dist(k, p))
        return best if math.dist(best, p) < 0.5 else None

    def path(self, sources, targets):
        src = [k for k in (self.nearest(p) for p in sources) if k is not None]
        tgt = {k for k in (self.nearest(p) for p in targets) if k is not None}
        dist = {k: 0.0 for k in src}; prev = {}
        pq = [(0.0, k) for k in src]
        heapq.heapify(pq)
        while pq:
            d, u = heapq.heappop(pq)
            if d > dist.get(u, 1e18):
                continue
            if u in tgt:
                out = []
                while u in prev:
                    pu, e = prev[u]
                    out.append(e); u = pu
                return out
            for (v, w, wd, pa, pb) in self.edges.get(u, []):
                nd = d + w
                if nd < dist.get(v, 1e18):
                    dist[v] = nd; prev[v] = (u, (pa, pb, wd)); heapq.heappush(pq, (nd, v))
        return None


def main():
    text, tree, fps, pads = kpcb.load()
    board = Polygon(kpcb.outline(tree))
    segs, vias = check.tracks(tree)
    g = pours.G(kpcb.outline(tree))
    obs = pours.obstacles(pads, vias)
    area = board.buffer(-pours.EDGE)
    t9 = pours.terminals(pads, vias, '+9V')
    t3 = pours.terminals(pads, vias, '+3V3'); t5 = pours.terminals(pads, vias, '+5V')

    far9 = [p for p in t9 if p[1] > 100]                                  # the relay coil and the two LEDs
    nine = unary_union(NINE + [box(x - BLOCK9, y - BLOCK9, x + BLOCK9, y + BLOCK9) for x, y in far9]).intersection(area)
    nine = bevel(nine, 0.8)

    pts = np.array(t3 + t5); lab = np.array([0] * len(t3) + [1] * len(t5))
    x0, y0 = 120.0, 48.0
    nx, ny = int(57 / C) + 1, int(96 / C) + 1
    gx = x0 + (np.arange(nx) + 0.5) * C; gy = y0 + (np.arange(ny) + 0.5) * C
    X, Y = np.meshgrid(gx, gy)
    d = np.stack([np.maximum(np.abs(X - px), np.abs(Y - py)) for (px, py) in pts])   # square metric
    label = lab[d.argmin(0)]                                                          # 0 = +3V3, 1 = +5V
    for _ in range(SMOOTH):
        votes = np.stack([ndi.uniform_filter((label == k).astype(float), size=WIN, mode='nearest') for k in (0, 1)])
        label = votes.argmax(0)
    for (x, y), k in zip(pts, lab):
        label[(X - x) ** 2 + (Y - y) ** 2 <= STRAY ** 2] = k

    def poly_of(mask):
        return unary_union([box(x0 + i * C, y0 + j * C, x0 + (i + 1) * C, y0 + (j + 1) * C) for j, i in np.argwhere(mask)])

    rest = area.difference(nine.buffer(pours.GAP))
    res = {'+9V': nine}
    for k, net in ((0, '+3V3'), (1, '+5V')):
        res[net] = bevel(poly_of(label == k).intersection(rest)).intersection(rest)
    res['+5V'] = res['+5V'].difference(res['+3V3'].buffer(pours.GAP))
    res['+3V3'] = res['+3V3'].difference(res['+5V'].buffer(pours.GAP))
    for net in ('+3V3', '+5V'):
        res[net] = res[net].buffer(-pours.GAP, join_style=BEVEL).intersection(area)

    bb = {net: Backbone(segs, net) for net in pours.RAILS}
    for rnd in range(10):
        added = False
        for net in pours.RAILS:
            grp, terms, lost = pours.groups_in_fill(net, res[net], obs, pads, vias)
            comps = [list(q) for q in grp] + [[t] for t in lost]
            if len(comps) <= 1:
                continue
            joined = [terms[t] for t in comps[0]]
            for other in comps[1:]:
                tgt = [terms[t] for t in other]
                p = bb[net].path(joined, tgt)
                if not p:
                    continue
                bar = unary_union([LineString([a, b]).buffer(max(w, BAR) / 2, cap_style=3, join_style=2) for (a, b, w) in p])
                bar = bar.intersection(area)
                res[net] = unary_union([res[net], bar])
                for o in pours.RAILS:
                    if o != net:
                        res[o] = res[o].difference(bar.buffer(0.22, join_style=BEVEL))
                joined += tgt
                added = True
                print('round %d: %-5s bus bar of %.1f mm to the group at %s' % (
                    rnd, net, sum(math.dist(a, b) for a, b, w in p), tuple(round(v, 1) for v in tgt[0])))
        if not added:
            break

    # a rail with no old track between two of its groups: route a link afresh, hugging the board edge
    edge_dist = ndi.distance_transform_edt(g.polymask(board)) * pours.RES
    for net in pours.RAILS:
        for attempt in range(6):
            grp, terms, lost = pours.groups_in_fill(net, res[net], obs, pads, vias)
            comps = [list(q) for q in grp] + [[t] for t in lost]
            if len(comps) <= 1:
                break
            for (hn, ha, hb) in HINTS:                       # put the hinted pair's groups first, so they are joined first
                if hn != net:
                    continue
                ia_ = min(range(len(terms)), key=lambda t: math.dist(terms[t], ha))
                ib_ = min(range(len(terms)), key=lambda t: math.dist(terms[t], hb))
                ga = next((q for q in comps if ia_ in q), None); gb = next((q for q in comps if ib_ in q), None)
                if ga is not None and gb is not None and ga is not gb:
                    comps = [[ib_], [ia_]] + [q for q in comps if q is not ga and q is not gb]   # route exactly this pair
                    break
            blk = ~g.polymask(board.buffer(-(pours.EDGE + EDGE_BAR / 2)))
            for (gm, n) in obs:
                if n != net:
                    blk |= g.polymask(gm.buffer(pours.CLR + EDGE_BAR / 2 + 0.04))
            cost = np.where(blk, 1e9, 1.0 + EDGE_PEN * edge_dist)
            best = None
            for other in comps[1:]:
                for ta in other:
                    mcp = MCP_Geometric(cost, fully_connected=True)
                    ja, ia = g.cell(*terms[ta])
                    free = np.zeros_like(blk); free[max(ja - 5, 0):ja + 6, max(ia - 5, 0):ia + 6] = True
                    cst = np.where(blk & ~free, 1e9, cost)
                    mcp = MCP_Geometric(cst, fully_connected=True)
                    cum, _ = mcp.find_costs([(ja, ia)])
                    for tb in comps[0]:
                        jb, ib = g.cell(*terms[tb])
                        v = cum[jb, ib]
                        if np.isfinite(v) and v < 1e8 and (best is None or v < best[0]):
                            best = (v, mcp, (jb, ib), terms[ta], terms[tb])
                    break                                  # one start terminal per group is enough
            if best is None:
                print('%-5s no free link between its groups' % net)
                break
            v, mcp, end, pa, pb = best
            path = [g.xy(j, i) for (j, i) in mcp.traceback(end)]
            line = LineString([pa] + path + [pb]).simplify(0.15)
            bar = line.buffer(EDGE_BAR / 2, cap_style=3, join_style=2).intersection(area)
            res[net] = unary_union([res[net], bar])
            for o in pours.RAILS:
                if o != net:
                    res[o] = res[o].difference(bar.buffer(0.22, join_style=BEVEL))
            print('%-5s link of %.1f mm along the edge: %s -> %s' % (net, line.length, tuple(round(c, 1) for c in pa), tuple(round(c, 1) for c in pb)))

    for net in pours.RAILS:                     # drop leftovers: small pieces holding no pin of their rail
        keep = []
        terms = pours.terminals(pads, vias, net)
        for p in (list(res[net].geoms) if res[net].geom_type == 'MultiPolygon' else [res[net]]):
            if p.area >= 40 or any(p.distance(Point(t)) < 0.3 for t in terms):
                keep.append(p)
            else:
                print('%-5s dropped a %.1f mm2 piece without pins at (%.0f, %.0f)' % (net, p.area, p.centroid.x, p.centroid.y))
        res[net] = unary_union(keep)

    jump = []
    for net in pours.RAILS:
        grp, terms, lost = pours.groups_in_fill(net, res[net], obs, pads, vias)
        print('%-5s fill: %d terminals in %d joined group(s), %d floating %s' % (
            net, len(terms), len(grp), len(lost), [tuple(round(v, 1) for v in terms[t]) for t in lost]))
        if len(grp) > 1 or lost:
            jump += pours.jumpers(g, net, grp, terms, lost, pads, vias, segs, jump, board)
    jump += pours.vdda(g, pads, vias, segs, jump, board)
    pours.write(res, jump)
    return jump


if __name__ == '__main__':
    main()
