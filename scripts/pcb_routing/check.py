"""Check the routed board from the board file: every net connected, copper clearances, edge clearance,
hole spacing. Stand-in for KiCad's DRC until the board is opened in KiCad.

GND counts as connected through the In1.Cu plane (vias and through-hole GND pads reach it).
Usage: python3 check.py [-v]
"""
import os, sys, re
from collections import defaultdict
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kpcb, nets
from shapely.geometry import Polygon, LineString, Point
from shapely.strtree import STRtree

EDGE = 0.5          # copper to board edge (project rule)
HOLE = 0.254        # hole to hole (project rule)
TOL = 0.005


def tracks(tree):
    segs, vias = [], []
    for s in kpcb.findall(tree, 'segment'):
        segs.append(dict(a=tuple(map(float, kpcb.find(s, 'start')[1:3])), b=tuple(map(float, kpcb.find(s, 'end')[1:3])),
                         w=float(kpcb.find(s, 'width')[1]), layer=kpcb.find(s, 'layer')[1], net=kpcb.find(s, 'net')[1]))
    for v in kpcb.findall(tree, 'via'):
        at = kpcb.find(v, 'at')
        vias.append(dict(x=float(at[1]), y=float(at[2]), d=float(kpcb.find(v, 'size')[1]),
                         drill=float(kpcb.find(v, 'drill')[1]), net=kpcb.find(v, 'net')[1]))
    return segs, vias


def clear_of(net):
    if not net or net.startswith('unconnected'):
        return 0.15
    return nets.CLEAR[nets.kind(net)]


def run(verbose=False):
    text, tree, fps, pads = kpcb.load()
    segs, vias = tracks(tree)
    items = []      # (layer, geom, net, kind, id)
    for i, p in enumerate(pads):
        g = Polygon(kpcb.pad_polygon(p))
        for l in p['layers']:
            if p['kind'] == 'np_thru_hole':
                continue
            items.append((l, g, p['net'] if p['net'] and not p['net'].startswith('unconnected') else None,
                          'pad', '%s.%s' % (p['ref'], p['num'])))
    for i, s in enumerate(segs):
        g = LineString([s['a'], s['b']]).buffer(s['w'] / 2, quad_segs=8) if s['a'] != s['b'] else Point(s['a']).buffer(s['w'] / 2)
        items.append((s['layer'], g, s['net'], 'seg', 'seg%d' % i))
    for i, v in enumerate(vias):
        g = Point(v['x'], v['y']).buffer(v['d'] / 2, quad_segs=8)
        for l in kpcb.CU:
            items.append((l, g, v['net'], 'via', 'via%d' % i))

    # connectivity
    parent = list(range(len(items)))
    def f(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]; i = parent[i]
        return i
    def u(a, b):
        a, b = f(a), f(b)
        if a != b: parent[a] = b
    by_id = defaultdict(list)
    for k, it in enumerate(items):
        by_id[it[4]].append(k)
    for ks in by_id.values():            # one pad / via across its layers
        for k in ks[1:]:
            u(ks[0], k)
    plane = None
    for k, it in enumerate(items):         # GND on In1 joins the plane
        if it[0] == 'In1.Cu' and it[2] == 'GND':
            if plane is None: plane = k
            else: u(plane, k)
    by_layer = defaultdict(list)
    for k, it in enumerate(items):
        by_layer[it[0]].append(k)
    problems = []
    for l, ks in by_layer.items():
        geoms = [items[k][1] for k in ks]
        tree_ = STRtree(geoms)
        for a_i, k in enumerate(ks):
            la, ga, na, kind_a, ida = items[k]
            for b_i in tree_.query(ga.buffer(0.3)):
                if b_i <= a_i: continue
                kb = ks[b_i]
                lb, gb, nb, kind_b, idb = items[kb]
                if ida == idb: continue
                d = ga.distance(gb)
                if na is not None and na == nb:
                    if d < 1e-4: u(k, kb)
                    continue
                if kind_a == 'pad' and kind_b == 'pad':
                    continue           # pad to pad is the footprint's business
                need = max(clear_of(na), clear_of(nb))
                if d < need - TOL:
                    if l == 'In1.Cu' and 'GND' in (na, nb):
                        pass
                    problems.append(('clearance', l, ida, na, idb, nb, round(d, 3), need))
    comps = defaultdict(set)
    for k, it in enumerate(items):
        if it[2] and it[3] == 'pad':
            comps[it[2]].add(f(k))
    unrouted = {n: len(c) - 1 for n, c in comps.items() if len(c) > 1}
    # edge
    edge = Polygon(kpcb.outline(tree)).exterior
    for l, g, n, kind, idd in items:
        if kind == 'pad': continue
        if g.distance(edge) < EDGE - TOL:
            problems.append(('edge', l, idd, n, '', '', round(g.distance(edge), 3), EDGE))
    # holes: via to via and via to through-hole
    holes = [(Point(v['x'], v['y']).buffer(v['drill'] / 2), v['net'], 'via%d' % i) for i, v in enumerate(vias)]
    holes += [(Point(p['x'], p['y']).buffer(p['drill'][0] / 2), p['net'], '%s.%s' % (p['ref'], p['num']))
              for p in pads if p['drill']]
    ht = STRtree([h[0] for h in holes])
    for i, (g, n, idd) in enumerate(holes):
        for j in ht.query(g.buffer(HOLE)):
            if j <= i or not idd.startswith('via'): continue
            d = g.distance(holes[j][0])
            if d < HOLE - TOL:
                problems.append(('hole', '', idd, n, holes[j][2], holes[j][1], round(d, 3), HOLE))
    seen = set(); uniq = []
    for p in problems:
        key = (p[0], p[2], p[4])
        if key not in seen:
            seen.add(key); uniq.append(p)
    print('tracks %d, vias %d' % (len(segs), len(vias)))
    print('unrouted nets: %d (%d connections)' % (len(unrouted), sum(unrouted.values())))
    for n, c in sorted(unrouted.items()):
        print('   ', n, c)
    kinds = defaultdict(int)
    for p in uniq: kinds[p[0]] += 1
    print('problems:', dict(kinds) or 'none')
    for p in uniq[:200 if verbose else 30]:
        print('   ', p)
    return unrouted, uniq


if __name__ == '__main__':
    run('-v' in sys.argv)
