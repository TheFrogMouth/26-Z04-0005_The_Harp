"""Fanout to the inner layers: every SMD pad of the given nets gets its own via.

GND (Relic rule): the via lands on the In1.Cu plane and that is the whole connection.
Rails (+3V3, +5V, +9V): the via takes the rail down to In2.Cu, where the router joins the vias.

For each pad: the nearest via spot that clears every other copper item on all four layers (vias
go through the board), every hole, the board edge and the SWD keepout, joined to the pad by one
straight stub that clears the pad's own layer. On ICs the via goes inward, under the package, so
it does not block the signal escapes; on two-pin parts it goes off the pad's free end. A pad that
finds nothing within 2.2 mm tries again up to 4.5 mm away with a 0.25 mm stub.
"""
import os, sys, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kpcb, nets
from shapely.geometry import Polygon, Point, LineString
from shapely.strtree import STRtree

VD, VDR = nets.VIA
HOLE = 0.254
EDGE = 0.5


def fanout(fps, pads, outline, netset, fixed=(), keepout=None):
    """Return stubs and vias (routes.json items) for every SMD pad on a net in netset.
    fixed: items already on the board (they are obstacles, or joinable if on the same net)."""
    edge = Polygon(outline)
    inner = edge.buffer(-EDGE)
    fpd = {f['ref']: f for f in fps}
    obst = []                      # (geom, net, layers, kind, pad)
    for p in pads:
        if p['kind'] == 'np_thru_hole':
            obst.append((Point(p['x'], p['y']).buffer(p['w'] / 2), None, set(kpcb.CU), 'hole', p))
        else:
            obst.append((Polygon(kpcb.pad_polygon(p)), p['net'], set(p['layers']), p['kind'], p))
    holes = [Point(p['x'], p['y']).buffer(p['drill'][0] / 2) for p in pads if p['drill']]

    def add(w):
        if w['type'] == 'via':
            obst.append((Point(w['x'], w['y']).buffer(VD / 2), w['net'], set(kpcb.CU), 'via', None))
            holes.append(Point(w['x'], w['y']).buffer(VDR / 2))
        else:
            for a, b in zip(w['pts'], w['pts'][1:]):
                obst.append((LineString([a, b]).buffer(w['w'] / 2), w['net'], {w['layer']}, 'track', None))
    for w in fixed:
        add(w)
    out, failed = [], []
    todo = [p for p in pads if p['net'] in netset and p['kind'] == 'smd']
    for p in todo:
        net = p['net']
        clr = nets.CLEAR[nets.kind(net)]
        f = fpd[p['ref']]
        tree_ = STRtree([o[0] for o in obst])
        htree = STRtree(holes)
        L = p['layers'][0]
        own = Polygon(kpcb.pad_polygon(p))
        if len(f['pads']) > 3:          # IC: inward, toward the package centre
            pref = (f['x'] - p['x'], f['y'] - p['y'])
        else:                           # two/three-pin part: off the free end
            pref = (p['x'] - f['x'], p['y'] - f['y'])
        nrm = math.hypot(*pref) or 1.0
        pref = (pref[0] / nrm, pref[1] / nrm)
        best = None
        for reach, wmax in ((2.2, 0.4), (4.5, 0.25)):
            w = min(wmax, min(p['w'], p['h']))
            span = int((reach + VD) / 0.1)
            for i in range(-span, span + 1):
                for j in range(-span, span + 1):
                    x, y = p['x'] + i * 0.1, p['y'] + j * 0.1
                    c = Point(x, y)
                    d = own.distance(c)
                    if d < VD / 2 + 0.1 or d > VD / 2 + reach:
                        continue
                    vx, vy = x - p['x'], y - p['y']
                    score = d + 0.8 * (1 - (vx * pref[0] + vy * pref[1]) / math.hypot(vx, vy))
                    if best and score >= best[0]:
                        continue
                    via = c.buffer(VD / 2)
                    if not inner.contains(via) or (keepout is not None and via.intersects(keepout)):
                        continue
                    stub = LineString([(p['x'], p['y']), (x, y)]).buffer(w / 2)
                    ok = True
                    for k in tree_.query(via.buffer(clr).union(stub.buffer(clr))):
                        g, n, lays, kind, q = obst[k]
                        if q is p:
                            continue
                        if n == net:
                            if kind == 'smd' and g.distance(via) < 0.05:
                                ok = False; break          # no via in another pad
                            if kind == 'via' and g.distance(via) < clr:
                                ok = False; break          # each pad its own via
                            continue
                        need = max(clr, nets.CLEAR[nets.kind(n)] if n and not n.startswith('unconnected') else 0.15)
                        if g.distance(via) < need or (L in lays and g.distance(stub) < need):
                            ok = False; break
                    if not ok:
                        continue
                    if any(holes[k].distance(c) < VDR / 2 + HOLE for k in htree.query(c.buffer(VDR / 2 + HOLE))):
                        continue
                    best = (score, x, y, w)
            if best:
                break
        if not best:
            failed.append('%s.%s' % (p['ref'], p['num']))
            continue
        _, x, y, w = best
        new = [dict(type='wire', net=net, layer=L, w=w, pts=[(p['x'], p['y']), (x, y)]),
               dict(type='via', net=net, x=x, y=y)]
        for it in new:
            add(it); out.append(it)
    return out, failed
