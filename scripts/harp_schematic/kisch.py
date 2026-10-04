"""Minimal KiCad 10 schematic reader / net tracer / writer helpers.

parse(text) -> nested lists of str (atoms keep quotes stripped; strings are
marked by being instances of Str).
"""
import re, math, uuid as _uuid
from collections import defaultdict


class Str(str):
    pass


def parse(text):
    i, n = 0, len(text)
    stack = [[]]
    while i < n:
        c = text[i]
        if c == '(':
            stack.append([])
            i += 1
        elif c == ')':
            top = stack.pop()
            stack[-1].append(top)
            i += 1
        elif c == '"':
            j = i + 1
            buf = []
            while text[j] != '"':
                if text[j] == '\\':
                    buf.append(text[j:j + 2])
                    j += 2
                    continue
                buf.append(text[j])
                j += 1
            stack[-1].append(Str(''.join(buf)))
            i = j + 1
        elif c in ' \t\r\n':
            i += 1
        else:
            j = i
            while j < n and text[j] not in ' \t\r\n()':
                j += 1
            stack[-1].append(text[i:j])
            i = j
    return stack[0][0]


def find(node, key):
    return [c for c in node if isinstance(c, list) and c and c[0] == key]


def first(node, key):
    r = find(node, key)
    return r[0] if r else None


def prop(node, name):
    for p in find(node, 'property'):
        if p[1] == name:
            return p[2]
    return None


def _rot(x, y, ang):
    a = math.radians(ang)
    return (x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a))


def lib_pins(libsym, unit=None, convert=1):
    """Return list of (number, name, x, y, angle, length, type) in symbol coords (y up)."""
    out = []
    name = libsym[1]
    for sub in find(libsym, 'symbol'):
        # sub-unit names: NAME_U_C
        m = re.match(r'.*_(\d+)_(\d+)$', sub[1])
        u, cv = (int(m.group(1)), int(m.group(2))) if m else (0, 1)
        if unit is not None and u not in (0, unit):
            continue
        if cv not in (0, convert):
            continue
        for p in find(sub, 'pin'):
            at = first(p, 'at')
            ln = first(p, 'length')
            nm = first(p, 'name')
            nb = first(p, 'number')
            out.append((nb[1], nm[1], float(at[1]), float(at[2]),
                        float(at[3]) if len(at) > 3 else 0.0,
                        float(ln[1]) if ln else 0.0, p[1]))
    return out


def pin_endpoints(sym, libsyms):
    """Absolute sheet coordinates of each pin's connection point for a placed symbol."""
    ln = first(sym, 'lib_name')
    lib = libsyms[ln[1] if ln else first(sym, 'lib_id')[1]]
    at = first(sym, 'at')
    X, Y = float(at[1]), float(at[2])
    ang = float(at[3]) if len(at) > 3 else 0.0
    unit = first(sym, 'unit')
    unit = int(unit[1]) if unit else 1
    mirror = first(sym, 'mirror')
    res = []
    for nb, nm, px, py, pa, ln, typ in lib_pins(lib, unit):
        x, y = px, py
        if mirror and mirror[1] == 'y':
            x = -x
        if mirror and mirror[1] == 'x':
            y = -y
        # symbol coords are y-up; rotate in y-up space, then flip
        x, y = _rot(x, y, ang)
        res.append((nb, nm, round(X + x, 3), round(Y - y, 3), typ))
    return res


class UF:
    def __init__(self):
        self.p = {}

    def f(self, a):
        self.p.setdefault(a, a)
        while self.p[a] != a:
            self.p[a] = self.p[self.p[a]]
            a = self.p[a]
        return a

    def u(self, a, b):
        self.p[self.f(a)] = self.f(b)


def _on_seg(pt, a, b, eps=1e-3):
    (x, y), (x1, y1), (x2, y2) = pt, a, b
    if min(x1, x2) - eps <= x <= max(x1, x2) + eps and min(y1, y2) - eps <= y <= max(y1, y2) + eps:
        return abs((x2 - x1) * (y - y1) - (y2 - y1) * (x - x1)) < eps
    return False


def sheet_nets(root, sheet_prefix=''):
    """Net trace one sheet.

    Returns (pins, labels) where pins = list of (ref, pinnum, pinname, nodeid),
    labels = dict nodeid -> set of ('global'|'local'|'hier'|'power', name).
    Node ids are local to this call.
    """
    libsyms = {s[1]: s for s in find(first(root, 'lib_symbols') or [], 'symbol')}
    uf = UF()
    pts = []
    wires = []
    for w in find(root, 'wire'):
        xy = find(first(w, 'pts'), 'xy')
        a = (round(float(xy[0][1]), 3), round(float(xy[0][2]), 3))
        b = (round(float(xy[1][1]), 3), round(float(xy[1][2]), 3))
        wires.append((a, b))
        uf.u(a, b)
        pts += [a, b]
    attach = []  # (point, kind, payload)
    pins = []
    for s in find(root, 'symbol'):
        if not first(s, 'lib_id'):
            continue
        ref = prop(s, 'Reference')
        lid = first(s, 'lib_name')[1] if first(s, 'lib_name') else first(s, 'lib_id')[1]
        for nb, nm, x, y, typ in pin_endpoints(s, libsyms):
            pt = (x, y)
            if lid.startswith('power:') or (libsyms[lid] and first(libsyms[lid], 'power') is not None):
                attach.append((pt, 'power', prop(s, 'Value')))
            else:
                pins.append((ref, nb, nm, pt))
            pts.append(pt)
    for kind, key in (('global', 'global_label'), ('local', 'label'), ('hier', 'hierarchical_label')):
        for l in find(root, key):
            at = first(l, 'at')
            pt = (round(float(at[1]), 3), round(float(at[2]), 3))
            attach.append((pt, kind, l[1]))
            pts.append(pt)
    # sheet pins of subsheets
    for sh in find(root, 'sheet'):
        sname = prop(sh, 'Sheetname')
        for p in find(sh, 'pin'):
            at = first(p, 'at')
            pt = (round(float(at[1]), 3), round(float(at[2]), 3))
            attach.append((pt, 'sheetpin', (sname, p[1])))
            pts.append(pt)
    # no_connect markers
    for nc in find(root, 'no_connect'):
        at = first(nc, 'at')
        pt = (round(float(at[1]), 3), round(float(at[2]), 3))
        attach.append((pt, 'nc', ''))
        pts.append(pt)
    # T-junctions: any point lying on a wire interior joins that wire
    for pt in set(pts):
        uf.f(pt)
        for a, b in wires:
            if pt != a and pt != b and _on_seg(pt, a, b):
                uf.u(pt, a)
    labels = defaultdict(set)
    for pt, kind, name in attach:
        labels[uf.f(pt)].add((kind, name))
    pins = [(r, nb, nm, uf.f(pt)) for r, nb, nm, pt in pins]
    return pins, labels


def new_uuid():
    return str(_uuid.uuid4())
