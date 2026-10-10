"""Bring every track to its class width (nets.py: 0.254 / 0.508 / 0.762 / 1.0) and every segment to
0, 45 or 90 degrees.

Widths: a track that would then come closer than the clearance to another net's copper (or to the
board edge) steps down one width at a time, never below 0.254. Angles: an odd segment becomes an
orthogonal piece plus a 45 degree piece (either order), the first that keeps the clearance; one that
fits neither way is left and listed.
Usage: python3 widths.py
"""
import os, sys, re
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from shapely.geometry import Polygon, LineString, Point
from shapely.strtree import STRtree
import kpcb, check, nets

STEPS = [1.0, 0.762, 0.508, 0.254]
EDGE = 0.5
TOL = 0.002


def fmt(v):
    return ('%.4f' % v).rstrip('0').rstrip('.')


def main():
    t = open(kpcb.PCB).read()
    text, tree, fps, pads = kpcb.load()
    segs, vias = check.tracks(tree)
    inside = Polygon(kpcb.outline(tree)).buffer(-EDGE)
    fixed = {L: [] for L in kpcb.CU}            # (geom, net)
    for p in pads:
        g = Polygon(kpcb.pad_polygon(p))
        n = p['net'] if p['kind'] != 'np_thru_hole' else None
        for L in p['layers']:
            fixed[L].append((g, n))
    for v in vias:
        for L in kpcb.CU:
            fixed[L].append((Point(v['x'], v['y']).buffer(v['d'] / 2), v['net']))
    geoms = {}                                   # segment index -> current geometry
    def geom(s, w, pts=None):
        pts = pts or [s['a'], s['b']]
        return LineString(pts).buffer(w / 2) if pts[0] != pts[-1] else Point(pts[0]).buffer(w / 2)
    for k, s in enumerate(segs):
        geoms[k] = geom(s, s['w'])
    by_layer = {L: [k for k, s in enumerate(segs) if s['layer'] == L] for L in kpcb.CU}

    def clear(k, g):
        """g (for segment k) keeps its clearance to every other net's copper on its layer and to the edge."""
        s = segs[k]
        need = lambda n: max(nets.CLEAR[nets.kind(s['net'])] if s['net'] else 0.1524,
                             nets.CLEAR[nets.kind(n)] if n and not n.startswith('unconnected') else 0.1524)
        if not inside.contains(g):
            return False
        obs = [(o, n) for o, n in fixed[s['layer']] if n != s['net']]
        obs += [(geoms[m], segs[m]['net']) for m in by_layer[s['layer']] if m != k and segs[m]['net'] != s['net']]
        tr = STRtree([o for o, _ in obs])
        for i in tr.query(g.buffer(0.3)):
            if g.distance(obs[i][0]) < need(obs[i][1]) - TOL:
                return False
        return True

    # ---- widths
    changed = stepped = 0
    for k, s in enumerate(segs):
        if not s['net'] or s['net'].startswith('unconnected'): continue
        want = nets.width(s['net'])
        if abs(want - s['w']) < 1e-6: continue
        cands = [want] + [x for x in STEPS if x < want] if want in STEPS else [want]
        for w in cands:
            g = geom(s, w)
            if w <= s['w'] or clear(k, g):
                s['w2'] = w; geoms[k] = g
                changed += 1; stepped += (w != want)
                break
        else:
            s['w2'] = s['w']        # even the narrowest widening fails: leave it
    # ---- angles
    odd = left = 0
    for k, s in enumerate(segs):
        (x1, y1), (x2, y2) = s['a'], s['b']
        dx, dy = x2 - x1, y2 - y1
        if abs(dx) < 1e-6 or abs(dy) < 1e-6 or abs(abs(dx) - abs(dy)) < 1e-3: continue
        odd += 1
        w = s.get('w2', s['w'])
        m = min(abs(dx), abs(dy))
        sx, sy = (1 if dx > 0 else -1), (1 if dy > 0 else -1)
        options = [(x1 + sx * m, y1 + sy * m), (x2 - sx * m, y2 - sy * m)]   # diagonal first / orthogonal first
        for ww in [w] + [x for x in STEPS if x < w]:      # a tight one may fit narrower
            for mid in options:
                mid = (round(mid[0], 4), round(mid[1], 4))
                g = geom(s, ww, [s['a'], mid, s['b']])
                if clear(k, g):
                    s['mid'] = mid; s['w2'] = ww; geoms[k] = g
                    break
            if 'mid' in s:
                break
        else:
            left += 1
            print('  odd segment left: %s %s (%s)-(%s)' % (s['net'], s['layer'], s['a'], s['b']))
    print('widths: %d segments changed (%d stepped down); angles: %d odd, %d left' % (changed, stepped, odd, left))

    # ---- write back, in file order
    k = [0]
    def sub(m):
        s = segs[k[0]]; k[0] += 1
        b = m.group(0)
        w = s.get('w2', s['w'])
        b = re.sub(r'\(width [-\d.]+\)', '(width %s)' % fmt(w), b)
        if 'mid' in s:
            (mx, my) = s['mid']
            b2 = b.replace('(start %s %s)' % (fmt(s['a'][0]), fmt(s['a'][1])), '(start %s %s)' % (fmt(mx), fmt(my)), 1)
            b2 = re.sub(r'\(uuid "[^"]*"\)', '(uuid "%s")' % __import__('uuid').uuid4(), b2)
            b = b.replace('(end %s %s)' % (fmt(s['b'][0]), fmt(s['b'][1])), '(end %s %s)' % (fmt(mx), fmt(my)), 1)
            return b + b2
        return b
    t = re.sub(r'\n\t\(segment\n.*?\n\t\)', sub, t, flags=re.S)
    assert k[0] == len(segs)
    open(kpcb.PCB, 'w').write(t)


if __name__ == '__main__':
    main()
