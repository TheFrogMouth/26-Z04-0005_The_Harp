"""Footprint geometry from the Harp PCB: courtyard boxes and pads in face coordinates."""
import os
HERE = os.path.dirname(os.path.abspath(__file__))
import re, math, sys
sys.path.insert(0, HERE)
from pcbread import footprints, PCB

def rot(x, y, a):
    r = math.radians(a)
    return x * math.cos(r) + y * math.sin(r), -x * math.sin(r) + y * math.cos(r)

def to_face(px, py):
    return px - 148.5, 105 - py

def parse_fp(f):
    b = f['b']
    at = re.search(r'\n\t\t\(at ([-\d.]+) ([-\d.]+)(?: ([-\d.]+))?\)', b)
    X, Y, A = float(at.group(1)), float(at.group(2)), float(at.group(3) or 0)
    layer = re.search(r'\n\t\t\(layer "([^"]+)"\)', b).group(1)
    pts = {'F': [], 'B': []}
    for m in re.finditer(r'\n\t\t\(fp_(line|rect|poly|circle|arc)(.*?)\n\t\t\)', b, re.S):
        body = m.group(2)
        lay = re.search(r'\(layer "([^"]+)"\)', body).group(1)
        if 'CrtYd' not in lay: continue
        side = lay[0]
        xy = [(float(a), float(c)) for a, c in re.findall(r'\((?:start|end|mid|center|xy) ([-\d.]+) ([-\d.]+)\)', body)]
        if m.group(1) == 'circle':
            c = re.search(r'\(center ([-\d.]+) ([-\d.]+)\)', body); e = re.search(r'\(end ([-\d.]+) ([-\d.]+)\)', body)
            cx, cy = float(c.group(1)), float(c.group(2)); rr = math.hypot(float(e.group(1)) - cx, float(e.group(2)) - cy)
            xy = [(cx - rr, cy - rr), (cx + rr, cy + rr), (cx - rr, cy + rr), (cx + rr, cy - rr)]
        pts[side] += xy
    cy = {}
    for side, P in pts.items():
        if not P: continue
        Q = [to_face(X + rx, Y + ry) for rx, ry in (rot(x, y, A) for x, y in P)]
        xs = [q[0] for q in Q]; ys = [q[1] for q in Q]
        cy[side] = (min(xs), max(xs), min(ys), max(ys))
    pads = []
    for m in re.finditer(r'\(pad "([^"]*)" (\w+) (\w+)\n\t\t\t\(at ([-\d.]+) ([-\d.]+)(?: ([-\d.]+))?\)\n\t\t\t\(size ([-\d.]+) ([-\d.]+)\)', b):
        rx, ry = rot(float(m.group(4)), float(m.group(5)), A)
        fx, fy = to_face(X + rx, Y + ry)
        pads.append(dict(num=m.group(1), kind=m.group(2), x=fx, y=fy, w=float(m.group(7)), h=float(m.group(8))))
    fx, fy = to_face(X, Y)
    return dict(ref=f['ref'], layer=layer, x=fx, y=fy, a=A, cy=cy, pads=pads,
                fp=re.search(r'\(footprint "([^"]+)"', b).group(1))

def load():
    t = open(PCB).read()
    return t, [parse_fp(f) for f in footprints(t)]

def box(g):
    c = g['cy'].get('F') or g['cy'].get('B')
    if c: return c
    xs = [p['x'] for p in g['pads']]; ys = [p['y'] for p in g['pads']]
    return (min(xs) - 1, max(xs) + 1, min(ys) - 1, max(ys) + 1)

def on_board(g):
    return -28 < g['x'] < 28 and -38 < g['y'] < 57
