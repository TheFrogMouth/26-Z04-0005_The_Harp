"""Greedy zoned placement for The Harp (face coordinates, top side)."""
import os
HERE = os.path.dirname(os.path.abspath(__file__))
import re, math, sys, json
sys.path.insert(0, HERE)
from pcbread import footprints, PCB
from geom import rot, to_face

t = open(PCB).read()
F = {f['ref']: f for f in footprints(t)}

def local(b):
    at = re.search(r'\n\t\t\(at ([-\d.]+) ([-\d.]+)(?: ([-\d.]+))?\)', b)
    X, Y, A = float(at.group(1)), float(at.group(2)), float(at.group(3) or 0)
    cy = []
    for m in re.finditer(r'\n\t\t\(fp_(line|rect|poly|arc|circle)(.*?)\n\t\t\)', b, re.S):
        if 'CrtYd' in re.search(r'\(layer "([^"]+)"\)', m.group(2)).group(1):
            cy += [(float(a), float(c)) for a, c in re.findall(r'\((?:start|end|mid|xy) ([-\d.]+) ([-\d.]+)\)', m.group(2))]
    pads = []
    for m in re.finditer(r'\(pad "([^"]*)" (\w+) \w+\n\t\t\t\(at ([-\d.]+) ([-\d.]+)(?: [-\d.]+)?\)\n\t\t\t\(size ([-\d.]+) ([-\d.]+)\)(.*?)\n\t\t\)', b, re.S):
        net = re.search(r'\(net "([^"]*)"\)', m.group(7))
        pads.append(dict(num=m.group(1), kind=m.group(2), lx=float(m.group(3)), ly=float(m.group(4)),
                         w=float(m.group(5)), h=float(m.group(6)), net=net.group(1) if net else None))
    if not cy:   # no courtyard (IC501): pads + 0.5 mm
        for p in pads:
            cy += [(p['lx'] - p['w'] / 2 - .5, p['ly'] - p['h'] / 2 - .5), (p['lx'] + p['w'] / 2 + .5, p['ly'] + p['h'] / 2 + .5)]
        cy += [(-3.9, -4.6), (3.9, 4.6)]
    layer = re.search(r'\n\t\t\(layer "([^"]+)"\)', b).group(1)
    return dict(X=X, Y=Y, A=A, cy=cy, pads=pads, layer=layer)

L = {r: local(f['b']) for r, f in F.items()}

def bbox(ref, fx, fy, a):
    pts = [rot(x, y, a) for x, y in L[ref]['cy']]
    xs = [fx + p[0] for p in pts]; ys = [fy - p[1] for p in pts]     # face Y is up: board y down
    return (min(xs), max(xs), min(ys), max(ys))

def padpos(ref, fx, fy, a):
    out = []
    for p in L[ref]['pads']:
        rx, ry = rot(p['lx'], p['ly'], a)
        out.append((p, fx + rx, fy - ry))
    return out

def face_of(ref):
    return to_face(L[ref]['X'], L[ref]['Y']) + (L[ref]['A'],)

# ---------------------------------------------------------------- fixed parts and keep-outs
FIXED = ['RV101', 'RV102', 'RV103', 'RV105', 'SW101', 'SW102', 'SW103', 'J401', 'J402', 'J403', 'J404', 'J406',
         'D113']
pos = {}
for r in FIXED:
    pos[r] = face_of(r)
pos['D114'] = (18.73, -35.0, 0.0)          # mirror of D113 (LED centre at pad 1 + 1.27)
pos['U201'] = (0.0, -21.5, 0.0)            # the only 17.5 mm square on the board: between the lower jack pins, under SW102
FIXED += ['D114', 'U201']
TALL = {'K401', 'C502', 'C508'}            # taller than ~4 mm: kept out from under the OLED module
MODULE = (-19.0, 19.0, -26.25, -13.75)

occ = []      # (x0, x1, y0, y1, owner)
for r in FIXED:
    fx, fy, a = pos[r]
    if L[r]['layer'] == 'F.Cu':
        occ.append(bbox(r, fx, fy, a) + (r,))
    for p, px, py in padpos(r, fx, fy, a):          # through-hole pads of underside parts land on the top too
        if p['kind'] == 'thru_hole' and L[r]['layer'] == 'B.Cu':
            s = max(p['w'], p['h']) / 2 + 0.5
            occ.append((px - s, px + s, py - s, py + s, r + ':pad'))

E = 0.3                                              # courtyard to board edge
def in_board(b):
    x0, x1, y0, y1 = b
    if y1 > 52 - E:                                  # the DC tab: 18 mm wide to +56.5
        if not (x0 >= -9 + E and x1 <= 9 - E and y1 <= 56.5 - E and y0 >= -38 + E): return False
        return True
    if x0 < -28 + E or x1 > 28 - E or y0 < -38 + E: return False
    for cx, cy in ((-26, 50), (26, 50), (-26, -36), (26, -36)):     # R2 corners
        px = x0 if cx < 0 else x1; py = y1 if cy > 0 else y0
        if (px - cx) * (1 if cx > 0 else -1) > 0 and (py - cy) * (1 if cy > 0 else -1) > 0:
            if math.hypot(px - cx, py - cy) > 2 - E: return False
    return True

def free(b, gap=0.05):
    x0, x1, y0, y1 = b
    for o in occ:
        if x0 < o[1] + gap and x1 > o[0] - gap and y0 < o[3] + gap and y1 > o[2] - gap:
            return False
    return True

def find_spot(ref, tx, ty, rots=(0, 90), rmax=45, step=0.25):
    best = None
    n = int(rmax / step)
    for k in range(n):
        r = k * step
        cands = []
        m = max(1, int(2 * math.pi * r / step))
        for i in range(m):
            th = 2 * math.pi * i / m
            cands.append((tx + r * math.cos(th), ty + r * math.sin(th)))
        for x, y in cands:
            x = round(x / step) * step; y = round(y / step) * step
            for a in rots:
                b = bbox(ref, x, y, a)
                if in_board(b) and free(b):
                    return x, y, a, b
    return None

POWER = {'GND', '+3V3', '+5V', '+9V', 'VDDA'}
def place(ref, tx, ty, rots=(0, 90)):
    if ref in TALL:
        occ.append(MODULE + ('module',))
    s = find_spot(ref, tx, ty, rots, rmax=100)
    if ref in TALL:
        occ[:] = [o for o in occ if o[4] != 'module']
    if not s:
        print('NO ROOM', ref); return False
    x, y, a, b = s
    pos[ref] = (x, y, a); occ.append(b + (ref,))
    return True

def placed_pads(net, refs=None):
    out = []
    for r, (x, y, a) in pos.items():
        if refs and r not in refs: continue
        for p, px, py in padpos(r, x, y, a):
            if p['net'] == net: out.append((px, py))
    return out

def target(ref, home):
    """Centroid of placed pads on this part's signal nets; decoupling parts: nearest placed pad of their supply net in the group."""
    sig = [p['net'] for p in L[ref]['pads'] if p['net'] and p['net'] not in POWER and not p['net'].startswith('unconnected')]
    pts = []
    for n in sig:
        pts += placed_pads(n)
    if pts:
        return sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts)
    pw = [p['net'] for p in L[ref]['pads'] if p['net'] in POWER and p['net'] != 'GND']
    if pw and home.get('ic') in pos:
        cand = placed_pads(pw[0], {home['ic']})
        if cand:
            used = home.setdefault('used', {})
            k = used.get(pw[0], 0); used[pw[0]] = k + 1
            return cand[k % len(cand)]
    return home['xy']
