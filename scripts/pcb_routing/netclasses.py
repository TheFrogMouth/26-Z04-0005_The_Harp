"""Write the routing net classes (nets.py) into the KiCad project, so KiCad's DRC and
interactive router use the same widths and clearances as the scripted routing.

One pattern per net (exact name). Default stays for anything new; its via becomes 0.6/0.3.
"""
import os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kpcb, nets

PRO = os.path.join(HERE, '..', '..', 'kicad', 'the_harp', 'The Harp.kicad_pro')
NAMES = {'GND': 'GND', 'RAIL': 'Rail', 'POWER': 'Power', 'AUDIO': 'Audio', 'DIGITAL': 'Digital', 'CTRL': 'Control'}


def main():
    d = json.load(open(PRO))
    ns = d['net_settings']
    default = next(c for c in ns['classes'] if c['name'] == 'Default')
    default['via_diameter'], default['via_drill'] = nets.VIA
    classes = [default]
    for i, (k, name) in enumerate(NAMES.items()):
        c = dict(default)
        c.update(name=name, priority=i, clearance=nets.CLEAR[k], track_width=nets.WIDTH[k])
        classes.append(c)
    ns['classes'] = classes
    _, _, _, pads = kpcb.load()
    allnets = sorted({p['net'] for p in pads if p['net'] and not p['net'].startswith('unconnected')})
    ns['netclass_patterns'] = [dict(netclass=NAMES[nets.kind(n)], pattern=n) for n in allnets]
    ds = d['board']['design_settings']
    ds['track_widths'] = [0.0, 0.254, 0.508, 0.762, 1.0]       # the Alchemist's set
    default['clearance'] = 0.1524
    ds['rules']['min_track_width'] = 0.1016                     # NRST through the SWD needle pads
    vd = {(v['diameter'], v['drill']) for v in ds['via_dimensions']} | {nets.VIA}
    ds['via_dimensions'] = [dict(diameter=a, drill=b) for a, b in sorted(vd)]
    json.dump(d, open(PRO, 'w'), indent=2)
    open(PRO, 'a').write('\n')
    print('classes', [c['name'] for c in classes], 'patterns', len(ns['netclass_patterns']))


if __name__ == '__main__':
    main()
