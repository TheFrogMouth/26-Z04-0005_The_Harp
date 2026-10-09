"""One-off Update-PCB-from-Schematic for The Harp, without KiCad."""
import os
HERE = os.path.dirname(os.path.abspath(__file__))
import re, sys, uuid
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, '..', 'harp_schematic'))
from pcbread import footprints, spec_nets, PCB
import schgen
from kisch import lib_pins

NS = uuid.UUID('5f1e2a7c-8d3b-4c6e-9a1f-26a040050005')
U = lambda k: str(uuid.uuid5(NS, 'pcb/' + k))
SCH = os.path.join(HERE, '..', '..', 'kicad', 'the_harp') + '/'
DSP = os.path.join(HERE, '..', '..', '..', '25-Z01-0001_DSP_Development_Board', 'kicad', 'dsp_board', 'STM32H750 DEV BOARD.kicad_pcb')

t = open(PCB).read()
parts = spec_nets()
fps = {f['ref']: f for f in footprints(t)}

# ---- symbol paths from the generated schematics
root = open(SCH + 'The Harp.kicad_sch').read()
sheet_uuid = {}
for m in re.finditer(r'\(sheet\n.*?\(property "Sheetname" "([^"]+)".*?\n\t\)', root, re.S):
    blk = m.group(0)
    sheet_uuid[m.group(1)] = re.search(r'\n\t\t\(uuid "([^"]+)"\)', blk).group(1)
def sym_uuid(sheet, ref):
    s = open(SCH + sheet + '.kicad_sch').read()
    i = s.index('(property "Reference" "%s"' % ref)
    j = s.rfind('\n\t(symbol\n', 0, i)
    return re.search(r'\(uuid "([^"]+)"\)', s[j:i]).group(1)

def pin_names(lib, unit=None):
    return {nb: nm for nb, nm, *_ in lib_pins(schgen.libnode(lib))}

def strip_cache(b):
    return re.sub(r'\n\t*\(render_cache .*?\n\t\t\t\)', '', b, flags=re.S)

def set_pad_nets(b, ref, padnet, names, old=None):
    """Rewrite each pad's (net ...) from padnet; unconnected pins get KiCad's unconnected-(...) name."""
    def sub(m):
        head, pad, body = m.group(1), m.group(2), m.group(3)
        has = re.search(r'\n\t\t\t\(net "[^"]*"\)', body)
        if pad not in padnet:
            return head + body             # mounting pads etc.: untouched
        net = padnet[pad]
        if net is None:
            prev = (old or {}).get(pad)
            net = prev if prev and prev.startswith('unconnected-') else 'unconnected-(%s-%s-Pad%s)' % (ref, names.get(pad, pad), pad)
        ins = '\n\t\t\t(net "%s")' % net
        if has:
            return head + body[:has.start()] + ins + body[has.end():]
        k = body.find('\n\t\t\t(pinfunction')
        if k < 0:
            k = body.find('\n\t\t\t(uuid')
        return head + body[:k] + ins + body[k:]
    return re.sub(r'(\(pad "([^"]+)" [^\n]*)(\n.*?\n\t\t\))', sub, b, flags=re.S)

def old_nets(b):
    return {m.group(1): (re.search(r'\(net "([^"]*)"\)', m.group(2)) or [None, None])[1]
            for m in re.finditer(r'\(pad "([^"]+)" [^\n]*\n(.*?)\n\t\t\)', b, re.S)}

log = []
# ---- 1. remove footprints no longer in the schematic
for ref in sorted(set(fps) - set(parts)):
    f = fps[ref]
    t = t.replace(f['b'], '', 1)
    log.append('removed ' + ref)

# ---- 2. update existing footprints: value, dnp, pad nets
for ref, f in footprints(t) and {x['ref']: x for x in footprints(t)}.items():
    if ref not in parts:
        continue
    d = parts[ref]
    b = f['b']
    nb = re.sub(r'(\(property "Value" ")[^"]*(")', lambda m: m.group(1) + d['value'] + m.group(2), b, count=1)
    names = pin_names(d['lib'])
    nb = set_pad_nets(nb, ref, d['padnet'], names, old_nets(b))
    if nb != b:
        t = t.replace(b, nb, 1)
        log.append('updated ' + ref)

# ---- 3. add new footprints, cloned from templates
dsp = {f['ref']: f for f in footprints(open(DSP).read())}
cur = {f['ref']: f for f in footprints(t)}
TEMPLATE = {
    'Resistor_SMD:R_0603_1608Metric': cur['R601']['b'], 'Capacitor_SMD:C_0603_1608Metric': cur['C601']['b'],
    'Capacitor_SMD:C_1206_3216Metric': cur['C701']['b'], 'Diode_SMD:D_SOD-523': cur['D403']['b'],
    'Audio_Module:SOP65P760X150-30N': dsp['IC401']['b'], 'Package_SO:SOIC-8_5.23x5.23mm_P1.27mm': dsp['U901']['b'],
}
PARK = {   # face (X, Y): parked off-board beside the existing parked groups, as Update PCB leaves new parts
    'C104': (132, 25), 'U202': (138, 10), 'D407': (132, 0),
    'R720': (132, -10), 'R721': (136, -10), 'R722': (140, -10), 'C708': (145, -10), 'C709': (150, -10),
    'R607': (132, -22), 'R608': (136, -22), 'R609': (140, -22), 'R610': (144, -22), 'R611': (148, -22), 'R612': (152, -22),
    'C611': (132, -27), 'C612': (136, -27), 'C613': (140, -27), 'C614': (144, -27), 'C615': (148, -27), 'C616': (152, -27),
    'C617': (156, -27), 'C618': (160, -27), 'IC501': (140, -45),
}
STD_PROPS = {'Reference', 'Value', 'Datasheet', 'Description', 'Footprint'}
def clone(ref):
    d = parts[ref]
    b = strip_cache(TEMPLATE[d['fp']]).lstrip('\n')
    # normalise rotation to 0
    rot = re.search(r'^\t\(footprint "[^"]+"\n\t\t\(layer "[^"]+"\)\n\t\t\(uuid "[^"]+"\)\n\t\t\(at [-\d.]+ [-\d.]+(?: ([-\d.]+))?\)', b, re.M)
    r0 = float(rot.group(1) or 0)
    X, Y = PARK[ref]
    b = re.sub(r'(\n\t\t\(at )[-\d.]+ [-\d.]+(?: [-\d.]+)?\)', r'\g<1>%g %g)' % (148.5 + X, 105 - Y), b, count=1)
    if r0:
        def fix(m):
            a = (float(m.group(3)) - r0) % 360
            return '%s%s %s%s)' % (m.group(1), m.group(2), '' if False else '', ('%g' % a) if a else '0')
        b = re.sub(r'(\n\t\t\t\(at )([-\d.]+ [-\d.]+) ([-\d.]+)\)', lambda m: '%s%s %g)' % (m.group(1), m.group(2), (float(m.group(3)) - r0) % 360), b)
    # drop non-standard properties, then rename
    b = re.sub(r'\n\t\t\(property "([^"]+)" "[^"]*"\n.*?\n\t\t\)', lambda m: m.group(0) if m.group(1) in STD_PROPS else '', b, flags=re.S)
    b = re.sub(r'\n\t\t\(property ki_[^\n]*\)', '', b)
    b = re.sub(r'(\(property "Reference" ")[^"]*', r'\g<1>' + ref, b, count=1)
    b = re.sub(r'(\(property "Value" ")[^"]*', lambda m: m.group(1) + d['value'], b, count=1)
    b = re.sub(r'(\(property "Description" ")[^"]*', r'\g<1>', b, count=1)
    extra = ''
    for k, v in d['props'].items():
        extra += ('\n\t\t(property "%s" "%s"\n\t\t\t(at 0 0 0)\n\t\t\t(layer "F.Fab")\n\t\t\t(hide yes)\n\t\t\t(uuid "%s")'
                  '\n\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t)\n\t\t\t)\n\t\t)') % (k, v, U(ref + '/prop/' + k))
    sheet = d['sheet']
    ident = '\n\t\t(path "/%s/%s")\n\t\t(sheetname "/%s/")\n\t\t(sheetfile "%s.kicad_sch")' % (sheet_uuid[sheet], sym_uuid(sheet, ref), sheet, sheet)
    b = re.sub(r'\n\t\t\(path "[^"]*"\)\n\t\t\(sheetname "[^"]*"\)\n\t\t\(sheetfile "[^"]*"\)', '', b)
    k = b.find('\n\t\t(attr')
    b = b[:k] + extra + ident + b[k:]
    # fresh uuids
    n = [0]
    def nu(m):
        n[0] += 1
        return '(uuid "%s")' % U('%s/%d' % (ref, n[0]))
    b = re.sub(r'\(uuid "[^"]+"\)', nu, b)
    b = set_pad_nets(b, ref, d['padnet'], pin_names(d['lib']))
    return '\n' + b.rstrip('\n')

new = sorted(set(parts) - {f['ref'] for f in footprints(t)})
anchor = footprints(t)[-1]
blocks = ''.join(clone(r) for r in new)
t = t[:anchor['e']] + blocks + t[anchor['e']:]
log += ['added ' + r for r in new]
open(PCB, 'w').write(t)
print('\n'.join(log))
