"""Finish what Freerouting left open: a grid maze router (A*) for the remaining connections.

0.05 mm grid on F.Cu and B.Cu (fine enough to follow 0.5 mm pitch pins) (In2.Cu too for the rails, which prefer it). Everything already on
the board is an obstacle grown by the track's half width plus the clearance plus a grid margin;
a via needs room on every layer it passes (F, B, In2), 0.254 mm to every hole, and stays off
pads and out of the SWD keepout. Vias cost the same as 6 mm of track, and a track pays double
inside the other side's region (audio vs digital), so the separation holds where there is any
way round. Each net is routed from one of its pieces to the nearest other piece until it is
whole. Adds the tracks to build/routes.json; check.py has the last word.

Usage: python3 fill.py [--fresh] [--routes build/routes.json]
  --fresh  clear every signal track first (GND, rails and supplies stay) and route all signals
           with this router, shortest nets first
"""
import os, sys, json, math, heapq, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np
from matplotlib.path import Path
from shapely.geometry import Polygon, Point, LineString
import kpcb, nets, regions, route

RES = 0.05
MARGIN = 0.03           # grid rounding allowance on top of every clearance
VIA_COST = 120          # in grid steps (6 mm)
SOFT_COST = 25          # per step through another signal track or via (rip-up mode), times the round number
RIPPABLE = {'AUDIO', 'DIGITAL', 'CTRL'}
HIST_STEP = 2.0         # added per step cost wherever a rip-up happened (PathFinder history)


def rippable(net):
    """Signal nets, plus the low-current relay coil, LED and VDDA nets (not the supplies)."""
    return bool(net) and (nets.kind(net) in RIPPABLE or net.startswith('/Jacks and Bypass/') or net == 'VDDA')
REGION_COST = 1.0       # extra per step inside the other side's region
EDGE = 0.5
HOLE = 0.254
LAYERS = ['F.Cu', 'B.Cu', 'In2.Cu']
LI = {l: i for i, l in enumerate(LAYERS)}
VD, VDR = nets.VIA


class Grid:
    def __init__(self, outline):
        xs = [p[0] for p in outline]; ys = [p[1] for p in outline]
        self.x0, self.y0 = min(xs) - 0.5, min(ys) - 0.5
        self.nx = int((max(xs) - self.x0 + 0.5) / RES) + 1
        self.ny = int((max(ys) - self.y0 + 0.5) / RES) + 1
        gx = self.x0 + np.arange(self.nx) * RES; gy = self.y0 + np.arange(self.ny) * RES
        self.X, self.Y = np.meshgrid(gx, gy)            # [iy, ix]

    def cell(self, x, y):
        return int(round((y - self.y0) / RES)), int(round((x - self.x0) / RES))

    def xy(self, iy, ix):
        return self.x0 + ix * RES, self.y0 + iy * RES

    def mask(self, geom, m=None):
        """Grid points inside geom (a shapely polygon), as a boolean [ny, nx]; ORed into m if given."""
        if m is None:
            m = np.zeros((self.ny, self.nx), bool)
        polys = list(geom.geoms) if geom.geom_type == 'MultiPolygon' else [geom]
        for p in polys:
            if p.is_empty:
                continue
            x0, y0, x1, y1 = p.bounds
            i0 = max(0, int((x0 - self.x0) / RES)); i1 = min(self.nx, int((x1 - self.x0) / RES) + 2)
            j0 = max(0, int((y0 - self.y0) / RES)); j1 = min(self.ny, int((y1 - self.y0) / RES) + 2)
            if i1 <= i0 or j1 <= j0:
                continue
            pts = np.stack([self.X[j0:j1, i0:i1].ravel(), self.Y[j0:j1, i0:i1].ravel()], 1)
            inside = Path(np.asarray(p.exterior.coords)).contains_points(pts)
            for hole in p.interiors:
                inside &= ~Path(np.asarray(hole.coords)).contains_points(pts)
            m[j0:j1, i0:i1] |= inside.reshape(j1 - j0, i1 - i0)
        return m


def copper(pads, items):
    """Every copper item: (layer, shapely geometry, net, kind, hole radius or 0, index in items or None)."""
    out = []
    for p in pads:
        if p['kind'] == 'np_thru_hole':
            for l in LAYERS:
                out.append((l, Point(p['x'], p['y']).buffer(p['w'] / 2), None, 'npth', p['w'] / 2, None))
            continue
        g = Polygon(kpcb.pad_polygon(p))
        net = p['net'] if p['net'] and not p['net'].startswith('unconnected') else None
        for l in p['layers']:
            if l in LI:
                out.append((l, g, net, 'pad' if p['kind'] == 'smd' else 'th', (p['drill'][0] / 2) if p['drill'] else 0, None))
    for k, w in enumerate(items):
        if w['type'] == 'via':
            for l in LAYERS:
                out.append((l, Point(w['x'], w['y']).buffer(VD / 2), w['net'], 'via', VDR / 2, k))
        else:
            for a, b in zip(w['pts'], w['pts'][1:]):
                out.append((w['layer'], LineString([a, b]).buffer(w['w'] / 2), w['net'], 'track', 0, k))
    return out


def components(net, cu):
    """Connected pieces of a net: list of lists of indices into cu (GND joins through In1)."""
    idx = [i for i, c in enumerate(cu) if c[2] == net]
    parent = {i: i for i in idx}
    def f(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]; i = parent[i]
        return i
    for a in idx:
        for b in idx:
            if a < b and f(a) != f(b):
                ca, cb = cu[a], cu[b]
                same_item = ca[3] in ('via', 'th') and cb[3] == ca[3] and ca[1].equals(cb[1])
                if same_item or (ca[0] == cb[0] and ca[1].distance(cb[1]) < 1e-4):
                    parent[f(a)] = f(b)
    groups = {}
    for i in idx:
        groups.setdefault(f(i), []).append(i)
    return [g for g in groups.values() if any(cu[i][3] in ('pad', 'th') for i in g)]


def route_one(G, net, cu, comps, allowed, region_pen, edge_ok, via_block_base, soft=False, soft_cost=None, hist=None):
    """soft: other signal nets' tracks may be crossed at SOFT_COST a cell (they get ripped up)."""
    w = nets.width(net)
    clr = nets.CLEAR[nets.kind(net)]
    grow = w / 2 + MARGIN
    # obstacles per layer: other nets' copper grown by our half width + the larger clearance
    block, softm = {}, {}
    for l in allowed:
        m = np.zeros((G.ny, G.nx), bool); ms = np.zeros((G.ny, G.nx), bool)
        for (ly, g, n, kind, hr, k) in cu:
            if ly != l or n == net:
                continue
            need = max(clr, nets.CLEAR[nets.kind(n)] if n else 0.15)
            if soft and kind in ('track', 'via') and rippable(n):
                G.mask(g.buffer(need + grow), ms)
            else:
                G.mask(g.buffer(need + grow), m)
        block[l] = m | ~edge_ok
        softm[l] = ms & ~block[l]
    # vias: room on F, B and In2, off pads, clear of holes
    vb = via_block_base.copy()
    for (ly, g, n, kind, hr, k) in cu:
        if n == net and kind not in ('pad',):
            continue
        need = max(clr, nets.CLEAR[nets.kind(n)] if n else 0.15)
        if kind == 'pad' and n == net:
            need = 0.0
        G.mask(g.buffer(need + VD / 2 + MARGIN), vb)
    for (ly, g, n, kind, hr, k) in cu:
        if hr and ly == 'F.Cu':
            G.mask(g.centroid.buffer(hr + HOLE + VDR / 2 + MARGIN), vb)
    # sources: the first piece; targets: every other piece
    src_c, tgt = comps[0], [i for c in comps[1:] for i in c]
    def cells(ids):
        out = {}
        for i in ids:
            l = cu[i][0]
            if l not in allowed:
                continue
            m = G.mask(cu[i][1].buffer(-min(0.05, w / 4))) if cu[i][3] != 'track' else G.mask(cu[i][1])
            out.setdefault(l, np.zeros((G.ny, G.nx), bool))
            out[l] |= m
        return out
    S = cells(src_c); T = cells(tgt)
    if not S or not T:
        return None
    # heuristic: straight-line distance (in cells) to the nearest target cell
    from scipy.ndimage import distance_transform_edt
    tall = np.zeros((G.ny, G.nx), bool)
    for m in T.values():
        tall |= m
    hfield = distance_transform_edt(~tall)
    lay = [l for l in LAYERS if l in allowed]
    lcost = {l: (3.0 if (nets.kind(net) == 'RAIL' and l != 'In2.Cu') else 1.0) for l in lay}
    # search state arrays (layer, iy, ix), flattened
    NL, NY, NX = len(LAYERS), G.ny, G.nx
    free = np.zeros((NL, NY, NX), bool)
    step = np.ones((NL, NY, NX), np.float32)
    Sa = np.zeros((NL, NY, NX), bool); Ta = np.zeros((NL, NY, NX), bool)
    for l in lay:
        li = LI[l]
        if l in S: Sa[li] = S[l]
        if l in T: Ta[li] = T[l]
        free[li] = ~block[l] | Sa[li] | Ta[li]
        step[li] = lcost[l] + (REGION_COST if region_pen.get(l) is not None else 0) * \
            (region_pen[l] if region_pen.get(l) is not None else 0) + (soft_cost or SOFT_COST) * softm[l] + (hist[LI[l]] if hist is not None else 0)
    viaok = ~vb
    hf = hfield.astype(np.float32)
    dist = np.full(NL * NY * NX, np.inf, np.float32)
    prev = np.full(NL * NY * NX, -1, np.int32)
    pq = []
    for idx in np.flatnonzero(Sa):
        dist[idx] = 0.0
        r = idx % (NY * NX)
        heapq.heappush(pq, (float(hf.flat[r]), int(idx)))
    moves = [(0, 1, 1.0), (1, 0, 1.0), (0, -1, 1.0), (-1, 0, 1.0),
             (1, 1, 1.4142), (1, -1, 1.4142), (-1, 1, 1.4142), (-1, -1, 1.4142)]
    lis = [LI[l] for l in lay]
    goal = None
    pops = 0
    stepf = step.ravel(); freef = free.ravel(); Taf = Ta.ravel()
    while pq:
        f, idx = heapq.heappop(pq)
        g = float(dist[idx])
        if f - float(hf.flat[idx % (NY * NX)]) > g + 1e-3:
            continue
        pops += 1
        if pops > 4_000_000:
            break
        if Taf[idx]:
            goal = idx; break
        li, r = divmod(idx, NY * NX)
        j, i = divmod(r, NX)
        for dj, di, c in moves:
            nj, ni = j + dj, i + di
            if not (0 <= nj < NY and 0 <= ni < NX):
                continue
            n = li * NY * NX + nj * NX + ni
            if not freef[n]:
                continue
            ng = g + c * float(stepf[n])
            if ng < dist[n]:
                dist[n] = ng; prev[n] = idx
                heapq.heappush(pq, (ng + float(hf[nj, ni]), n))
        if viaok[j, i]:
            for l2 in lis:
                if l2 == li:
                    continue
                n = l2 * NY * NX + r
                if not freef[n] or (softm[LAYERS[l2]][j, i] and not Sa.flat[n]):
                    continue
                ng = g + VIA_COST
                if ng < dist[n]:
                    dist[n] = ng; prev[n] = idx
                    heapq.heappush(pq, (ng + float(hf[j, i]), n))
    if goal is None:
        return None
    path = [goal]
    while prev[path[-1]] >= 0:
        path.append(int(prev[path[-1]]))
    path.reverse()
    path = [(p // (NY * NX), (p % (NY * NX)) // NX, p % NX) for p in path]
    # to tracks and vias: split by layer, merge straight runs
    out = []
    run = [path[0]]
    def flush(run):
        if len(run) < 2:
            return
        pts = [G.xy(s[1], s[2]) for s in run]
        simp = [pts[0]]
        for k in range(1, len(pts) - 1):
            a, b, c2 = simp[-1], pts[k], pts[k + 1]
            if abs((b[0] - a[0]) * (c2[1] - a[1]) - (b[1] - a[1]) * (c2[0] - a[0])) > 1e-9:
                simp.append(b)
        simp.append(pts[-1])
        out.append(dict(type='wire', net=net, layer=LAYERS[run[0][0]], w=w,
                        pts=[(round(x, 4), round(y, 4)) for x, y in simp]))
    for s in path[1:]:
        if s[0] != run[-1][0]:
            flush(run)
            x, y = G.xy(s[1], s[2])
            out.append(dict(type='via', net=net, x=round(x, 4), y=round(y, 4)))
            run = [s]
        else:
            run.append(s)
    flush(run)
    return out


def prune(items, pads):
    """Drop track ends left dangling by rip-up: a track whose free end touches nothing of its net."""
    from collections import defaultdict
    while True:
        ends = defaultdict(int)
        anchors = defaultdict(list)
        for p in pads:
            if p['net']:
                anchors[p['net']].append((Polygon(kpcb.pad_polygon(p)), set(p['layers'])))
        for w in items:
            if w['type'] == 'via':
                anchors[w['net']].append((Point(w['x'], w['y']).buffer(VD / 2), set(LAYERS)))
        for w in items:
            if w['type'] == 'wire':
                for e in (w['pts'][0], w['pts'][-1]):
                    ends[(w['net'], w['layer'], round(e[0], 3), round(e[1], 3))] += 1
        keep, dropped = [], 0
        for w in items:
            if w['type'] != 'wire':
                keep.append(w); continue
            ok = True
            for e in (w['pts'][0], w['pts'][-1]):
                key = (w['net'], w['layer'], round(e[0], 3), round(e[1], 3))
                if ends[key] > 1:
                    continue
                pe = Point(e)
                if any(w['layer'] in ls and g.distance(pe) < 1e-3 for g, ls in anchors[w['net']]):
                    continue
                if any(o is not w and o['type'] == 'wire' and o['net'] == w['net'] and o['layer'] == w['layer']
                       and LineString(o['pts']).distance(pe) < 1e-3 for o in items):
                    continue
                ok = False
            if ok:
                keep.append(w)
            else:
                dropped += 1
        items = keep
        if not dropped:
            return items


def main():
    text, tree, fps, pads = kpcb.load()
    outline = kpcb.outline(tree)
    G = Grid(outline)
    rp = os.path.join(kpcb.BUILD, 'routes.json')
    if '--routes' in sys.argv:
        rp = sys.argv[sys.argv.index('--routes') + 1]
    items = json.load(open(rp))
    if '--fresh' in sys.argv:      # keep GND, rails and supplies; route every signal again from scratch
        items = [w for w in items if not rippable(w['net'])]
    board = Polygon(outline)
    region = {}
    for l in ('F.Cu', 'B.Cu'):
        region[l] = {}
        for side in ('AUDIO', 'DIGITAL'):
            m = np.zeros((G.ny, G.nx), bool)
            for poly in regions.territory(pads, outline, l, side):
                m |= G.mask(poly)
            region[l][side] = m
    via_block_base = G.mask(Polygon(route.no_via_w201(pads)).buffer(0.0)) | ~G.mask(board.buffer(-(EDGE + VD / 2 + MARGIN)))
    signal = sorted({p['net'] for p in pads if p['net'] and not p['net'].startswith('unconnected') and p['net'] != 'GND'})
    hpwl = {}
    for n in signal:
        xs = [p['x'] for p in pads if p['net'] == n]; ys = [p['y'] for p in pads if p['net'] == n]
        hpwl[n] = (max(xs) - min(xs)) + (max(ys) - min(ys))
    added, ripped = 0, 0
    hist = np.zeros((len(LAYERS), G.ny, G.nx), np.float32)
    for rnd in range(20):
        cu = copper(pads, items)
        todo = [n for n in signal if len(components(n, cu)) > 1]
        todo.sort(key=lambda n: hpwl[n])     # short nets first: they claim their pin escapes
        print('round %d: %d nets open' % (rnd, len(todo)), flush=True)
        json.dump(items, open(rp, 'w'))
        if not todo:
            break
        for net in todo:
            k = nets.kind(net)
            allowed = ['In2.Cu', 'F.Cu', 'B.Cu'] if k == 'RAIL' else ['F.Cu', 'B.Cu']
            other = {'AUDIO': 'DIGITAL', 'DIGITAL': 'AUDIO', 'CTRL': 'AUDIO'}.get(k)
            pen = {l: region[l][other] for l in ('F.Cu', 'B.Cu')} if other else {}
            edge_ok = G.mask(board.buffer(-(nets.width(net) / 2 + EDGE + MARGIN)))
            for attempt in range(6):
                cu = copper(pads, items)
                comps = components(net, cu)
                if len(comps) < 2:
                    break
                t0 = time.time()
                r = route_one(G, net, cu, comps, allowed, pen, edge_ok, via_block_base, hist=hist)
                how = 'clear'
                nv = lambda rr: sum(1 for x in rr if x['type'] == 'via')
                if not r and k in RIPPABLE | {'POWER', 'RAIL'}:
                    r = route_one(G, net, cu, comps, allowed, pen, edge_ok, via_block_base, soft=True,
                                  soft_cost=SOFT_COST * (1 + rnd), hist=hist)
                    how = 'rip-up'
                if not r:
                    print('  %-34s no path' % net, flush=True); break
                if how == 'rip-up':     # take out the signal tracks the new route runs through
                    new_geo = [(w['layer'], LineString(w['pts']).buffer(w['w'] / 2)) for w in r if w['type'] == 'wire']
                    victims = set()
                    for (ly, g, n, kind, hr, kk) in cu:
                        if kind not in ('track', 'via') or n == net or not rippable(n):
                            continue
                        need = max(nets.CLEAR[k], nets.CLEAR[nets.kind(n)])
                        if any(ly == l2 and g.distance(g2) < need for l2, g2 in new_geo):
                            victims.add(kk)
                    items = [w for i, w in enumerate(items) if i not in victims]
                    # PathFinder history: where nets fought, every later route pays more
                    for w in r:
                        if w['type'] == 'wire':
                            G.mask(LineString(w['pts']).buffer(0.4), contested := np.zeros((G.ny, G.nx), bool))
                            hist[LI[w['layer']]][contested] += HIST_STEP
                    ripped += len(victims)
                items += r; added += len(r)
                print('  %-34s %-6s %d tracks %d vias%s  %.0f s' % (net, how, sum(1 for x in r if x['type'] == 'wire'),
                      sum(1 for x in r if x['type'] == 'via'),
                      ('  ripped %d' % len(victims)) if how == 'rip-up' else '', time.time() - t0), flush=True)
    items = prune(items, pads)
    json.dump(items, open(rp, 'w'))
    cu = copper(pads, items)
    left = [n for n in signal if len(components(n, cu)) > 1]
    print('added %d items, ripped %d; still open: %s' % (added, ripped, ' '.join(left) or 'none'))


if __name__ == '__main__':
    main()
