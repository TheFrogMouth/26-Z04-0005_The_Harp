"""Write a Specctra DSN of the Harp board for Freerouting, and read its SES back.

Every footprint becomes its own image placed at the footprint origin, unrotated, on the front;
pad shapes are written already rotated and on their real copper layers, so bottom-side parts
need no mirroring. Coordinates: um, Y up (DSN) <-> mm, Y down (KiCad).
"""
import math, re
import kpcb, nets

U = 1000.0      # um per mm


def q(s):
    return '"%s"' % s.replace('"', "'")


def P(x, y):
    return '%d %d' % (round(x * U), round(-y * U))


def pin_names(fp):
    seen, out = {}, []
    for p in fp['pads']:
        n = p['num'] or '@'
        k = seen.get(n, 0); seen[n] = k + 1
        out.append(n if k == 0 else '%s@%d' % (n, k))
    return out


def padstack(p):
    """Shape list (one per copper layer) relative to the pad centre, DSN units."""
    shapes = []
    for lay in p['layers']:
        if p['shape'] == 'circle':
            shapes.append('(circle %s %d)' % (lay, round(p['w'] * U)))
        elif p['shape'] == 'oval':
            L = (max(p['w'], p['h']) - min(p['w'], p['h'])) / 2
            dx, dy = (L, 0) if p['w'] >= p['h'] else (0, L)
            dx, dy = kpcb.rot(dx, dy, p['a'])
            shapes.append('(path %s %d %s %s)' % (lay, round(min(p['w'], p['h']) * U), P(-dx, -dy), P(dx, dy)))
        elif p['shape'] == 'rect' and p['a'] % 90 == 0:
            w, h = (p['w'], p['h']) if p['a'] % 180 == 0 else (p['h'], p['w'])
            shapes.append('(rect %s %s %s)' % (lay, P(-w / 2, h / 2), P(w / 2, -h / 2)))
        else:
            c = dict(p, x=0.0, y=0.0)
            pts = kpcb.pad_polygon(c, n=2)
            shapes.append('(polygon %s 0 %s)' % (lay, ' '.join(P(x, y) for x, y in pts)))
    return shapes


def write(path, fps, outline_pts, phase_nets, classes, keepouts=(), fixed=(), plane=True, auto=None):
    """phase_nets: nets to route now; fixed: earlier wires/vias (dicts) kept as protected.
    classes: {class name: dict(nets=[...], width=mm, clear=mm, layers=[...])}
    keepouts: [(layer, [(x, y), ...], kind)] kind 'keepout' | 'via_keepout' | 'wire_keepout'.
    auto: dict(via_costs=, plane_via_costs=, layers={layer: (active, direction, cost, against_cost)})"""
    stacks, images, comps = {}, [], []
    all_nets = {}
    for fp in fps:
        pins = []
        for p, name in zip(fp['pads'], pin_names(fp)):
            sh = padstack(p)
            key = ' '.join(sh)
            if p['kind'] == 'np_thru_hole':
                key = 'NPTH ' + key
            if key not in stacks:
                stacks[key] = 'PS%d' % len(stacks)
            pins.append('(pin %s %s %s)' % (stacks[key], q(name), P(p['x'] - fp['x'], p['y'] - fp['y'])))
            if p['net'] and not p['net'].startswith('unconnected'):
                all_nets.setdefault(p['net'], []).append('%s-%s' % (fp['ref'], name))
        img = 'IMG_' + fp['ref']
        images.append('(image %s\n   %s\n  )' % (q(img), '\n   '.join(pins)))
        comps.append('(component %s (place %s %s front 0))' % (q(img), q(fp['ref']), P(fp['x'], fp['y'])))
    via_name = 'Via600_300'
    o = []
    o.append('(pcb "the_harp"')
    o.append(' (parser (string_quote ") (space_in_quoted_tokens on) (host_cad "KiCad\'s Pcbnew") (host_version "10.0"))')
    o.append(' (resolution um 10)\n (unit um)')
    o.append(' (structure')
    for i, l in enumerate(kpcb.CU):
        typ = 'signal'
        o.append('  (layer %s (type %s) (property (index %d)))' % (l, typ, i))
    o.append('  (boundary (path pcb 0 %s))' % ' '.join(P(x, y) for x, y in outline_pts + [outline_pts[0]]))
    if plane:
        o.append('  (plane GND (polygon In1.Cu 0 %s))' % ' '.join(P(x, y) for x, y in outline_pts))
    for k, (lay, pts, kind) in enumerate(keepouts):
        o.append('  (%s "K%d" (polygon %s 0 %s))' % (kind, k, lay, ' '.join(P(x, y) for x, y in pts)))
    o.append('  (via %s)' % via_name)
    o.append('  (rule (width 200) (clearance 150) (clearance 150 (type default_smd)) (clearance 50 (type smd_smd)))')
    if auto:
        o.append('  (autoroute_settings (fanout %s) (autoroute on) (postroute on) (vias on) (via_costs %d) '
                 '(plane_via_costs %d) (start_ripup_costs 100) (start_pass_no 1)' % (
                     'on' if auto.get('fanout') else 'off', auto['via_costs'], auto['plane_via_costs']))
        for l in kpcb.CU:
            act, dirn, c, ca = auto['layers'][l]
            o.append('   (layer_rule %s (active %s) (preferred_direction %s) (preferred_direction_trace_costs %.1f) '
                     '(against_preferred_direction_trace_costs %.1f))' % (l, 'on' if act else 'off', dirn, c, ca))
        o.append('  )')
    o.append(' )')
    o.append(' (placement\n  %s\n )' % '\n  '.join(comps))
    o.append(' (library')
    o.extend('  ' + i for i in images)
    for key, name in stacks.items():
        sh = key.replace('NPTH ', '')
        o.append('  (padstack %s %s (attach off))' % (name, ' '.join('(shape %s)' % s for s in re.findall(r'\([^()]*\)', sh))))
    d, dr = nets.VIA
    o.append('  (padstack %s %s (attach off))' % (via_name, ' '.join('(shape (circle %s %d))' % (l, round(d * U)) for l in kpcb.CU)))
    o.append(' )')
    o.append(' (network')
    routed = set(phase_nets) | {w['net'] for w in fixed}
    for n in sorted(routed):
        if n in all_nets:
            o.append('  (net %s (pins %s))' % (q(n), ' '.join(q(x) if ' ' in x else x for x in all_nets[n])))
    for cname, c in classes.items():
        members = [n for n in c['nets'] if n in routed and n in all_nets]
        if not members:
            continue
        o.append('  (class %s %s (circuit (use_via %s) (use_layer %s)) (rule (width %d) (clearance %d)))' % (
            q(cname), ' '.join(q(n) for n in members), via_name, ' '.join(c['layers']),
            round(c['width'] * U), round(c['clear'] * U)))
    o.append(' )')
    o.append(' (wiring')
    for w in fixed:
        if w['type'] == 'via':
            o.append('  (via %s %s (net %s) (type protect))' % (via_name, P(w['x'], w['y']), q(w['net'])))
        else:
            o.append('  (wire (path %s %d %s) (net %s) (type protect))' % (
                w['layer'], round(w['w'] * U), ' '.join(P(x, y) for x, y in w['pts']), q(w['net'])))
    o.append(' )')
    o.append(')')
    open(path, 'w').write('\n'.join(o) + '\n')
    return all_nets


def read_ses(path):
    """Wires and vias from a Freerouting session file, KiCad coordinates (mm, Y down)."""
    t = open(path).read()
    tree = kpcb.parse(t)
    routes = kpcb.find(tree, 'routes')
    res = kpcb.find(routes, 'resolution')
    scale = float(res[2])          # units per um
    k = 1.0 / (scale * U)
    out = []
    netout = kpcb.find(routes, 'network_out')
    for n in kpcb.findall(netout, 'net'):
        name = n[1]
        for w in kpcb.findall(n, 'wire'):
            path = kpcb.find(w, 'path')
            vals = [float(v) for v in path[3:] if not isinstance(v, list)]
            pts = [(vals[i] * k, -vals[i + 1] * k) for i in range(0, len(vals) - 1, 2)]
            out.append(dict(type='wire', net=name, layer=path[1], w=float(path[2]) * k, pts=pts))
        for v in kpcb.findall(n, 'via'):
            out.append(dict(type='via', net=name, x=float(v[2]) * k, y=-float(v[3]) * k))
    return out
