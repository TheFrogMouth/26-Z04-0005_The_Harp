import os
HERE = os.path.dirname(os.path.abspath(__file__))
import re, sys
sys.path.insert(0, os.path.join(HERE, '..', 'harp_schematic'))
PCB = os.path.join(HERE, '..', '..', 'kicad', 'the_harp', 'The Harp.kicad_pcb')

def footprints(t):
    starts = [m.start() for m in re.finditer(r'\n\t\(footprint "', t)]
    out = []
    for i, s in enumerate(starts):
        e = starts[i + 1] if i + 1 < len(starts) else None
        b = t[s:e] if e else t[s:]
        if e is None:      # last footprint: cut at its closing "\n\t)"
            k = b.find('\n\t)\n'); b = b[:k + 3]; e = s + len(b)
        ref = re.search(r'\(property "Reference" "([^"]+)"', b).group(1)
        out.append(dict(ref=ref, s=s, e=e, b=b))
    return out

def spec_nets():
    import harp_spec
    from collections import defaultdict
    sheets_of = defaultdict(set)
    parts = {}
    for sh in harp_spec.SHEETS:
        for p in sh.parts:
            for pin, net in p.pins.items():
                if net: sheets_of[net].add(sh.name)
            d = parts.setdefault(p.ref, dict(sheet=sh.name, value=p.value, fp=p.fp, lib=p.lib, pins={}, dnp=p.dnp, props=p.props or {}))
            d['pins'].update(p.pins)
    POWER = {'GND', '+3V3', '+5V', '+9V', 'VDDA'}
    def name(net, sheet):
        if net is None: return None
        if net in POWER or len(sheets_of[net]) > 1: return net
        return '/%s/%s' % (sheet, net)
    for ref, d in parts.items():
        d['padnet'] = {pin: name(net, d['sheet']) for pin, net in d['pins'].items()}
    return parts
