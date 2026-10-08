"""Placement v2 (2026-10-08): two-sided. The bottom takes the parts that gain nothing from the top
(relay and its driver, LED and footswitch drivers, pot RC filters, expression buffer, SWD and
footswitch pads) so the top middle holds the codec next to the MCU's SAI pins and the ADC driver
next to the input buffers."""
import os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'build'); os.makedirs(OUT, exist_ok=True)
sys.path.insert(0, HERE)
from place import *

G = {   # name: home (face X, Y), side, anchor IC, refs
 'relay': dict(xy=(0, -26),  side='B', ic='K401', refs='K401 Q401 R406 R407 D402 R405'),
 'leds':  dict(xy=(0, -35),  side='B', ic=None,   refs='Q402 R404 R408 R409 Q403 R411 R412 R413 R410 C408 R414 C409'),
 'exp':   dict(xy=(20, 12),  side='B', ic='U401', refs='U401 R415 R416 R417 C410 C411 R418 C412'),
 'pads':  dict(xy=(-18, 30), side='B', ic=None,   refs='W201 J405 J407'),
 'pots':  dict(xy=(0, 10),   side='B', ic=None,   refs='R101 C101 R102 C102 R103 C103 R105 C105'),
 'in':    dict(xy=(19, -22), side='F', ic='U701', refs='U701 R701 C701 R702 R703 R704 C707 R705 C702 C703 R720 C708 R721 R722 C709 D403 D407 D406'),
 'mcu':   dict(xy=(0, -21.5),side='F', ic='U201', refs='J408 U202 C201 C202 C203 C204 C205 C206 C207 C208 C209 C210 C211 C212 C213 C214 R201 R202 R203 R204 FB201 Y201 R107 R108 C104'),
 'adc':   dict(xy=(17, -4),  side='F', ic='U601', refs='U601 C601 C602 C603 C604 C608 C609 C610 R601 R602 R603 R604 R605 R606 '
                                                      'R607 R608 R609 R610 R611 R612 C611 C612 C613 C614 C618'),
 'codec': dict(xy=(-17, -4), side='F', ic='IC501', refs='IC501 C605 C606 C607 C615 C616 C617 U501 C501 C502 C503 C504 C505 C506 C507 C508 C509 R501 R504 R505'),
 'out':   dict(xy=(-17, 24), side='F', ic='U702', refs='U702 R706 R707 R708 R709 R710 R711 R712 R713 R714 R715 R716 R717 R718 R719 C704 C705 C706 D404 D405'),
 'buck':  dict(xy=(-14, 48), side='F', ic='U301', refs='U301 L301 D301 D302 FB301 C301 C302 C303 C304 C305 R301 R302 R303 C306 C307'),
 'ldo':   dict(xy=(14, 48),  side='F', ic='U302', refs='FB302 C308 C309 U302 C310 C311 FB303 C312'),
}
ORDER = ['relay', 'in', 'mcu', 'adc', 'codec', 'out', 'leds', 'exp', 'pads', 'pots', 'buck', 'ldo']
SPOT = {'J408': (-21.75, -22.0), 'U202': (0, -34), 'IC501': (-18, -4), 'U601': (17, -4), 'U701': (19, -22), 'U702': (-17, 24),
        'K401': (0, -24), 'U401': (20, 12), 'U501': (-2, 24), 'W201': (-18, 30), 'J405': (-14, 14), 'J407': (14, 14)}
ROTS = {'J408': (90,)}
PIN_TARGET = {'C605': ('IC501', ('4', '5')), 'C606': ('IC501', ('4',)), 'C607': ('IC501', ('5',)),     # anti-alias caps at the
              'C615': ('IC501', ('2', '3')), 'C616': ('IC501', ('2',)), 'C617': ('IC501', ('3',))}     # codec's input pins
def pin_target(r):
    ic, pins = PIN_TARGET[r]
    pts = [(px, py) for p, px, py in padpos(ic, *pos[ic]) if p['num'] in pins]
    return sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts)
for g in G.values():
    g['refs'] = [r for r in g['refs'].split() if r in L and r not in FIXED]
missing_from_groups = set(L) - set(FIXED) - {r for g in G.values() for r in g['refs']}
assert not missing_from_groups, missing_from_groups

def area(r):
    b = bbox(r, 0, 0, 0); return (b[1] - b[0]) * (b[3] - b[2])
for gname in ORDER:
    g = G[gname]
    rest = list(g['refs'])
    firsts = [r for r in rest if r in SPOT or r == g['ic']]
    firsts.sort(key=lambda r: -area(r))
    for r in firsts:
        rest.remove(r)
        tx, ty = SPOT.get(r) or g['xy']
        place(r, tx, ty, rots=ROTS.get(r, (0, 90, 180, 270)), side=g['side'])
    while rest:
        def score(r):
            sig = [p['net'] for p in L[r]['pads'] if p['net'] and p['net'] not in POWER]
            hit = sum(1 for n in sig if placed_pads(n))
            dec = all(p['net'] in POWER for p in L[r]['pads'] if p['net'])
            return (0 if dec else 1, -hit, -area(r))
        rest.sort(key=score)
        pinned = [x for x in rest if x in PIN_TARGET]
        r = pinned[0] if pinned else rest.pop(0)
        if pinned: rest.remove(r)
        tx, ty = pin_target(r) if r in PIN_TARGET else target(r, g)
        place(r, tx, ty, side=g['side'])
missing = [r for g in G.values() for r in g['refs'] if r not in pos]
print('placed', len(pos), 'missing', missing, 'bottom', sum(1 for r in SIDE if SIDE[r] == 'B'))
json.dump({r: k for k, g in G.items() for r in g['refs']}, open(os.path.join(OUT, 'groups.json'), 'w'))
json.dump({r: list(v) + [SIDE.get(r, L[r]['layer'][0])] for r, v in pos.items()}, open(os.path.join(OUT, 'pos.json'), 'w'))
