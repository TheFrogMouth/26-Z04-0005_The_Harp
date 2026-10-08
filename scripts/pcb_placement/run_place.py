import os
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'build'); os.makedirs(OUT, exist_ok=True)
import sys
sys.path.insert(0, HERE)
from place import *

# zone homes (face X, Y) after docs/pcb-plan.md "Zoning"; ic = anchor for decoupling
G = {
 'buck':   dict(xy=(-14, 48), ic='U301', refs='J401? U301 L301 D301 D302 FB301 C301 C302 C303 C304 C305 R301 R302 R303 C306 C307'),
 'ldo':    dict(xy=(14, 48),  ic='U302', refs='FB302 C308 C309 U302 C310 C311 FB303 C312'),
 'codec':  dict(xy=(-17, -4), ic='IC501', refs='IC501 U501 C501 C502 C503 C504 C505 C506 C507 C508 C509 R501 R504 R505'),
 'adc':    dict(xy=(17, -4),  ic='U601', refs='U601 C601 C602 C603 C604 C605 C606 C607 C608 C609 C610 R601 R602 R603 R604 R605 R606 '
                                               'R607 R608 R609 R610 R611 R612 C611 C612 C613 C614 C615 C616 C617 C618'),
 'mcu':    dict(xy=(10, -29), ic='U201', refs='J408 U202 C201 C202 C203 C204 C205 C206 C207 C208 C209 C210 C211 C212 C213 C214 R201 R202 R203 R204 FB201 Y201'),
 'in':     dict(xy=(23, -17), ic='U701', refs='U701 R701 C701 R702 R703 R704 C707 R705 C702 C703 R720 C708 R721 R722 C709'),
 'out':    dict(xy=(-15, -18), ic='U702', refs='U702 R706 R707 R708 R709 R710 R711 R712 R713 R714 R715 R716 R717 R718 R719 C704 C705 C706'),
 'io':     dict(xy=(22, -30), ic='U401', refs='J405 U401 R415 R416 R417 C410 C411 R418 C412 D403 D404 D405 D406 D407 J407 R404 R408 R409 R410 R411 R412 R413 R414 C408 C409 Q403'),
 'relay':  dict(xy=(-18, -30), ic='K401', refs='K401 W201 Q401 R406 R407 D402 R405 Q402'),
 'ctl':    dict(xy=(0, 24),   ic=None, refs='R101 C101 R102 C102 R103 C103 R105 C105 C104 R107 R108'),
}
for g in G.values():
    g['refs'] = [r for r in g['refs'].split() if r in L and r not in FIXED]
ORDER = ['relay', 'in', 'mcu', 'adc', 'codec', 'out', 'io', 'buck', 'ldo', 'ctl']
ANCHOR = {'mcu': [], 'codec': ['IC501', 'U501'], 'adc': ['U601'], 'in': ['U701'], 'out': ['U702'], 'relay': ['K401'],
          'io': ['J407', 'J405', 'U401'], 'buck': ['U301', 'L301'], 'ldo': ['U302'], 'ctl': []}
SPOT = {'K401': (17, -4), 'IC501': (-18, -4), 'U501': (-10, 22), 'U601': (-17, -24), 'U701': (19, -22), 'U702': (16, 24),
        'J407': (21, -35), 'U401': (24, -30), 'W201': (-3, 24), 'U202': (0, -34), 'J405': (10, 47)}
home_of = {r: g for g in G.values() for r in g['refs']}
def area(r):
    b = bbox(r, 0, 0, 0); return (b[1] - b[0]) * (b[3] - b[2])
for gname in ORDER:
    g = G[gname]
    for r in ANCHOR[gname]:
        tx, ty = SPOT.get(r) or (g['xy'] if r == g['ic'] else target(r, g))
        place(r, tx, ty, rots=(0, 90, 180, 270))
    rest = [r for r in g['refs'] if r not in pos]
    if gname == 'mcu':
        rest.remove('J408'); place('J408', -22, -23, rots=(90,))
    for r in ('U202',) + (('W201',) if gname == 'relay' else ()):
        if r in rest:
            rest.remove(r); place(r, *SPOT[r], rots=(0, 90, 180, 270))
    while rest:
        def score(r):
            sig = [p['net'] for p in L[r]['pads'] if p['net'] and p['net'] not in POWER]
            hit = sum(1 for n in sig if placed_pads(n))
            dec = all(p['net'] in POWER for p in L[r]['pads'] if p['net'])
            return (0 if dec else 1, -hit, -area(r))
        rest.sort(key=score)
        r = rest.pop(0)
        tx, ty = target(r, g)
        place(r, tx, ty)
import json
missing = [r for g in G.values() for r in g['refs'] if r not in pos]
print('placed', len(pos), 'missing', missing)
json.dump({ref: k for k, g in G.items() for ref in g['refs']}, open(os.path.join(OUT, 'groups.json'), 'w'))
import json
json.dump({r: list(v) for r, v in pos.items()}, open(os.path.join(OUT, 'pos.json'), 'w'))
