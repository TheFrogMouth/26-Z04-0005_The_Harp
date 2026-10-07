#!/usr/bin/env python3
"""Preview renderer: draws a KiCad 10 .kicad_sch to PNG with Pillow.

    python3 render_png.py SHEET.kicad_sch OUT.png [px_per_mm]

A preview only: symbol graphics, pins, wires, junctions, labels, text,
sheets and sheet notes are drawn well enough to spot overlapping text,
wires through symbols and missing junctions. The owner checks the real
look in KiCad. Oswald is used when FONT_DIR holds Oswald-Regular.ttf and
Oswald-Bold.ttf; otherwise DejaVu Sans.
"""
import sys, os, math, re
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kisch import parse, find, first, prop

FONT_DIR = os.environ.get('FONT_DIR', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fonts'))
PAPER = {'A4': (297, 210), 'A3': (420, 297), 'A2': (594, 420)}
BG = (255, 255, 255)
C_SYM = (140, 0, 0)
C_PIN = (140, 0, 0)
C_PINNAME = (0, 100, 100)
C_PINNUM = (169, 0, 0)
C_WIRE = (0, 150, 0)
C_LABEL = (0, 0, 0)
C_GLABEL = (140, 0, 0)
C_TEXT = (0, 0, 0)
C_REF = (0, 100, 100)
C_VAL = (0, 100, 100)
C_SHEET = (0, 100, 100)
C_NC = (0, 0, 132)


class Canvas:
    def __init__(self, w_mm, h_mm, s):
        self.s = s
        self.im = Image.new('RGB', (int(w_mm * s), int(h_mm * s)), BG)
        self.d = ImageDraw.Draw(self.im)
        self.fonts = {}

    def P(self, x, y):
        return (x * self.s, y * self.s)

    def font(self, size_mm, bold=False):
        px = max(6, int(size_mm * self.s * 1.25))
        key = (px, bold)
        if key not in self.fonts:
            cand = [os.path.join(FONT_DIR, 'Oswald-Bold.ttf' if bold else 'Oswald-Regular.ttf'),
                    '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf' if bold else '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf']
            for c in cand:
                if os.path.exists(c):
                    self.fonts[key] = ImageFont.truetype(c, px)
                    break
            else:
                self.fonts[key] = ImageFont.load_default()
        return self.fonts[key]

    def line(self, a, b, color, w=0.15):
        self.d.line([self.P(*a), self.P(*b)], fill=color, width=max(1, int(w * self.s)))

    def text(self, s, x, y, size, color, hj='left', vj='center', angle=0, bold=False):
        """hj: left/center/right, vj: top/center/bottom, angle 0 or 90 (counter-clockwise, text reads upward)."""
        f = self.font(size, bold)
        lines = s.split('\n')
        lh = f.size * 1.15
        if angle in (0, 180):
            widths = [f.getlength(l) for l in lines]
            W, H = max(widths) if widths else 0, lh * len(lines)
            px, py = self.P(x, y)
            x0 = px - {'left': 0, 'center': W / 2, 'right': W}[hj]
            y0 = py - {'top': 0, 'center': H / 2, 'bottom': H}[vj]
            for i, l in enumerate(lines):
                lx = x0 + {'left': 0, 'center': (W - widths[i]) / 2, 'right': W - widths[i]}[hj]
                self.d.text((lx, y0 + i * lh), l, font=f, fill=color)
            return
        # rotated: render to a temp image, rotate 90 ccw
        widths = [f.getlength(l) for l in lines]
        W, H = int(max(widths)) + 2, int(lh * len(lines)) + 2
        tmp = Image.new('RGBA', (max(W, 1), max(H, 1)), (0, 0, 0, 0))
        td = ImageDraw.Draw(tmp)
        for i, l in enumerate(lines):
            td.text((0, i * lh), l, font=f, fill=color)
        tmp = tmp.rotate(90, expand=True)
        px, py = self.P(x, y)
        # after rotation: text runs upward; horizontal justify maps to vertical placement
        y0 = py - {'left': H and tmp.height, 'center': tmp.height / 2, 'right': 0}[hj]
        x0 = px - {'top': 0, 'center': tmp.width / 2, 'bottom': tmp.width}[vj]
        self.im.paste(tmp, (int(x0), int(y0)), tmp)

    def circle(self, x, y, r, color, fill=None, w=0.15):
        px, py = self.P(x, y)
        rr = r * self.s
        self.d.ellipse([px - rr, py - rr, px + rr, py + rr], outline=color, fill=fill, width=max(1, int(w * self.s)))


def effects(node):
    """(size, bold, hjust, vjust, hidden, color)"""
    e = first(node, 'effects') if node else None
    size, bold, hj, vj, hide, color = 1.27, False, 'center', 'center', False, None
    if e:
        f = first(e, 'font')
        if f:
            sz = first(f, 'size')
            if sz:
                size = float(sz[1])
            bold = first(f, 'bold') is not None and first(f, 'bold')[1] == 'yes'
            c = first(f, 'color')
            if c:
                color = tuple(int(float(v)) for v in c[1:4])
        j = first(e, 'justify')
        if j:
            for t in j[1:]:
                if t in ('left', 'right'):
                    hj = t
                if t in ('top', 'bottom'):
                    vj = t
        h = first(e, 'hide')
        hide = h is not None and h[1] == 'yes'
    if node is not None:
        h = first(node, 'hide')
        if h is not None and h[1] == 'yes':
            hide = True
    return size, bold, hj, vj, hide, color


def stroke_color(node, default):
    st = first(node, 'stroke')
    if st:
        c = first(st, 'color')
        if c and not (float(c[1]) == 0 and float(c[2]) == 0 and float(c[3]) == 0 and float(c[4]) == 0):
            return tuple(int(float(v)) for v in c[1:4])
        w = first(st, 'width')
        return default
    return default


def stroke_width(node, default=0.15):
    st = first(node, 'stroke')
    if st:
        w = first(st, 'width')
        if w and float(w[1]) > 0:
            return float(w[1])
    return default


class SymXform:
    def __init__(self, X, Y, ang, mirror):
        self.X, self.Y, self.ang, self.mirror = X, Y, ang, mirror

    def __call__(self, x, y):
        if self.mirror == 'y':
            x = -x
        if self.mirror == 'x':
            y = -y
        a = math.radians(self.ang)
        xr, yr = x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a)
        return (self.X + xr, self.Y - yr)

    def dir(self, ang_deg):
        """Transform a direction (symbol y-up angle) to sheet-space unit vector (y-down)."""
        dx, dy = math.cos(math.radians(ang_deg)), math.sin(math.radians(ang_deg))
        if self.mirror == 'y':
            dx = -dx
        if self.mirror == 'x':
            dy = -dy
        a = math.radians(self.ang)
        xr, yr = dx * math.cos(a) - dy * math.sin(a), dx * math.sin(a) + dy * math.cos(a)
        return (round(xr, 6), round(-yr, 6))


def draw_symbol(cv, sym, libsyms):
    ln = first(sym, 'lib_name')
    lid = ln[1] if ln else first(sym, 'lib_id')[1]
    lib = libsyms.get(lid)
    if lib is None:
        return
    at = first(sym, 'at')
    X, Y = float(at[1]), float(at[2])
    ang = float(at[3]) if len(at) > 3 else 0.0
    m = first(sym, 'mirror')
    T = SymXform(X, Y, ang, m[1] if m else None)
    unit = first(sym, 'unit')
    unit = int(unit[1]) if unit else 1
    is_power = first(lib, 'power') is not None or lid.startswith('power:')
    pin_names = first(lib, 'pin_names')
    hide_names = pin_names is not None and any(isinstance(c, list) and c[0] == 'hide' and c[1] == 'yes' for c in pin_names)
    hide_names = hide_names or any(isinstance(c, list) and c[0] == 'pin_names' and 'hide' in c for c in lib)
    pn_off = 0.508
    if pin_names:
        o = first(pin_names, 'offset')
        if o:
            pn_off = float(o[1])
    hide_numbers = first(lib, 'pin_numbers') is not None and ('hide' in first(lib, 'pin_numbers') or
                                                               any(isinstance(c, list) and c[0] == 'hide' and c[1] == 'yes' for c in first(lib, 'pin_numbers')))
    for sub in find(lib, 'symbol'):
        mm = re.match(r'.*_(\d+)_(\d+)$', sub[1])
        u, cv_ = (int(mm.group(1)), int(mm.group(2))) if mm else (0, 1)
        if u not in (0, unit) or cv_ not in (0, 1):
            continue
        for g in sub:
            if not isinstance(g, list):
                continue
            k = g[0]
            if k == 'rectangle':
                s, e = first(g, 'start'), first(g, 'end')
                pts = [T(float(s[1]), float(s[2])), T(float(e[1]), float(s[2])), T(float(e[1]), float(e[2])), T(float(s[1]), float(e[2]))]
                fill = first(g, 'fill')
                if fill and first(fill, 'type') and first(fill, 'type')[1] == 'background':
                    cv.d.polygon([cv.P(*p) for p in pts], fill=(255, 255, 194))
                for i in range(4):
                    cv.line(pts[i], pts[(i + 1) % 4], C_SYM, stroke_width(g, 0.254))
            elif k == 'polyline':
                xy = [T(float(p[1]), float(p[2])) for p in find(first(g, 'pts'), 'xy')]
                fill = first(g, 'fill')
                if fill and first(fill, 'type') and first(fill, 'type')[1] in ('background', 'outline') and len(xy) > 2:
                    cv.d.polygon([cv.P(*p) for p in xy], fill=(255, 255, 194) if first(fill, 'type')[1] == 'background' else C_SYM)
                for a, b in zip(xy, xy[1:]):
                    cv.line(a, b, C_SYM, stroke_width(g, 0.254))
            elif k == 'circle':
                c = first(g, 'center')
                r = float(first(g, 'radius')[1])
                cx, cy = T(float(c[1]), float(c[2]))
                fill = first(g, 'fill')
                f = (255, 255, 194) if fill and first(fill, 'type') and first(fill, 'type')[1] == 'background' else None
                cv.circle(cx, cy, r, C_SYM, fill=f, w=stroke_width(g, 0.254))
            elif k == 'arc':
                s, mid, e = (first(g, n) for n in ('start', 'mid', 'end'))
                p1, p2, p3 = (T(float(n[1]), float(n[2])) for n in (s, mid, e))
                draw_arc(cv, p1, p2, p3, C_SYM, stroke_width(g, 0.254))
            elif k == 'text':
                at2 = first(g, 'at')
                x, y = T(float(at2[1]), float(at2[2]))
                size, bold, hj, vj, hide, color = effects(g)
                cv.text(g[1], x, y, size, C_SYM, hj, vj)
            elif k == 'pin':
                draw_pin(cv, g, T, is_power, hide_names, hide_numbers, pn_off)
    # properties
    for p in find(sym, 'property'):
        if p[1] in ('Reference', 'Value') or (p[1] not in ('Footprint', 'Datasheet', 'Description')):
            size, bold, hj, vj, hide, color = effects(p)
            if hide:
                continue
            if p[1] not in ('Reference', 'Value'):
                continue
            pat = first(p, 'at')
            px, py = float(pat[1]), float(pat[2])
            pang = float(pat[3]) if len(pat) > 3 else 0
            # KiCad: property angle is absolute on sheet; justify is given in text's own frame
            txt = p[2]
            if p[1] == 'Reference':
                un = first(sym, 'unit')
                nunits = len({re.match(r'.*_(\d+)_\d+$', s[1]).group(1) for s in find(lib, 'symbol') if re.match(r'.*_(\d+)_\d+$', s[1])} - {'0'})
                if nunits > 1 and un:
                    txt += chr(ord('A') + int(un[1]) - 1)
            cv.text(txt, px, py, size, C_REF if p[1] == 'Reference' else C_VAL, hj, vj, angle=90 if pang % 180 == 90 else 0, bold=bold)


def draw_pin(cv, g, T, is_power, hide_names, hide_numbers, pn_off):
    at = first(g, 'at')
    x, y = float(at[1]), float(at[2])
    pang = float(at[3]) if len(at) > 3 else 0
    ln = first(g, 'length')
    L = float(ln[1]) if ln else 0
    name = first(g, 'name')
    num = first(g, 'number')
    hidden = first(g, 'hide') is not None and first(g, 'hide')[1] == 'yes'
    if hidden:
        return
    a = T(x, y)
    ux, uy = math.cos(math.radians(pang)), math.sin(math.radians(pang))
    b = T(x + ux * L, y + uy * L)
    if L > 0:
        cv.line(a, b, C_PIN, 0.15)
    if is_power:
        return
    dx, dy = T.dir(pang)  # sheet-space direction from pin end toward body
    size_n = 1.27
    e = first(name, 'effects') if name else None
    if e:
        s = first(first(e, 'font'), 'size') if first(e, 'font') else None
        if s:
            size_n = float(s[1])
    # pin number: just above the pin line, centred
    if num and num[1] and not hide_numbers and L > 0:
        mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
        if abs(dx) > abs(dy):
            cv.text(num[1], mx, my - 0.3, size_n * 0.8, C_PINNUM, 'center', 'bottom')
        else:
            cv.text(num[1], mx - 0.3, my, size_n * 0.8, C_PINNUM, 'center', 'bottom', angle=90)
    if name and name[1] and name[1] != '~' and not hide_names:
        nx, ny = b[0] + dx * pn_off, b[1] + dy * pn_off
        if abs(dx) > abs(dy):
            cv.text(name[1].replace('~{', '').replace('}', ''), nx, ny, size_n * 0.85, C_PINNAME, 'left' if dx > 0 else 'right', 'center')
        else:
            # vertical pin: name reads upward
            cv.text(name[1].replace('~{', '').replace('}', ''), nx, ny, size_n * 0.85, C_PINNAME, 'left' if dy < 0 else 'right', 'center', angle=90)


def draw_arc(cv, p1, p2, p3, color, w):
    (x1, y1), (x2, y2), (x3, y3) = p1, p2, p3
    d = 2 * (x1 * (y2 - y3) + x2 * (y3 - y1) + x3 * (y1 - y2))
    if abs(d) < 1e-9:
        cv.line(p1, p3, color, w)
        return
    ux = ((x1 ** 2 + y1 ** 2) * (y2 - y3) + (x2 ** 2 + y2 ** 2) * (y3 - y1) + (x3 ** 2 + y3 ** 2) * (y1 - y2)) / d
    uy = ((x1 ** 2 + y1 ** 2) * (x3 - x2) + (x2 ** 2 + y2 ** 2) * (x1 - x3) + (x3 ** 2 + y3 ** 2) * (x2 - x1)) / d
    r = math.hypot(x1 - ux, y1 - uy)
    a1 = math.degrees(math.atan2(y1 - uy, x1 - ux))
    a2 = math.degrees(math.atan2(y2 - uy, x2 - ux))
    a3 = math.degrees(math.atan2(y3 - uy, x3 - ux))

    def ccw(a, b):
        return (b - a) % 360
    # choose direction so that mid lies between start and end
    if ccw(a1, a2) <= ccw(a1, a3):
        start, end = a1, a3
    else:
        start, end = a3, a1
    cx, cy = cv.P(ux, uy)
    rr = r * cv.s
    cv.d.arc([cx - rr, cy - rr, cx + rr, cy + rr], start, end, fill=color, width=max(1, int(w * cv.s)))


def draw_label(cv, l, kind):
    at = first(l, 'at')
    x, y = float(at[1]), float(at[2])
    ang = float(at[3]) if len(at) > 3 else 0
    size, bold, hj, vj, hide, color = effects(l)
    name = l[1]
    f = cv.font(size)
    tw = f.getlength(name) / cv.s
    th = size * 1.3
    if kind == 'global':
        # box with a point at the connection end; text inside
        pad = th * 0.4
        if ang == 0:      # text to the right of the point
            pts = [(x, y), (x + pad, y - th / 2), (x + tw + 2 * pad, y - th / 2), (x + tw + 2 * pad, y + th / 2), (x + pad, y + th / 2)]
            cv.text(name, x + pad * 1.3, y, size, C_GLABEL, 'left', 'center')
        elif ang == 180:
            pts = [(x, y), (x - pad, y - th / 2), (x - tw - 2 * pad, y - th / 2), (x - tw - 2 * pad, y + th / 2), (x - pad, y + th / 2)]
            cv.text(name, x - pad * 1.3, y, size, C_GLABEL, 'right', 'center')
        elif ang == 90:   # text goes upward
            pts = [(x, y), (x - th / 2, y - pad), (x - th / 2, y - tw - 2 * pad), (x + th / 2, y - tw - 2 * pad), (x + th / 2, y - pad)]
            cv.text(name, x, y - pad * 1.3, size, C_GLABEL, 'left', 'center', angle=90)
        else:
            pts = [(x, y), (x - th / 2, y + pad), (x - th / 2, y + tw + 2 * pad), (x + th / 2, y + tw + 2 * pad), (x + th / 2, y + pad)]
            cv.text(name, x, y + pad * 1.3, size, C_GLABEL, 'right', 'center', angle=90)
        for a, b in zip(pts, pts[1:] + pts[:1]):
            cv.line(a, b, C_GLABEL, 0.15)
    else:
        off = 0.4
        if ang == 0:
            cv.text(name, x + off, y - off, size, C_LABEL, 'left', 'bottom')
        elif ang == 180:
            cv.text(name, x - off, y - off, size, C_LABEL, 'right', 'bottom')
        elif ang == 90:
            cv.text(name, x - off, y - off, size, C_LABEL, 'left', 'bottom', angle=90)
        else:
            cv.text(name, x - off, y + off, size, C_LABEL, 'right', 'bottom', angle=90)


def render(path, out, s=6.0):
    root = parse(open(path).read())
    paper = first(root, 'paper')
    W, H = PAPER.get(paper[1] if paper else 'A3', (420, 297))
    if paper and 'portrait' in paper:
        W, H = H, W
    cv = Canvas(W, H, s)
    # frame
    cv.d.rectangle([cv.P(10, 10), cv.P(W - 10, H - 10)], outline=(120, 120, 120), width=1)
    libsyms = {sy[1]: sy for sy in find(first(root, 'lib_symbols') or [], 'symbol')}
    for sh in find(root, 'sheet'):
        at, sz = first(sh, 'at'), first(sh, 'size')
        x, y, w, h = float(at[1]), float(at[2]), float(sz[1]), float(sz[2])
        col = stroke_color(sh, C_SHEET)
        fill = first(sh, 'fill')
        fc = None
        if fill and first(fill, 'color'):
            c = first(fill, 'color')
            a = float(c[4])
            if a > 0:
                fc = tuple(int(255 - (255 - int(float(v))) * a) for v in c[1:4])
        cv.d.rectangle([cv.P(x, y), cv.P(x + w, y + h)], outline=col, fill=fc, width=max(1, int(stroke_width(sh, 0.15) * s)))
        for p in find(sh, 'property'):
            size, bold, hj, vj, hide, color = effects(p)
            if hide:
                continue
            pat = first(p, 'at')
            cv.text(p[2], float(pat[1]), float(pat[2]), size, color or col, hj, vj, bold=bold)
        for pin in find(sh, 'pin'):
            pat = first(pin, 'at')
            cv.circle(float(pat[1]), float(pat[2]), 0.6, col)
            size, bold, hj, vj, hide, color = effects(pin)
            cv.text(pin[1], float(pat[1]) + (1 if pat[3] == '0' else -1), float(pat[2]), size, col, 'left' if pat[3] == '0' else 'right', 'center')
    for g in find(root, 'rectangle'):
        sa, e = first(g, 'start'), first(g, 'end')
        col = stroke_color(g, (0, 0, 0))
        st = first(g, 'stroke')
        dashed = st is not None and first(st, 'type') is not None and first(st, 'type')[1] == 'dash'
        pts = [(float(sa[1]), float(sa[2])), (float(e[1]), float(sa[2])), (float(e[1]), float(e[2])), (float(sa[1]), float(e[2]))]
        for a, b in zip(pts, pts[1:] + pts[:1]):
            if dashed:
                dashed_line(cv, a, b, col, stroke_width(g, 0.15))
            else:
                cv.line(a, b, col, stroke_width(g, 0.15))
    for g in find(root, 'polyline'):
        xy = [(float(p[1]), float(p[2])) for p in find(first(g, 'pts'), 'xy')]
        col = stroke_color(g, (0, 0, 132))
        for a, b in zip(xy, xy[1:]):
            cv.line(a, b, col, stroke_width(g, 0.15))
    for w in find(root, 'wire'):
        xy = [(float(p[1]), float(p[2])) for p in find(first(w, 'pts'), 'xy')]
        for a, b in zip(xy, xy[1:]):
            cv.line(a, b, C_WIRE, 0.25)
    for b in find(root, 'bus'):
        xy = [(float(p[1]), float(p[2])) for p in find(first(b, 'pts'), 'xy')]
        for a, c in zip(xy, xy[1:]):
            cv.line(a, c, (0, 0, 132), 0.5)
    for sym in find(root, 'symbol'):
        if first(sym, 'lib_id'):
            draw_symbol(cv, sym, libsyms)
    for j in find(root, 'junction'):
        at = first(j, 'at')
        cv.circle(float(at[1]), float(at[2]), 0.5, C_WIRE, fill=C_WIRE)
    for nc in find(root, 'no_connect'):
        at = first(nc, 'at')
        x, y = float(at[1]), float(at[2])
        cv.line((x - 0.8, y - 0.8), (x + 0.8, y + 0.8), C_NC, 0.2)
        cv.line((x - 0.8, y + 0.8), (x + 0.8, y - 0.8), C_NC, 0.2)
    for kind, key in (('global', 'global_label'), ('local', 'label'), ('hier', 'hierarchical_label')):
        for l in find(root, key):
            draw_label(cv, l, 'global' if kind != 'local' else 'local')
    for t in find(root, 'text'):
        at = first(t, 'at')
        size, bold, hj, vj, hide, color = effects(t)
        cv.text(t[1].replace('\\n', '\n'), float(at[1]), float(at[2]), size, color or C_TEXT, hj, vj,
                angle=90 if (len(at) > 3 and float(at[3]) % 180 == 90) else 0, bold=bold)
    cv.im.save(out)
    return out


def dashed_line(cv, a, b, col, w, dash=2.0):
    L = math.hypot(b[0] - a[0], b[1] - a[1])
    if L == 0:
        return
    n = int(L / dash)
    for i in range(0, n, 2):
        t0, t1 = i / n, min((i + 1) / n, 1)
        cv.line((a[0] + (b[0] - a[0]) * t0, a[1] + (b[1] - a[1]) * t0), (a[0] + (b[0] - a[0]) * t1, a[1] + (b[1] - a[1]) * t1), col, w)


if __name__ == '__main__':
    s = float(sys.argv[3]) if len(sys.argv) > 3 else 6.0
    print(render(sys.argv[1], sys.argv[2], s))
