"""Read the Harp board file: footprints, pads in board coordinates, the outline and the nets.

A small S-expression reader; no KiCad needed. Board coordinates are KiCad's (mm, Y down).
"""
import os, re, math

HERE = os.path.dirname(os.path.abspath(__file__))
PCB = os.path.join(HERE, '..', '..', 'kicad', 'the_harp', 'The Harp.kicad_pcb')
BUILD = os.path.join(HERE, 'build')
CU = ['F.Cu', 'In1.Cu', 'In2.Cu', 'B.Cu']

TOK = re.compile(r'\s*(?:(\()|(\))|"((?:[^"\\]|\\.)*)"|([^\s()"]+))')


def parse(text):
    """S-expression to nested lists. Quoted strings come back as str, atoms as str too."""
    stack, cur, pos = [], [], 0
    n = len(text)
    while pos < n:
        m = TOK.match(text, pos)
        if not m or m.end() == pos:
            break
        pos = m.end()
        if m.group(1):
            stack.append(cur); cur = []
        elif m.group(2):
            done = cur; cur = stack.pop(); cur.append(done)
        elif m.group(3) is not None:
            cur.append(m.group(3).replace('\\"', '"'))
        else:
            cur.append(m.group(4))
    return cur[0]


def find(node, key):
    for c in node:
        if isinstance(c, list) and c and c[0] == key:
            return c
    return None


def findall(node, key):
    return [c for c in node if isinstance(c, list) and c and c[0] == key]


def rot(x, y, a):
    """KiCad rotation: a in degrees, counter-clockwise on screen (Y down)."""
    r = math.radians(a)
    return x * math.cos(r) + y * math.sin(r), -x * math.sin(r) + y * math.cos(r)


def expand_layers(lays):
    out = []
    for l in lays:
        if l == '*.Cu':
            out += CU
        elif l == 'F&B.Cu':
            out += ['F.Cu', 'B.Cu']
        elif l in CU:
            out.append(l)
    return out


def load(path=PCB):
    text = open(path).read()
    tree = parse(text)
    fps, pads = [], []
    for f in findall(tree, 'footprint'):
        ref = next(c[2] for c in findall(f, 'property') if c[1] == 'Reference')
        at = find(f, 'at')
        X, Y = float(at[1]), float(at[2]); A = float(at[3]) if len(at) > 3 else 0.0
        side = find(f, 'layer')[1][0]
        fp = dict(ref=ref, x=X, y=Y, a=A, side=side, name=f[1], pads=[])
        for p in findall(f, 'pad'):
            num, kind, shape = p[1], p[2], p[3]
            pat = find(p, 'at')
            px, py = float(pat[1]), float(pat[2]); pa = float(pat[3]) if len(pat) > 3 else 0.0
            dx, dy = rot(px, py, A)
            size = find(p, 'size')
            drill = find(p, 'drill')
            dr = None
            if drill:
                vals = [v for v in drill[1:] if not isinstance(v, list)]
                if vals and vals[0] == 'oval':
                    dr = (float(vals[1]), float(vals[2]) if len(vals) > 2 else float(vals[1]))
                elif vals:
                    dr = (float(vals[0]), float(vals[0]))
            net = find(p, 'net')
            rr = find(p, 'roundrect_rratio')
            pad = dict(ref=ref, num=num, kind=kind, shape=shape, x=X + dx, y=Y + dy, a=pa,
                       w=float(size[1]), h=float(size[2]), drill=dr,
                       layers=expand_layers(find(p, 'layers')[1:]),
                       net=net[1] if net else None, rratio=float(rr[1]) if rr else 0.0)
            fp['pads'].append(pad); pads.append(pad)
        fps.append(fp)
    return text, tree, fps, pads


def outline(tree):
    """Edge.Cuts as one closed polygon (lines and arcs, arcs as 8 segments), board coordinates."""
    segs = []
    for kind in ('gr_line', 'gr_arc'):
        for g in findall(tree, kind):
            if find(g, 'layer')[1] != 'Edge.Cuts':
                continue
            s = tuple(map(float, find(g, 'start')[1:3])); e = tuple(map(float, find(g, 'end')[1:3]))
            if kind == 'gr_line':
                segs.append([s, e])
            else:
                m = tuple(map(float, find(g, 'mid')[1:3]))
                segs.append(arc_points(s, m, e, 8))
    # chain the pieces
    poly = list(segs.pop(0))
    while segs:
        last = poly[-1]
        for i, sg in enumerate(segs):
            if close(sg[0], last):
                poly += sg[1:]; segs.pop(i); break
            if close(sg[-1], last):
                poly += sg[::-1][1:]; segs.pop(i); break
        else:
            raise ValueError('outline does not close at %s' % (last,))
    if close(poly[0], poly[-1]):
        poly.pop()
    return poly


def close(a, b, eps=1e-3):
    return abs(a[0] - b[0]) < eps and abs(a[1] - b[1]) < eps


def arc_points(s, m, e, n):
    (x1, y1), (x2, y2), (x3, y3) = s, m, e
    d = 2 * (x1 * (y2 - y3) + x2 * (y3 - y1) + x3 * (y1 - y2))
    ux = ((x1 * x1 + y1 * y1) * (y2 - y3) + (x2 * x2 + y2 * y2) * (y3 - y1) + (x3 * x3 + y3 * y3) * (y1 - y2)) / d
    uy = ((x1 * x1 + y1 * y1) * (x3 - x2) + (x2 * x2 + y2 * y2) * (x1 - x3) + (x3 * x3 + y3 * y3) * (x2 - x1)) / d
    r = math.hypot(x1 - ux, y1 - uy)
    a1 = math.atan2(y1 - uy, x1 - ux); a2 = math.atan2(y2 - uy, x2 - ux); a3 = math.atan2(y3 - uy, x3 - ux)
    def norm(a):
        while a < a1: a += 2 * math.pi
        return a
    if norm(a2) < norm(a3):
        sweep = norm(a3) - a1
    else:
        sweep = norm(a3) - a1 - 2 * math.pi
    return [(ux + r * math.cos(a1 + sweep * i / n), uy + r * math.sin(a1 + sweep * i / n)) for i in range(n + 1)]


def pad_polygon(p, grow=0.0, n=4):
    """Pad copper outline as a polygon (board coordinates), grown by grow mm."""
    w, h = p['w'] / 2 + grow, p['h'] / 2 + grow
    if p['shape'] == 'circle':
        r = p['w'] / 2 + grow
        return [(p['x'] + r * math.cos(2 * math.pi * i / 16), p['y'] + r * math.sin(2 * math.pi * i / 16)) for i in range(16)]
    if p['shape'] in ('oval',):
        r = min(w, h)
    elif p['shape'] == 'roundrect':
        r = min(p['w'], p['h']) * p['rratio'] + grow
    else:
        r = grow if grow > 0 else 0.0
    pts = []
    for cx, cy, a0 in ((w - r, h - r, 0), (-(w - r), h - r, 90), (-(w - r), -(h - r), 180), (w - r, -(h - r), 270)):
        if r <= 1e-9:
            pts.append((cx, cy)); continue
        for i in range(n + 1):
            a = math.radians(a0 + 90 * i / n)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    out = []
    for x, y in pts:
        dx, dy = rot(x, y, p['a'])
        out.append((p['x'] + dx, p['y'] + dy))
    return out
