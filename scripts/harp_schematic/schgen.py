"""Generate KiCad 10 hierarchical schematic sheets from a component/net spec.

Every pin gets a 2.54 mm stub and, at the stub end, a power symbol, a global
label (net used on more than one sheet) or a local label. Pins on net None
get a no-connect marker. Symbols are packed in rows on the sheet.
"""
import re, math, sys, os, uuid as U
sys.path.insert(0, os.path.dirname(__file__))
from kisch import parse, lib_pins, find, first
HERE = os.path.dirname(os.path.abspath(__file__))
VENDORED = os.path.join(HERE, 'symbols.sexpr')

STUB = 2.54
POWER_NETS = {'GND', '+3V3', '+5V', '+9V', 'VDDA'}


NS = U.UUID('5f1e2a7c-8d3b-4c6e-9a1f-26a040050005')   # The Harp, 26-Z04-0005


def uid(key=None):
    """Stable UUID for sheets and symbols (so regenerating keeps PCB links), random otherwise."""
    return str(U.uuid5(NS, key)) if key else str(U.uuid4())


# ---------------------------------------------------------------- library
def _load_vendored(path):
    """Read the top-level (symbol ...) blocks of symbols.sexpr into {name: text}."""
    txt = open(path).read()
    out, i, n = {}, 0, len(txt)
    while True:
        i = txt.find('(symbol "', i)
        if i < 0:
            return out
        d, j = 0, i
        while j < n:
            ch = txt[j]
            if ch == '"':
                j += 1
                while txt[j] != '"':
                    j += 2 if txt[j] == '\\' else 1
            elif ch == '(':
                d += 1
            elif ch == ')':
                d -= 1
                if d == 0:
                    break
            j += 1
        blk = txt[i:j + 1]
        out[re.match(r'\(symbol "([^"]*)"', blk).group(1)] = blk
        i = j + 1


if os.path.exists(VENDORED):
    LIB = _load_vendored(VENDORED)
else:
    from libcollect import allb
    LIB = {k: v for k, (p, v) in allb.items()}


def _clone_power(src, new):
    t = LIB['power:' + src]
    t = t.replace('"power:%s"' % src, '"power:%s"' % new)
    t = t.replace('"%s_0_1"' % src, '"%s_0_1"' % new).replace('"%s_1_1"' % src, '"%s_1_1"' % new)
    t = t.replace('(property "Value" "%s"' % src, '(property "Value" "%s"' % new)
    t = re.sub(r'Power symbol creates a global label with name "[^"]*"',
               'Power symbol creates a global label with name "%s"' % new, t)
    LIB['power:' + new] = t


if 'power:+9V' not in LIB:
    _clone_power('+5V', '+9V')
if 'power:VDDA' not in LIB:
    _clone_power('VDD', 'VDDA')

if 'MCU_ST_STM32H7:STM32H750VBTx' not in LIB:
  _vb = open(os.path.join(HERE, 'h750vb.kicad_sym')).read()
  _i = _vb.index('(symbol "STM32H750VBTx"')
  _d = 0
  for _j in range(_i, len(_vb)):
      if _vb[_j] == '(':
          _d += 1
      elif _vb[_j] == ')':
          _d -= 1
          if _d == 0:
              break
  LIB['MCU_ST_STM32H7:STM32H750VBTx'] = _vb[_i:_j + 1].replace(
      '(symbol "STM32H750VBTx"', '(symbol "MCU_ST_STM32H7:STM32H750VBTx"', 1)

PARSED = {}


def libnode(lid):
    if lid not in PARSED:
        PARSED[lid] = parse(LIB[lid])
    return PARSED[lid]


def is_power(lid):
    return lid.startswith('power:')


# ---------------------------------------------------------------- spec types
class Part:
    def __init__(self, ref, lib, value, fp, pins, unit=1, dnp=False, props=None, note=None):
        self.ref, self.lib, self.value, self.fp = ref, lib, value, fp
        self.pins = pins            # {pin number: net or None}
        self.unit, self.dnp = unit, dnp
        self.props = props or {}
        self.note = note


# ---------------------------------------------------------------- geometry
def placed_pins(part, X, Y):
    out = []
    for nb, nm, px, py, pa, ln, typ in lib_pins(libnode(part.lib), part.unit):
        ex, ey = X + px, Y - py
        a = math.radians(pa)
        dx, dy = round(math.cos(a)), -round(math.sin(a))   # toward body, sheet coords
        out.append((nb, nm, round(ex, 3), round(ey, 3), -dx, -dy, typ))
    return out


def bbox(part):
    pins = placed_pins(part, 0, 0)
    xs = [p[2] for p in pins] or [0]
    ys = [p[3] for p in pins] or [0]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    # room for stubs + labels on each side
    def lab(side):
        n = 0
        for nb, nm, x, y, ox, oy, t in pins:
            net = part.pins.get(nb, 'MISSING')
            if (side == 'L' and ox < 0) or (side == 'R' and ox > 0) or (side == 'U' and oy < 0) or (side == 'D' and oy > 0):
                n = max(n, 0 if net in POWER_NETS or net is None else len(net))
        return n
    return (x0 - STUB - 1.3 * lab('L') - 4, x1 + STUB + 1.3 * lab('R') + 4,
            y0 - STUB - (1.3 * lab('U') if lab('U') else 4) - 4,
            y1 + STUB + (1.3 * lab('D') if lab('D') else 4) - 0 + 4)


def g(v):
    return round(round(v / 2.54) * 2.54, 3)


# ---------------------------------------------------------------- emitters
def _eff(justify=None, hide=False, size=1.27):
    j = '\n\t\t\t\t(justify %s)' % justify if justify else ''
    return '(effects\n\t\t\t\t(font\n\t\t\t\t\t(size %s %s)\n\t\t\t\t)%s\n\t\t\t)' % (size, size, j)


def _prop(name, val, x, y, hide=False, justify=None, ang=0):
    h = '\n\t\t\t(hide yes)' if hide else ''
    return ('\t\t(property "%s" "%s"\n\t\t\t(at %s %s %s)%s\n\t\t\t(show_name no)\n\t\t\t(do_not_autoplace no)\n\t\t\t%s\n\t\t)'
            % (name, val.replace('"', '\\"'), x, y, ang, h, _eff(justify)))


def symbol_block(lid, ref, value, x, y, ang, unit, path_prefix, project, fp='', dnp=False,
                 props=None, pins=(), refpos=None, valpos=None, hide_ref=False, hide_val=False, desc=''):
    props = props or {}
    suid = uid('symbol:%s:%s:%d' % (path_prefix, ref, unit)) if not ref.startswith('#') else uid()
    rx, ry = refpos or (x, y - 2)
    vx, vy = valpos or (x, y + 2)
    out = ['\t(symbol', '\t\t(lib_id "%s")' % lid, '\t\t(at %s %s %s)' % (x, y, ang), '\t\t(unit %d)' % unit,
           '\t\t(body_style 1)', '\t\t(exclude_from_sim no)', '\t\t(in_bom %s)' % ('no' if ref.startswith('#') else 'yes'),
           '\t\t(on_board %s)' % ('no' if ref.startswith('#') else 'yes'), '\t\t(in_pos_files yes)',
           '\t\t(dnp %s)' % ('yes' if dnp else 'no'), '\t\t(uuid "%s")' % suid]
    out.append(_prop('Reference', ref, rx, ry, hide=hide_ref, justify='left'))
    out.append(_prop('Value', value, vx, vy, hide=hide_val, justify='left'))
    out.append(_prop('Footprint', fp, x, y, hide=True))
    out.append(_prop('Datasheet', props.pop('Datasheet', ''), x, y, hide=True))
    out.append(_prop('Description', desc, x, y, hide=True))
    for k, v in props.items():
        out.append(_prop(k, v, x, y, hide=True))
    for p in pins:
        out.append('\t\t(pin "%s"\n\t\t\t(uuid "%s")\n\t\t)' % (p, uid()))
    out.append('\t\t(instances\n\t\t\t(project "%s"\n\t\t\t\t(path "%s"\n\t\t\t\t\t(reference "%s")\n\t\t\t\t\t(unit %d)\n\t\t\t\t)\n\t\t\t)\n\t\t)'
               % (project, path_prefix, ref, unit))
    out.append('\t)')
    return '\n'.join(out)


def wire(a, b):
    return ('\t(wire\n\t\t(pts\n\t\t\t(xy %s %s) (xy %s %s)\n\t\t)\n\t\t(stroke\n\t\t\t(width 0)\n\t\t\t(type default)\n\t\t)\n\t\t(uuid "%s")\n\t)'
            % (a[0], a[1], b[0], b[1], uid()))


def _dir_ang(ox, oy):
    if ox > 0: return 0, 'left'
    if ox < 0: return 180, 'right'
    if oy < 0: return 90, 'left'
    return 270, 'right'


def label(name, x, y, ox, oy, glob):
    ang, just = _dir_ang(ox, oy)
    if glob:
        return ('\t(global_label "%s"\n\t\t(shape passive)\n\t\t(at %s %s %s)\n\t\t(fields_autoplaced yes)\n\t\t%s\n\t\t(uuid "%s")\n'
                '\t\t(property "Intersheetrefs" "${INTERSHEET_REFS}"\n\t\t\t(at %s %s 0)\n\t\t\t(hide yes)\n\t\t\t(show_name no)\n\t\t\t(do_not_autoplace no)\n\t\t\t%s\n\t\t)\n\t)'
                % (name, x, y, ang, _eff(just), uid(), x, y, _eff(just)))
    return ('\t(label "%s"\n\t\t(at %s %s %s)\n\t\t(fields_autoplaced yes)\n\t\t%s\n\t\t(uuid "%s")\n\t)'
            % (name, x, y, ang, _eff(just + ' bottom'), uid()))


def no_connect(x, y):
    return '\t(no_connect\n\t\t(at %s %s)\n\t\t(uuid "%s")\n\t)' % (x, y, uid())


def text(s, x, y):
    return ('\t(text "%s"\n\t\t(exclude_from_sim no)\n\t\t(at %s %s 0)\n\t\t%s\n\t\t(uuid "%s")\n\t)'
            % (s.replace('"', '\\"').replace('\n', '\\n'), x, y, _eff('left bottom'), uid()))


# power symbol rotation so the body points away from the pin
def _pwr_ang(net, ox, oy):
    down = net == 'GND'
    if oy > 0: return 0 if down else 180
    if oy < 0: return 180 if down else 0
    if ox > 0: return 90 if down else 270
    return 270 if down else 90


PWR_COUNTER = [0]


class Sheet:
    def __init__(self, name, fname, title, paper='A3'):
        self.name, self.fname, self.title, self.paper = name, fname, title, paper
        self.parts = []
        self.notes = []
        self.uuid = uid('sheet:' + name)
        self.flags = []          # nets that get a PWR_FLAG

    def add(self, *parts):
        self.parts.extend(parts)


def render(sheet, project, root_uuid, global_nets, width=None):
    W, H = {'A3': (420, 297), 'A2': (594, 420), 'A4': (297, 210)}[sheet.paper]
    width = width or W
    path = '/%s/%s' % (root_uuid, sheet.uuid)
    used = set()
    body = []
    x, y, rowh = 20.32, 30.48, 0
    seen_pins = set()
    for part in sheet.parts:
        x0, x1, y0, y1 = bbox(part)
        w, h = x1 - x0, y1 - y0
        if x + w > width - 15:
            x = 20.32
            y += rowh + 5.08
            rowh = 0
        X, Y = g(x - x0), g(y - y0)
        lid = part.lib
        used.add(lid)
        pins = placed_pins(part, X, Y)
        props = dict(part.props)
        top = min(p[3] for p in pins) - 1.27
        bot = max(p[3] for p in pins) + 1.27
        midx = sum(p[2] for p in pins) / len(pins)
        lp = lib_pins(libnode(lid))
        allpins = sorted(set(p[0] for p in lp), key=lambda s: (len(s), s))
        unitpins = [p[0] for p in pins]
        body.append(symbol_block(lid, part.ref, part.value, X, Y, 0, part.unit, path, project, part.fp,
                                 part.dnp, props, pins=unitpins,
                                 refpos=(g(X + 2.54) if len(pins) <= 3 else round(x - x0 + (x0 + 4), 2), round(top - 1.5, 2)),
                                 valpos=(g(X + 2.54) if len(pins) <= 3 else round(x - x0 + (x0 + 4), 2), round(bot + 2.5, 2)),
                                 desc=part.note or ''))
        for nb, nm, ex, ey, ox, oy, typ in pins:
            key = (ex, ey)
            if key in seen_pins:
                continue
            seen_pins.add(key)
            if nb not in part.pins:
                raise SystemExit('%s pin %s (%s) has no net in spec' % (part.ref, nb, nm))
            net = part.pins[nb]
            if net is None:
                body.append(no_connect(ex, ey))
                continue
            sx, sy = round(ex + ox * STUB, 3), round(ey + oy * STUB, 3)
            body.append(wire((ex, ey), (sx, sy)))
            if net in POWER_NETS:
                PWR_COUNTER[0] += 1
                plid = 'power:' + net
                used.add(plid)
                body.append(symbol_block(plid, '#PWR%04d' % PWR_COUNTER[0], net, sx, sy, _pwr_ang(net, ox, oy), 1,
                                         path, project, hide_ref=True,
                                         valpos=(sx, round(sy + (3.2 if (net == 'GND') == (oy >= 0) else -3.2), 2)),
                                         pins=['1'], hide_val=False))
            else:
                body.append(label(net, sx, sy, ox, oy, net in global_nets))
        x += w + 5.08
        rowh = max(rowh, h)
    for net in sheet.flags:
        y_f = y + rowh + 10.16
        PWR_COUNTER[0] += 1
        used.add('power:PWR_FLAG')
        fx = g(20.32 + 15.24 * sheet.flags.index(net))
        fy = g(y_f)
        body.append(symbol_block('power:PWR_FLAG', '#FLG%04d' % PWR_COUNTER[0], 'PWR_FLAG', fx, fy, 0, 1, path, project,
                                 hide_ref=True, valpos=(fx, fy - 3), pins=['1']))
        body.append(wire((fx, fy), (fx, fy + STUB)))
        if net in POWER_NETS:
            PWR_COUNTER[0] += 1
            used.add('power:' + net)
            body.append(symbol_block('power:' + net, '#PWR%04d' % PWR_COUNTER[0], net, fx, round(fy + STUB, 3),
                                     0 if net == 'GND' else 180, 1, path, project, hide_ref=True,
                                     valpos=(fx, round(fy + STUB + 3.2, 2)), pins=['1']))
        else:
            body.append(label(net, fx, round(fy + STUB, 3), 0, 1, net in global_nets))
    ny = 15.24
    for n in sheet.notes:
        body.append(text(n, 20.32, ny))
        ny += 5.08 * (n.count('\n') + 1)
    libs = '\n'.join('\t\t' + LIB[l].strip().replace('\n', '\n\t\t') if not LIB[l].startswith('\t') else LIB[l]
                     for l in sorted(used))
    hdr = ('(kicad_sch\n\t(version 20260306)\n\t(generator "eeschema")\n\t(generator_version "10.0")\n\t(uuid "%s")\n\t(paper "%s")\n'
           '\t(title_block\n\t\t(title "The Harp - %s")\n\t\t(rev "A")\n\t\t(company "The Frogmouth")\n\t)\n\t(lib_symbols\n%s\n\t)\n'
           % (sheet.uuid, sheet.paper, sheet.title, libs))
    return hdr + "\n".join(body) + "\n)\n"


def root_sheet(project, root_uuid, sheets, note):
    out = ['(kicad_sch', '\t(version 20260306)', '\t(generator "eeschema")', '\t(generator_version "10.0")',
           '\t(uuid "%s")' % root_uuid, '\t(paper "A3")',
           '\t(title_block\n\t\t(title "The Harp")\n\t\t(rev "A")\n\t\t(company "The Frogmouth")\n\t)', '\t(lib_symbols)']
    out.append(text(note, 30, 30))
    for i, sh in enumerate(sheets):
        cx = 40 + (i % 4) * 90
        cy = 70 + (i // 4) * 50
        out.append(('\t(sheet\n\t\t(at %s %s)\n\t\t(size 63.5 25.4)\n\t\t(exclude_from_sim no)\n\t\t(in_bom yes)\n\t\t(on_board yes)\n\t\t(dnp no)\n'
                    '\t\t(fields_autoplaced yes)\n\t\t(stroke\n\t\t\t(width 0.152)\n\t\t\t(type solid)\n\t\t)\n\t\t(fill\n\t\t\t(color 0 0 0 0)\n\t\t)\n'
                    '\t\t(uuid "%s")\n%s\n%s\n\t\t(instances\n\t\t\t(project "%s"\n\t\t\t\t(path "/%s"\n\t\t\t\t\t(page "%d")\n\t\t\t\t)\n\t\t\t)\n\t\t)\n\t)')
                   % (cx, cy, sh.uuid,
                      _prop('Sheetname', sh.name, cx, round(cy - 0.7, 2), justify='left bottom'),
                      _prop('Sheetfile', sh.fname, cx, round(cy + 26, 2), justify='left top'),
                      project, root_uuid, i + 2))
    out.append('\t(sheet_instances\n\t\t(path "/"\n\t\t\t(page "1")\n\t\t)\n\t)\n)\n')
    return '\n'.join(out)
