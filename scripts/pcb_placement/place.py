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
    fp = re.search(r'\(footprint "([^"]+)"', b).group(1)
    return dict(X=X, Y=Y, A=A, cy=cy, pads=pads, layer=layer, fp=fp)

L = {r: local(f['b']) for r, f in F.items()}
SIDE = {}          # ref -> 'F' or 'B' for parts the placer puts on a side other than their file layer

def bbox(ref, fx, fy, a, side=None):
    side = side or SIDE.get(ref, L[ref]['layer'][0])
    pts = [rot(x, -y if side != L[ref]['layer'][0] else y, a) for x, y in L[ref]['cy']]
    xs = [fx + p[0] for p in pts]; ys = [fy - p[1] for p in pts]     # face Y is up: board y down
    return (min(xs), max(xs), min(ys), max(ys))

def padpos(ref, fx, fy, a, side=None):
    side = side or SIDE.get(ref, L[ref]['layer'][0])
    flip = side != L[ref]['layer'][0]
    out = []
    for p in L[ref]['pads']:
        rx, ry = rot(p['lx'], -p['ly'] if flip else p['ly'], a)
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
pos['U201'] = (0.0, -7.0, 0.0)             # under the OLED (option 1, 2026-10-09): the centre is free once Retune moves down
pos['SW102'] = (2.415, -28.7, 0.0)         # Retune toggle bat at face (0, -24) (footprint origin = bat + (2.415, -4.7))
FIXED += ['D114', 'U201']
TALL = {'K401', 'C502', 'C508'}            # taller than ~4 mm: kept out from under the OLED module
MODULE = (-19.0, 19.0, -11.25, 1.25)      # OLED module outline, window centred at (0, -5)

occ = []      # top side: (x0, x1, y0, y1, owner)
occb = []     # bottom side
def add_fixed(r):
    fx, fy, a = pos[r][:3]
    side = L[r]['layer'][0]
    (occ if side == 'F' else occb).append(bbox(r, fx, fy, a) + (r,))
    for p, px, py in padpos(r, fx, fy, a):          # through-holes block the other side too
        if p['kind'] in ('thru_hole', 'np_thru_hole'):
            s_ = max(p['w'], p['h']) / 2 + 0.5
            (occb if side == 'F' else occ).append((px - s_, px + s_, py - s_, py + s_, r + ':hole'))
for r in FIXED:
    add_fixed(r)

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

def free(b, gap=0.05, side='F'):
    x0, x1, y0, y1 = b
    for o in (occ if side == 'F' else occb):
        if x0 < o[1] + gap and x1 > o[0] - gap and y0 < o[3] + gap and y1 > o[2] - gap:
            return False
    return True

def holes_free(ref, x, y, a, side):
    for p, px, py in padpos(ref, x, y, a, side):
        if p['kind'] in ('thru_hole', 'np_thru_hole'):
            s_ = max(p['w'], p['h']) / 2 + 0.3
            if not free((px - s_, px + s_, py - s_, py + s_), 0, 'B' if side == 'F' else 'F'):
                return False
    return True

GRID = 0.5
PREF = {}          # (group, footprint) -> preferred rotation, so like parts in a group share an orientation
GROUP_OF = {}      # ref -> group name, set by the run script

def find_spot(ref, tx, ty, rots=(0, 90), rmax=45, step=GRID, side='F'):
    """Nearest free spot on the grid to (tx, ty); among spots within 1.5 mm of the nearest, prefer ones that line up
    with parts of the same group (same X or Y centre) and the group's usual rotation for this footprint."""
    tx, ty = round(tx / step) * step, round(ty / step) * step
    grp = GROUP_OF.get(ref)
    mates = [(pos[r][0], pos[r][1]) for r in pos if GROUP_OF.get(r) == grp and r != ref] if grp else []
    pref = PREF.get((grp, L[ref]['fp'] if 'fp' in L[ref] else None))
    found, r0 = [], None
    n = int(rmax / step)
    for k in range(n):
        r = k * step
        if r0 is not None and r > r0 + 2.5:
            break
        m = max(1, int(2 * math.pi * r / step))
        seen = set()
        for i in range(m):
            th = 2 * math.pi * i / m
            x = round((tx + r * math.cos(th)) / step) * step; y = round((ty + r * math.sin(th)) / step) * step
            if (x, y) in seen: continue
            seen.add((x, y))
            for a in rots:
                b = bbox(ref, x, y, a, side)
                if in_board(b) and free(b, side=side) and holes_free(ref, x, y, a, side):
                    if r0 is None: r0 = r
                    d = math.hypot(x - tx, y - ty)
                    al = any(abs(x - mx) < 1e-6 or abs(y - my) < 1e-6 for mx, my in mates)
                    score = d + (0 if al or not mates else 2.0) + (0 if pref is None or a % 180 == pref % 180 else 1.0)
                    found.append((score, x, y, a, b))
    if not found:
        return None
    found.sort(key=lambda f: f[0])
    _, x, y, a, b = found[0]
    if grp is not None:
        PREF.setdefault((grp, L[ref].get('fp')), a)
    return x, y, a, b

POWER = {'GND', '+3V3', '+5V', '+9V', 'VDDA'}
def place(ref, tx, ty, rots=(0, 90), side='F'):
    SIDE[ref] = side
    if ref in TALL and side == 'F':
        occ.append(MODULE + ('module',))
    s = find_spot(ref, tx, ty, rots, rmax=100, side=side)
    if ref in TALL:
        occ[:] = [o for o in occ if o[4] != 'module']
    if not s:
        print('NO ROOM', ref); return False
    x, y, a, b = s
    pos[ref] = (x, y, a); (occ if side == 'F' else occb).append(b + (ref,))
    for p, px, py in padpos(ref, x, y, a, side):
        if p['kind'] in ('thru_hole', 'np_thru_hole'):
            s_ = max(p['w'], p['h']) / 2 + 0.3
            (occb if side == 'F' else occ).append((px - s_, px + s_, py - s_, py + s_, ref + ':hole'))
    return True

def placed_pads(net, refs=None):
    out = []
    for r, (x, y, a) in pos.items():
        if refs and r not in refs: continue
        for p, px, py in padpos(r, x, y, a):
            if p['net'] == net: out.append((px, py))
    return out

BIAS = {'VCOM_A', 'VCOM_B', '/Codec/VCOM'}    # DC bias nets run everywhere: they do not pull parts

def target(ref, home):
    """Centroid of placed pads on this part's signal nets (bias nets ignored unless that is all it has);
    decoupling parts: a supply pin of their group IC."""
    sig = [p['net'] for p in L[ref]['pads'] if p['net'] and p['net'] not in POWER and not p['net'].startswith('unconnected')]
    sig = [n for n in sig if n not in BIAS] or sig
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
