"""Hand-laid-out sheets for the Harp generator.

A sheet layout places every part of a spec sheet (harp_spec.py) on the
2.54 mm grid, draws the wires between pins explicitly, and puts a power
symbol or a global label where the spec says a pin meets a rail or a net
from another sheet. Junctions are added automatically wherever three or
more wire ends or pins meet. The result is checked by build.py pin by pin
against the spec, and by the checks at the bottom of this file (dangling
wires, wires through symbol bodies, overlapping wires, off-grid pins,
overlapping text).

Coordinates are sheet millimetres, y down, as in the .kicad_sch file.
"""
import math, re
from collections import defaultdict
import schgen
from schgen import symbol_block, wire as wire_block, no_connect, uid, _eff, POWER_NETS
from kisch import lib_pins, find, first

G = 2.54
FONT = 'Oswald'


def g(v):
    return round(round(v / 1.27) * 1.27, 3)


def _rot(x, y, ang):
    a = math.radians(ang)
    return (x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a))


class Placed:
    def __init__(self, part, x, y, ang, mirror):
        self.part, self.x, self.y, self.ang, self.mirror = part, x, y, ang, mirror
        self.lib = schgen.libnode(part.lib)
        self.pins = {}      # number -> (x, y, ox, oy)  ox,oy = outward unit vector (away from body)
        for nb, nm, px, py, pa, ln, typ in lib_pins(self.lib, part.unit):
            x1, y1 = px, py
            dx, dy = math.cos(math.radians(pa)), math.sin(math.radians(pa))   # toward body, y up
            if mirror == 'y':
                x1, dx = -x1, -dx
            if mirror == 'x':
                y1, dy = -y1, -dy
            x1, y1 = _rot(x1, y1, ang)
            dx, dy = _rot(dx, dy, ang)
            self.pins[nb] = (round(x + x1, 3), round(y - y1, 3), -round(dx), round(dy))
        self.ref_pos = self.val_pos = None
        self.hide_val = False

    def body_edges(self):
        """Sheet-space edges of the drawn body: rectangle sides, polyline legs, circles/arcs as their bbox."""
        edges = []

        def T(px, py):
            if self.mirror == 'y':
                px = -px
            if self.mirror == 'x':
                py = -py
            px, py = _rot(px, py, self.ang)
            return (self.x + px, self.y - py)
        for sub in find(self.lib, 'symbol'):
            m = re.match(r'.*_(\d+)_(\d+)$', sub[1])
            u, cv = (int(m.group(1)), int(m.group(2))) if m else (0, 1)
            if u not in (0, self.part.unit) or cv not in (0, 1):
                continue
            for gi in sub:
                if not isinstance(gi, list):
                    continue
                if gi[0] == 'rectangle':
                    s_, e = first(gi, 'start'), first(gi, 'end')
                    x0, y0, x1, y1 = float(s_[1]), float(s_[2]), float(e[1]), float(e[2])
                    pts = [T(x0, y0), T(x1, y0), T(x1, y1), T(x0, y1), T(x0, y0)]
                elif gi[0] == 'polyline':
                    pts = [T(float(p[1]), float(p[2])) for p in find(first(gi, 'pts'), 'xy')]
                elif gi[0] in ('circle', 'arc'):
                    if gi[0] == 'circle':
                        c, r = first(gi, 'center'), float(first(gi, 'radius')[1])
                        cx, cy = float(c[1]), float(c[2])
                        pts = [T(cx - r, cy - r), T(cx + r, cy - r), T(cx + r, cy + r), T(cx - r, cy + r), T(cx - r, cy - r)]
                    else:
                        pts = [T(float(first(gi, k)[1]), float(first(gi, k)[2])) for k in ('start', 'mid', 'end')]
                else:
                    continue
                edges += list(zip(pts, pts[1:]))
        return edges

    def body_bbox(self):
        """Sheet-space bbox of the drawn body (graphics only, no pins)."""
        xs, ys = [], []
        for sub in find(self.lib, 'symbol'):
            m = re.match(r'.*_(\d+)_(\d+)$', sub[1])
            u, cv = (int(m.group(1)), int(m.group(2))) if m else (0, 1)
            if u not in (0, self.part.unit) or cv not in (0, 1):
                continue
            for gi in sub:
                if not isinstance(gi, list):
                    continue
                pts = []
                if gi[0] == 'rectangle':
                    s, e = first(gi, 'start'), first(gi, 'end')
                    pts = [(float(s[1]), float(s[2])), (float(e[1]), float(e[2]))]
                elif gi[0] in ('polyline',):
                    pts = [(float(p[1]), float(p[2])) for p in find(first(gi, 'pts'), 'xy')]
                elif gi[0] == 'circle':
                    c, r = first(gi, 'center'), float(first(gi, 'radius')[1])
                    pts = [(float(c[1]) - r, float(c[2]) - r), (float(c[1]) + r, float(c[2]) + r)]
                elif gi[0] == 'arc':
                    pts = [(float(first(gi, k)[1]), float(first(gi, k)[2])) for k in ('start', 'mid', 'end')]
                for px, py in pts:
                    if self.mirror == 'y':
                        px = -px
                    if self.mirror == 'x':
                        py = -py
                    px, py = _rot(px, py, self.ang)
                    xs.append(self.x + px)
                    ys.append(self.y - py)
        if not xs:
            return None
        return (min(xs), min(ys), max(xs), max(ys))


class Layout:
    def __init__(self, sheet, global_nets, project, root_uuid):
        self.sheet = sheet
        self.glob = global_nets
        self.project, self.root_uuid = project, root_uuid
        self.path = '/%s/%s' % (root_uuid, sheet.uuid)
        self.parts = {}            # (ref, unit) -> Part
        for p in sheet.parts:
            self.parts[(p.ref, p.unit)] = p
        self.placed = {}           # (ref, unit) -> Placed
        self.wires = []            # list of (a, b)
        self.powers = []           # (net, x, y, ang, valpos, valjust)
        self.labels = []           # (name, x, y, ang, just)
        self.locals = []           # (name, x, y, ang, just)  local labels, justified in the PR
        self.ncs = []
        self.texts = []            # (s, x, y, size, bold)
        self.flags = []            # (net, x, y)
        self.problems = []

    # ------------------------------------------------------------ placing
    def at(self, ref, x, y, ang=0, mirror=None, unit=1, ref_pos=None, val_pos=None, hide_val=False):
        """Place part `ref` (unit `unit`) with its origin at (x, y). ref_pos/val_pos: (x, y, justify[, angle])."""
        key = (ref, unit)
        if key not in self.parts:
            raise KeyError('%s unit %d is not on sheet %s' % (ref, unit, self.sheet.name))
        p = Placed(self.parts[key], g(x), g(y), ang, mirror)
        p.ref_pos, p.val_pos, p.hide_val = ref_pos, val_pos, hide_val
        self.placed[key] = p
        return p

    def pin(self, ref, nb, unit=None):
        """Sheet point of a pin end. unit=None: find the unit that has it."""
        nb = str(nb)
        cands = [p for (r, u), p in self.placed.items() if r == ref and (unit is None or u == unit)]
        for p in cands:
            if nb in p.pins:
                return p.pins[nb][:2]
        raise KeyError('pin %s of %s not placed' % (nb, ref))

    def pindir(self, ref, nb, unit=None):
        nb = str(nb)
        for (r, u), p in self.placed.items():
            if r == ref and (unit is None or u == unit) and nb in p.pins:
                return p.pins[nb][2:]
        raise KeyError('pin %s of %s not placed' % (nb, ref))

    def P(self, spec):
        """Resolve a point spec: (x, y), ('R301', '1') or ('U701', '3', unit)."""
        if isinstance(spec, tuple) and len(spec) >= 2 and isinstance(spec[0], str):
            return self.pin(*spec)
        return (round(spec[0], 3), round(spec[1], 3))

    # ------------------------------------------------------------ wiring
    def w(self, *pts):
        """Wire through the given points. Each leg must be horizontal or vertical.
        'H' between two points inserts a corner going horizontal first, 'V' vertical first."""
        res = []
        pending = None
        for p in pts:
            if p in ('H', 'V'):
                pending = p
                continue
            q = self.P(p)
            if res:
                a = res[-1]
                if pending:
                    corner = (q[0], a[1]) if pending == 'H' else (a[0], q[1])
                    if corner != a and corner != q:
                        res.append(corner)
                    pending = None
                elif a[0] != q[0] and a[1] != q[1]:
                    raise ValueError('diagonal wire %s -> %s on %s' % (a, q, self.sheet.name))
            res.append(q)
        for a, b in zip(res, res[1:]):
            if a != b:
                self.wires.append((a, b))
        return res

    def stub(self, ref, nb, length=G, unit=None):
        """Wire from a pin end outward by `length`; returns the far end."""
        x, y = self.pin(ref, nb, unit)
        ox, oy = self.pindir(ref, nb, unit)
        e = (round(x + ox * length, 3), round(y + oy * length, 3))
        self.w((x, y), e)
        return e

    def gnd(self, spec, dir='down', length=0):
        """GND symbol at the point (or at the end of a stub of `length` from the pin)."""
        self.pwr('GND', spec, dir, length)

    def pwr(self, net, spec, dir='up', length=0):
        """Power symbol for `net` at the point; `dir` is where its body points.
        If spec is a pin and length > 0, a stub of that length is drawn first."""
        if isinstance(spec, tuple) and isinstance(spec[0], str) and length:
            x, y = self.stub(spec[0], spec[1], length, spec[2] if len(spec) > 2 else None)
        else:
            x, y = self.P(spec)
        down = net == 'GND'
        # power symbol library: pin at origin, body drawn upward (+y in symbol space) for rails, downward for GND
        if dir == 'up':
            ang = 180 if down else 0
            valpos, just = (x, round(y - 3.5, 2)), 'center'
        elif dir == 'down':
            ang = 0 if down else 180
            valpos, just = (x, round(y + 3.5, 2)), 'center'
        elif dir == 'left':
            ang = 270 if down else 90
            valpos, just = (round(x - 3.0, 2), y), 'right'
        else:
            ang = 90 if down else 270
            valpos, just = (round(x + 3.0, 2), y), 'left'
        self.powers.append((net, x, y, ang, valpos, just))
        return (x, y)

    def gl(self, name, spec, dir='left', length=0, shape=None):
        """Global label at the point. `dir` is the side the label body extends to."""
        if isinstance(spec, tuple) and isinstance(spec[0], str) and length:
            x, y = self.stub(spec[0], spec[1], length, spec[2] if len(spec) > 2 else None)
        else:
            x, y = self.P(spec)
        ang = {'right': 0, 'left': 180, 'up': 90, 'down': 270}[dir]
        just = {'right': 'left', 'left': 'right', 'up': 'left', 'down': 'right'}[dir]
        self.labels.append((name, x, y, ang, just, shape))
        return (x, y)

    def local(self, name, spec, dir='right', length=0):
        """Local label (the standard allows one only where a wire would be unreasonable)."""
        if isinstance(spec, tuple) and isinstance(spec[0], str) and length:
            x, y = self.stub(spec[0], spec[1], length, spec[2] if len(spec) > 2 else None)
        else:
            x, y = self.P(spec)
        ang = {'right': 0, 'left': 180, 'up': 90, 'down': 270}[dir]
        just = {'right': 'left', 'left': 'right', 'up': 'left', 'down': 'right'}[dir]
        self.locals.append((name, x, y, ang, just))
        return (x, y)

    def nc(self, ref, nb, unit=None):
        self.ncs.append(self.pin(ref, nb, unit))

    def text(self, s, x, y, size=1.27, bold=False):
        self.texts.append((s, x, y, size, bold))

    def flag(self, spec, dir='up'):
        """PWR_FLAG on a rail point: a 2.54 mm stub from the point in `dir` to the flag symbol."""
        x, y = self.P(spec)
        dx, dy = {'up': (0, -1), 'down': (0, 1), 'left': (-1, 0), 'right': (1, 0)}[dir]
        end = (round(x + dx * G, 3), round(y + dy * G, 3))
        self.flags.append((end[0], end[1], dir))
        self.wires.append(((x, y), end))

    # ------------------------------------------------------------ bookkeeping
    def split(self):
        """Split every wire at the pin ends, labels, power symbols and wire ends lying on its interior,
        so each wire ends where it connects (the standard: no wire across a pin end)."""
        pts = set(self._points())
        for p in self.placed.values():
            for nb, (x, y, ox, oy) in p.pins.items():
                pts.add((x, y))
        out = []
        for a, b in self.wires:
            inner = sorted((q for q in pts if q != a and q != b and _on_seg(q, a, b)),
                           key=lambda q: (q[0] - a[0]) ** 2 + (q[1] - a[1]) ** 2)
            prev = a
            for q in inner:
                out.append((prev, q))
                prev = q
            out.append((prev, b))
        self.wires = out

    def auto(self):
        """Pins not wired by the layout: raise, so nothing is silently dropped."""
        missing = []
        pts = self._points()
        for key, p in self.placed.items():
            for nb, (x, y, ox, oy) in p.pins.items():
                if self.parts[key].pins.get(nb, 'MISSING') is None:
                    if (x, y) not in self.ncs:
                        self.ncs.append((x, y))
                    continue
                if (x, y) not in pts and not any(_on_seg((x, y), a, b) for a, b in self.wires):
                    missing.append('%s.%s at %s' % (key[0], nb, (x, y)))
        for key in self.parts:
            if key not in self.placed:
                missing.append('%s unit %d not placed' % key)
        if missing:
            raise SystemExit('%s: unconnected or unplaced: %s' % (self.sheet.name, missing))

    def _points(self):
        pts = set()
        for a, b in self.wires:
            pts.add(a)
            pts.add(b)
        for n, x, y, *_ in self.powers:
            pts.add((x, y))
        for n, x, y, *_ in self.labels + self.locals:
            pts.add((x, y))
        for x, y, d in self.flags:
            pts.add((x, y))
        return pts

    def junctions(self):
        cnt = defaultdict(int)
        for a, b in self.wires:
            cnt[a] += 1
            cnt[b] += 1
        for p in self.placed.values():
            for nb, (x, y, ox, oy) in p.pins.items():
                cnt[(x, y)] += 1
        for n, x, y, *_ in self.powers:
            cnt[(x, y)] += 1
        for n, x, y, *_ in self.labels + self.locals:
            cnt[(x, y)] += 1
        for x, y, d in self.flags:
            cnt[(x, y)] += 1
        # points on the interior of a wire
        for pt in list(cnt):
            for a, b in self.wires:
                if pt != a and pt != b and _on_seg(pt, a, b):
                    cnt[pt] += 2
        return sorted(pt for pt, n in cnt.items() if n >= 3)

    # ------------------------------------------------------------ emit
    def emit(self):
        self.split()
        self.auto()
        body, used = [], set()
        for key, p in sorted(self.placed.items(), key=lambda kv: (kv[1].y, kv[1].x, kv[0])):
            part = p.part
            used.add(part.lib)
            unitpins = sorted(p.pins, key=lambda s: (len(s), s))
            lp = lib_pins(p.lib)
            n_units = len({re.match(r'.*_(\d+)_\d+$', s[1]).group(1) for s in find(p.lib, 'symbol')} - {'0'})
            rx, ry, rj, ra, vx, vy, vj, va = self._text_positions(p)
            hide_val = p.hide_val
            body.append(symbol_block(part.lib, part.ref, part.value, p.x, p.y, p.ang, part.unit, self.path, self.project,
                                     part.fp, part.dnp, dict(part.props), pins=unitpins, refpos=(rx, ry), valpos=(vx, vy),
                                     desc=part.note or '', mirror=p.mirror, refjust=rj, valjust=vj, refang=ra, valang=va,
                                     hide_val=hide_val))
        for a, b in self.wires:
            body.append(wire_block(a, b))
        for pt in self.junctions():
            body.append('\t(junction\n\t\t(at %s %s)\n\t\t(diameter 0)\n\t\t(color 0 0 0 0)\n\t\t(uuid "%s")\n\t)' % (pt[0], pt[1], uid()))
        for net, x, y, ang, valpos, just in self.powers:
            used.add('power:' + net)
            body.append(symbol_block('power:' + net, '#PWR@', net, x, y, ang, 1, self.path, self.project, hide_ref=True,
                                     valpos=valpos, valjust=just, pins=['1']))
        for x, y, dir in self.flags:
            used.add('power:PWR_FLAG')
            ang = {'up': 0, 'right': 270, 'down': 180, 'left': 90}[dir]
            vp, vj = {'up': ((x, round(y - 3.2, 2)), 'center'), 'down': ((x, round(y + 3.2, 2)), 'center'),
                      'right': ((round(x + 3.2, 2), y), 'left'), 'left': ((round(x - 3.2, 2), y), 'right')}[dir]
            body.append(symbol_block('power:PWR_FLAG', '#FLG@', 'PWR_FLAG', x, y, ang, 1, self.path, self.project,
                                     hide_ref=True, valpos=vp, valjust=vj, pins=['1']))
        for name, x, y, ang, just, shape in self.labels:
            body.append(_glabel(name, x, y, ang, just, shape or 'passive'))
        for name, x, y, ang, just in self.locals:
            body.append('\t(label "%s"\n\t\t(at %s %s %s)\n\t\t(fields_autoplaced yes)\n\t\t%s\n\t\t(uuid "%s")\n\t)'
                        % (name, x, y, ang, _eff(just + ' bottom'), uid()))
        for x, y in self.ncs:
            body.append(no_connect(x, y))
        for s, x, y, size, bold in self.texts:
            body.append(_text(s, x, y, size, bold))
        libs = '\n'.join('\t\t' + schgen.LIB[l].strip().replace('\n', '\n\t\t') if not schgen.LIB[l].startswith('\t') else schgen.LIB[l]
                         for l in sorted(used))
        hdr = ('(kicad_sch\n\t(version 20260306)\n\t(generator "eeschema")\n\t(generator_version "10.0")\n\t(uuid "%s")\n\t(paper "%s")\n'
               '\t(title_block\n\t\t(title "The Harp - %s")\n\t\t(rev "A")\n\t\t(company "The Frogmouth")\n\t)\n\t(lib_symbols\n%s\n\t)\n'
               % (self.sheet.uuid, self.sheet.paper, self.sheet.title, libs))
        return oswald(hdr + '\n'.join(body) + '\n)\n')

    def _text_positions(self, p):
        """Default Reference / Value placement: beside two-pin parts, above/below bigger ones."""
        part = p.part
        pins = list(p.pins.values())
        xs = [q[0] for q in pins] or [p.x]
        ys = [q[1] for q in pins] or [p.y]
        bb = p.body_bbox() or (p.x - 1, p.y - 1, p.x + 1, p.y + 1)
        ref_pos, val_pos = p.ref_pos, p.val_pos
        if ref_pos and val_pos:
            pass
        elif len(pins) <= 2 or part.lib in ('Device:LED', 'Device:D', 'Device:D_TVS', 'Diode:PMEG3010ER'):
            vertical = abs(ys[0] - ys[-1]) > abs(xs[0] - xs[-1]) if len(pins) == 2 else True
            if vertical:
                rx = round(bb[2] + 0.6, 2)
                ref_pos = ref_pos or (rx, round(p.y - 1.0, 2), 'left')
                val_pos = val_pos or (rx, round(p.y + 1.4, 2), 'left')
            else:
                ref_pos = ref_pos or (p.x, round(bb[1] - 1.0, 2), 'center')
                val_pos = val_pos or (p.x, round(bb[3] + 1.6, 2), 'center')
        else:
            ref_pos = ref_pos or (round(bb[0], 2), round(bb[1] - 3.2, 2), 'left')
            val_pos = val_pos or (round(bb[0], 2), round(bb[1] - 1.2, 2), 'left')
        rx, ry, rj = ref_pos[:3]
        ra = ref_pos[3] if len(ref_pos) > 3 else 0
        vx, vy, vj = val_pos[:3]
        va = val_pos[3] if len(val_pos) > 3 else 0
        return rx, ry, rj, ra, vx, vy, vj, va

    # ------------------------------------------------------------ checks
    def check(self):
        probs = []
        pts = self._points()
        # grid
        for key, p in self.placed.items():
            for nb, (x, y, ox, oy) in p.pins.items():
                if abs(x / 1.27 - round(x / 1.27)) > 1e-3 or abs(y / 1.27 - round(y / 1.27)) > 1e-3:
                    probs.append('off-grid pin %s.%s %s' % (key[0], nb, (x, y)))
        # dangling wire ends
        cnt = defaultdict(int)
        for a, b in self.wires:
            cnt[a] += 1
            cnt[b] += 1
        attach = set()
        for p in self.placed.values():
            for nb, (x, y, ox, oy) in p.pins.items():
                attach.add((x, y))
        for n, x, y, *_ in self.powers + self.labels + self.locals:
            attach.add((x, y))
        for x, y, d in self.flags:
            attach.add((x, y))
        for pt, n in cnt.items():
            if n == 1 and pt not in attach:
                if not any(pt != a and pt != b and _on_seg(pt, a, b) for a, b in self.wires):
                    probs.append('dangling wire end %s' % (pt,))
        # wires through bodies, and over pin lines
        for key, p in self.placed.items():
            edges = p.body_edges()
            if not edges:
                continue
            for a, b in self.wires:
                if any(_segs_intersect(a, b, c, d) for c, d in edges):
                    probs.append('wire %s-%s through %s body' % (a, b, key[0]))
            # pin lines: from pin end toward body
            for nb, (x, y, ox, oy) in p.pins.items():
                ln = _pin_len(p, nb)
                inner = (round(x - ox * ln, 3), round(y - oy * ln, 3))
                for a, b in self.wires:
                    if (x, y) in (a, b):
                        # a wire continuing along the pin line into the body
                        other = b if a == (x, y) else a
                        if _on_seg(inner, a, b) or (_collinear((x, y), inner, other) and _dot((other[0] - x, other[1] - y), (-ox, -oy)) > 0):
                            probs.append('wire %s-%s runs along pin %s.%s' % (a, b, key[0], nb))
                        continue
                    if ln > 0 and _seg_seg_overlap(a, b, (x, y), inner):
                        probs.append('wire %s-%s crosses pin %s.%s' % (a, b, key[0], nb))
        # overlapping collinear wires
        for i, (a, b) in enumerate(self.wires):
            for c, d in self.wires[i + 1:]:
                if _seg_seg_overlap(a, b, c, d):
                    probs.append('wires overlap %s-%s and %s-%s' % (a, b, c, d))
        # a wire end that lands on another wire's interior or on a pin not at its end counts as a junction: fine.
        # a wire passing over a pin end it is not attached to
        for key, p in self.placed.items():
            for nb, (x, y, ox, oy) in p.pins.items():
                for a, b in self.wires:
                    if (x, y) not in (a, b) and _on_seg((x, y), a, b):
                        probs.append('wire %s-%s passes over pin end %s.%s (joins it)' % (a, b, key[0], nb))
        # crossings (informational)
        cross = 0
        for i, (a, b) in enumerate(self.wires):
            for c, d in self.wires[i + 1:]:
                if _cross(a, b, c, d):
                    cross += 1
                    probs.append('crossing (no junction): %s-%s with %s-%s' % (a, b, c, d))
        # text overlaps (rough boxes)
        boxes = self.text_boxes()
        for i in range(len(boxes)):
            for j in range(i + 1, len(boxes)):
                if _box_overlap(boxes[i][1], boxes[j][1]):
                    probs.append('text overlap: %s / %s' % (boxes[i][0], boxes[j][0]))
        bodies = [(k[0], p.body_bbox()) for k, p in self.placed.items() if p.body_bbox()]
        for name, bx in boxes:
            for ref, bb in bodies:
                if _box_overlap(bx, bb) and not name.startswith(ref + ' '):
                    probs.append('text %s over body of %s' % (name, ref))
            for a, b in self.wires:
                if _seg_box(a, b, *bx):
                    probs.append('text %s over wire %s-%s' % (name, a, b))
        self.problems = probs
        return probs, cross

    def text_boxes(self):
        out = []
        for key, p in self.placed.items():
            rx, ry, rj, ra, vx, vy, vj, va = self._text_positions(p)
            out.append(('%s ref' % key[0], _tbox(p.part.ref + ('ABCDEFG'[p.part.unit - 1] if _nunits(p) > 1 else ''), rx, ry, rj, 1.27, ra)))
            if not p.hide_val:
                out.append(('%s value' % key[0], _tbox(p.part.value, vx, vy, vj, 1.27, va)))
        for x, y, dir in self.flags:
            vp, vj = {'up': ((x, round(y - 3.2, 2)), 'center'), 'down': ((x, round(y + 3.2, 2)), 'center'),
                      'right': ((round(x + 3.2, 2), y), 'left'), 'left': ((round(x - 3.2, 2), y), 'right')}[dir]
            out.append(('PWR_FLAG', _tbox('PWR_FLAG', vp[0], vp[1], vj, 1.27, 0)))
        for net, x, y, ang, (vx, vy), just in self.powers:
            out.append(('%s pwr' % net, _tbox(net, vx, vy, just, 1.27, 0)))
        for name, x, y, ang, just, shape in self.labels + [l + (None,) for l in self.locals]:
            L = len(name) * 0.62 * 1.27 + 2.0
            if ang == 0:
                bx = (x, y - 0.9, x + L, y + 0.9)
            elif ang == 180:
                bx = (x - L, y - 0.9, x, y + 0.9)
            elif ang == 90:
                bx = (x - 0.9, y - L, x + 0.9, y)
            else:
                bx = (x - 0.9, y, x + 0.9, y + L)
            out.append(('label %s' % name, bx))
        return out


def _nunits(p):
    return len({re.match(r'.*_(\d+)_\d+$', s[1]).group(1) for s in find(p.lib, 'symbol') if re.match(r'.*_(\d+)_\d+$', s[1])} - {'0'})


def _pin_len(p, nb):
    for n, nm, px, py, pa, ln, typ in lib_pins(p.lib, p.part.unit):
        if n == nb:
            return ln
    return 0


def _tbox(s, x, y, just, size, ang):
    w = max(len(line) for line in s.split('\n')) * 0.55 * size
    h = 1.2 * size * len(s.split('\n'))
    if ang % 180 == 90:
        w, h = h, w
        if just == 'left':
            return (x - h / 2, y - w, x + h / 2, y)
        if just == 'right':
            return (x - h / 2, y, x + h / 2, y + w)
        return (x - h / 2, y - w / 2, x + h / 2, y + w / 2)
    if just == 'left':
        return (x, y - h / 2, x + w, y + h / 2)
    if just == 'right':
        return (x - w, y - h / 2, x, y + h / 2)
    return (x - w / 2, y - h / 2, x + w / 2, y + h / 2)


def _box_overlap(a, b):
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def _dot(a, b):
    return a[0] * b[0] + a[1] * b[1]


def _collinear(a, b, c, eps=1e-3):
    return abs((b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])) < eps


def _on_seg(pt, a, b, eps=1e-3):
    (x, y), (x1, y1), (x2, y2) = pt, a, b
    if min(x1, x2) - eps <= x <= max(x1, x2) + eps and min(y1, y2) - eps <= y <= max(y1, y2) + eps:
        return abs((x2 - x1) * (y - y1) - (y2 - y1) * (x - x1)) < eps
    return False


def _seg_box(a, b, x0, y0, x1, y1):
    """Axis-aligned segment intersects the open box."""
    ax, ay = min(a[0], b[0]), min(a[1], b[1])
    bx, by = max(a[0], b[0]), max(a[1], b[1])
    return ax < x1 and bx > x0 and ay < y1 and by > y0


def _seg_seg_overlap(a, b, c, d, eps=1e-3):
    """Collinear axis-aligned segments sharing more than a point."""
    if not (_collinear(a, b, c) and _collinear(a, b, d)):
        return False
    if abs(a[0] - b[0]) < eps:   # vertical
        if abs(c[0] - a[0]) > eps:
            return False
        lo, hi = max(min(a[1], b[1]), min(c[1], d[1])), min(max(a[1], b[1]), max(c[1], d[1]))
    else:
        if abs(c[1] - a[1]) > eps:
            return False
        lo, hi = max(min(a[0], b[0]), min(c[0], d[0])), min(max(a[0], b[0]), max(c[0], d[0]))
    return hi - lo > eps


def _segs_intersect(a, b, c, d, eps=1e-3):
    """Proper crossing of segment ab with segment cd (touching at an end does not count)."""
    def orient(p, q, r):
        return (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])
    o1, o2, o3, o4 = orient(a, b, c), orient(a, b, d), orient(c, d, a), orient(c, d, b)
    return (o1 * o2 < -eps) and (o3 * o4 < -eps)


def _cross(a, b, c, d, eps=1e-3):
    """Perpendicular segments crossing in their interiors."""
    if abs(a[0] - b[0]) < eps and abs(c[1] - d[1]) < eps:
        v, h = (a, b), (c, d)
    elif abs(a[1] - b[1]) < eps and abs(c[0] - d[0]) < eps:
        v, h = (c, d), (a, b)
    else:
        return False
    x = v[0][0]
    y = h[0][1]
    return (min(h[0][0], h[1][0]) + eps < x < max(h[0][0], h[1][0]) - eps and
            min(v[0][1], v[1][1]) + eps < y < max(v[0][1], v[1][1]) - eps)


def _glabel(name, x, y, ang, just, shape):
    return ('\t(global_label "%s"\n\t\t(shape %s)\n\t\t(at %s %s %s)\n\t\t(fields_autoplaced yes)\n\t\t%s\n\t\t(uuid "%s")\n'
            '\t\t(property "Intersheetrefs" "${INTERSHEET_REFS}"\n\t\t\t(at %s %s 0)\n\t\t\t(hide yes)\n\t\t\t(show_name no)\n\t\t\t(do_not_autoplace no)\n\t\t\t%s\n\t\t)\n\t)'
            % (name, shape, x, y, ang, _eff(just), uid(), x, y, _eff(just)))


def _text(s, x, y, size, bold):
    b = '\n\t\t\t\t\t(bold yes)' if bold else ''
    return ('\t(text "%s"\n\t\t(exclude_from_sim no)\n\t\t(at %s %s 0)\n\t\t(effects\n\t\t\t(font\n\t\t\t\t(size %s %s)%s\n\t\t\t)\n\t\t\t(justify left bottom)\n\t\t)\n\t\t(uuid "%s")\n\t)'
            % (s.replace('"', '\\"').replace('\n', '\\n'), x, y, size, size, b, uid()))


def oswald(txt):
    """Give every font block the Oswald face."""
    txt = re.sub(r'\(font\n(\s*)\(', r'(font\n\1(face "%s")\n\1(' % FONT, txt)
    txt = re.sub(r'\(font \(', '(font (face "%s") (' % FONT, txt)
    return txt


def number_power(texts):
    """Renumber #PWR@ / #FLG@ across sheets (in the given order), top to bottom then left to right within a sheet."""
    out = []
    n = [0]
    for t in texts:
        # find each power symbol block and its position
        blocks = []
        for m in re.finditer(r'\t\(symbol\n\t\t\(lib_id "power:[^"]*"\)\n\t\t\(at ([\d.\-]+) ([\d.\-]+) [\d.\-]+\)', t):
            blocks.append((float(m.group(2)), float(m.group(1)), m.start()))
        order = sorted(range(len(blocks)), key=lambda i: (blocks[i][0], blocks[i][1]))
        rank = {blocks[i][2]: k for k, i in enumerate(order)}
        # assign numbers in document order of appearance but numbered by rank
        base = n[0]
        pieces = []
        last = 0
        for m in re.finditer(r'\t\(symbol\n\t\t\(lib_id "power:[^"]*"\)\n\t\t\(at ([\d.\-]+) ([\d.\-]+) [\d.\-]+\)', t):
            pieces.append(t[last:m.start()])
            end = t.find('\n\t)\n', m.start())
            blk = t[m.start():end]
            num = base + rank[m.start()] + 1
            blk = blk.replace('"#PWR@"', '"#PWR%04d"' % num).replace('"#FLG@"', '"#FLG%04d"' % num)
            blk = blk.replace('(reference "#PWR@")', '(reference "#PWR%04d")' % num).replace('(reference "#FLG@")', '(reference "#FLG%04d")' % num)
            pieces.append(blk)
            last = end
        pieces.append(t[last:])
        n[0] += len(blocks)
        out.append(''.join(pieces))
    return out
