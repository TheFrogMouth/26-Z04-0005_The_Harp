"""Route the Harp board, one net class at a time.

  gnd      every SMD GND pad gets its own via to the In1.Cu plane (fanout.py)
  rails    every SMD pad on +3V3/+5V/+9V gets its own via (fanout.py); Freerouting joins
           the vias and through-hole pins on In2.Cu, the only layer the rails may use
  power    local power nets (buck, LDO, DC in, VDDA, relay coil, LED current), wide, F/B
  core     digital round the MCU (codec interface, QSPI, crystal, SWD, OLED, reset): F.Cu/B.Cu,
           kept out of the audio region on both layers. Short, so it goes first
  audio    F.Cu/B.Cu, kept out of the digital region on both layers; before the long digital
           lines, so the bypass paths get the corridors under the MCU to the relay
  drive    digital lines out to the bottom-side LED and relay drivers, kept out of audio
  ctrl     pots, toggles, footswitches, expression (DC): kept out of the audio region
  repair   whatever is still open, with the region keepouts lifted (rails still In2 only) and
           the signal tracks unlocked, so the router may move them to make room; GND, rail and
           power copper stays fixed. The nets it changed are listed so they can be checked

Each Freerouting phase sees only its own nets; everything routed before is fixed (protected).
Signals never use In2.Cu. Vias cost more than in Freerouting's default (80 against 50), so a
track changes side rarely; much higher and it takes long one-sided detours instead.

Usage: FREEROUTING=/path/freerouting.jar JAVA=/path/java python3 route.py [phase ...]
With phase names, reruns those phases on top of the others kept in build/routes.json.
Writes build/<phase>.dsn/.ses/.log and build/routes.json.
"""
import os, sys, json, subprocess, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kpcb, nets, dsn, regions, fanout
from shapely.geometry import Polygon

JAR = os.environ.get('FREEROUTING', '/tmp/claude-0/fr/freerouting-2.4.1-executable.jar')
JAVA = os.environ.get('JAVA', '/usr/lib/jvm/java-25-openjdk-amd64/bin/java')
SIG = ['F.Cu', 'B.Cu']

PHASES = [
    dict(name='gnd', kinds={'GND'}, fanout=True),
    dict(name='rails', kinds={'RAIL'}, fanout=True, passes=16, via_costs=50),
    dict(name='power', kinds={'POWER'}, passes=16, via_costs=60),
    dict(name='core', kinds={'DIGITAL'}, drive=False, passes=20, via_costs=80, keep_out_of='AUDIO'),
    dict(name='audio', kinds={'AUDIO'}, passes=25, via_costs=80, keep_out_of='DIGITAL'),
    dict(name='drive', kinds={'DIGITAL'}, drive=True, passes=20, via_costs=80, keep_out_of='AUDIO'),
    dict(name='ctrl', kinds={'CTRL'}, passes=20, via_costs=80, keep_out_of='AUDIO'),
    dict(name='repair', kinds={'RAIL', 'POWER', 'AUDIO', 'DIGITAL', 'CTRL'}, passes=30, via_costs=80, repair=True,
         loose={'AUDIO', 'DIGITAL', 'CTRL'}),
]


def in_phase(phase, net):
    if nets.kind(net) not in phase['kinds']:
        return False
    return 'drive' not in phase or phase['drive'] == nets.is_drive(net)


def phase_of(net):
    return next(p['name'] for p in PHASES if not p.get('repair') and in_phase(p, net))


def no_via_w201(pads):
    """No via under the SWD needle adapter's pads (Relic rule): their box plus 0.6 mm."""
    ps = [p for p in pads if p['ref'] == 'W201' and p['kind'] == 'smd']
    r = ps[0]['w'] / 2 + 0.6
    x0 = min(p['x'] for p in ps) - r; x1 = max(p['x'] for p in ps) + r
    y0 = min(p['y'] for p in ps) - r; y1 = max(p['y'] for p in ps) + r
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def layers_of(kind):
    if kind == 'GND':
        return ['F.Cu', 'In1.Cu', 'B.Cu']
    if kind == 'RAIL':
        return ['In2.Cu']
    return SIG


def classes_for(netnames):
    out = {}
    for n in netnames:
        k = nets.kind(n); w = nets.width(n)
        c = out.setdefault('%s_%d' % (k, round(w * 1000)), dict(nets=[], width=w, clear=nets.CLEAR[k], layers=layers_of(k)))
        c['nets'].append(n)
    return out


def freeroute(phase, fps, pads, outline, fixed, phase_nets):
    name = phase['name']
    allnets = sorted(set(phase_nets) | {w['net'] for w in fixed})
    keep = [('B.Cu', no_via_w201(pads), 'via_keepout')]
    if phase.get('keep_out_of'):
        side = phase['keep_out_of']
        for l in SIG:
            for poly in regions.territory(pads, outline, l, side):
                keep.append((l, list(poly.exterior.coords)[:-1], 'wire_keepout'))
        if phase.get('shadow'):          # B.Cu also stays out from under the top-side region
            for poly in regions.territory(pads, outline, 'F.Cu', side):
                keep.append(('B.Cu', list(poly.exterior.coords)[:-1], 'wire_keepout'))
    d = os.path.join(kpcb.BUILD, name + '.dsn'); s = os.path.join(kpcb.BUILD, name + '.ses')
    dsn.write(d, fps, outline, phase_nets, classes_for(allnets), keepouts=keep, fixed=fixed,
              loose=phase.get('loose', ()))
    if os.path.exists(s):
        os.remove(s)
    cmd = [JAVA, '-jar', JAR, '--gui.enabled=false', '--usage_and_diagnostic_data.disable_analytics=true',
           '--router.fanout.enabled=false', '--router.scoring.via_costs=%d' % phase['via_costs'],
           '--router.scoring.plane_via_costs=5', '--router.copper_to_edge_clearance_um=500',
           '--router.hole_clearance_um=254', '-mt', '3', '-mp', str(phase['passes']), '-de', d, '-do', s]
    log = subprocess.run(cmd, capture_output=True, text=True, cwd=kpcb.BUILD)
    open(os.path.join(kpcb.BUILD, name + '.log'), 'w').write(log.stdout + log.stderr)
    if not os.path.exists(s):
        raise SystemExit('%s: no session written, see build/%s.log' % (name, name))
    keepset = set(phase_nets)
    return [w for w in dsn.read_ses(s) if w['net'] in keepset]


def run(phase, fps, pads, outline, fixed):
    t0 = time.time()
    phase_nets = sorted({p['net'] for p in pads if p['net'] and not p['net'].startswith('unconnected')
                         and in_phase(phase, p['net'])})
    new, failed = [], []
    if phase.get('fanout'):
        new, failed = fanout.fanout(fps, pads, outline, set(phase_nets), fixed, keepout=Polygon(no_via_w201(pads)))
    if phase.get('passes'):
        got = freeroute(phase, fps, pads, outline, fixed + new, phase_nets)
        if phase.get('repair'):
            # the session holds every item of the phase's nets, old (some moved) and new: it
            # replaces them all; main() drops the old ones of these nets
            mine = set(phase_nets)
            before = {key(w) for w in fixed if w['net'] in mine}
            got = dedupe(got)
            print('repair: changed', ' '.join(sorted({w['net'] for w in got if key(w) not in before})) or 'nothing')
            return got
        new = dedupe(new + got)
    print('%-8s %3d nets  %4d tracks %3d vias  %4.0f s%s' % (
        phase['name'], len(phase_nets), sum(1 for w in new if w['type'] == 'wire'),
        sum(1 for w in new if w['type'] == 'via'), time.time() - t0,
        ('  fanout failed: ' + ' '.join(failed)) if failed else ''))
    return new


def key(w):
    return (w['type'], w['net'], round(w.get('x', 0), 2), round(w.get('y', 0), 2), w.get('layer'),
            tuple((round(a, 2), round(b, 2)) for a, b in w.get('pts', [])))


def dedupe(items):
    """Drop repeats: the session hands back fixed items, split and rounded its own way (0.1 um).
    A segment already covered by kept copper of the same net on the same layer goes, as does a
    via within 0.02 mm of a kept one; tracks are kept as single segments."""
    from shapely.geometry import LineString
    from shapely.ops import unary_union
    kept, vias, cover = [], [], {}
    for w in items:
        if w['type'] == 'via':
            if any(v['net'] == w['net'] and abs(v['x'] - w['x']) < 0.02 and abs(v['y'] - w['y']) < 0.02 for v in vias):
                continue
            vias.append(w); kept.append(w)
            continue
        for a, b in zip(w['pts'], w['pts'][1:]):
            if abs(a[0] - b[0]) < 1e-6 and abs(a[1] - b[1]) < 1e-6:
                continue
            g = LineString([a, b]); k = (w['net'], w['layer'])
            c = cover.get(k)
            if c is not None and c.contains(g):
                continue
            cover[k] = g.buffer(0.01) if c is None else unary_union([c, g.buffer(0.01)])
            kept.append(dict(w, pts=[a, b]))
    return kept


def main(names):
    os.makedirs(kpcb.BUILD, exist_ok=True)
    text, tree, fps, pads = kpcb.load()
    outline = kpcb.outline(tree)
    out = os.path.join(kpcb.BUILD, 'routes.json')
    todo = [p for p in PHASES if not names or p['name'] in names]
    fixed = []
    if names and os.path.exists(out):      # keep the phases not being rerun
        rerun = set(names) - {'repair'}
        fixed = dedupe([w for w in json.load(open(out)) if phase_of(w['net']) not in rerun])
    for ph in todo:
        got = run(ph, fps, pads, outline, fixed)
        if ph.get('repair'):
            fixed = [w for w in fixed if not in_phase(ph, w['net'])]
        fixed = dedupe(fixed + got)
        json.dump(fixed, open(out, 'w'))


if __name__ == '__main__':
    main(sys.argv[1:])
