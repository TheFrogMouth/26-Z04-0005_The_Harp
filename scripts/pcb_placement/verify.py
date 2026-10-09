"""Check the board file itself (geometry re-read from the file, both sides)."""
import os, sys, json, math
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', 'harp_schematic'))
from geom import load, box
from kisch import parse
import place
t, G = load(); parse(t)
side_parts = {'F': [], 'B': []}; holes = {'F': [], 'B': []}
for g in G:
    sd = g['layer'][0]
    c = g['cy'].get(sd) or box(g)
    side_parts[sd].append((g['ref'], c))
    for p in g['pads']:
        if p['kind'] in ('thru_hole', 'np_thru_hole'):
            s = max(p['w'], p['h']) / 2
            holes['B' if sd == 'F' else 'F'].append((g['ref'], (p['x'] - s, p['x'] + s, p['y'] - s, p['y'] + s)))
def ov(a, b): return a[0] < b[1] - 1e-3 and a[1] > b[0] + 1e-3 and a[2] < b[3] - 1e-3 and a[3] > b[2] + 1e-3
for sd in 'FB':
    P = side_parts[sd]
    o = [(P[i][0], P[j][0]) for i in range(len(P)) for j in range(i + 1, len(P)) if ov(P[i][1], P[j][1])]
    h = sorted({(r, q) for r, a in P for q, b in holes[sd] if r != q and ov(a, b)})
    e = [r for r, c in P if not place.in_board(c) and r not in ('J401', 'J402', 'J403', 'J404', 'J406')]
    print(sd, 'parts', len(P), '| overlaps', o, '| over holes', h, '| outside', e)
MOD = place.MODULE
print('tall under OLED:', [r for r, c in side_parts['F'] if r in ('K401', 'C502', 'C508') and ov(c, MOD)])
# flip convention: pads read from the file vs the placer's model
pos = json.load(open(os.path.join(HERE, 'build', 'pos.json')))
worst = 0
for g in G:
    if g['ref'] not in pos: continue
    x, y, a, sd = pos[g['ref']]
    model = {(p['num'], round(px, 2), round(py, 2)) for p, px, py in place.padpos(g['ref'], x, y, a, sd)}
    for p in g['pads']:
        d = min(math.hypot(p['x'] - mx, p['y'] - my) for n, mx, my in model if n == p['num'])
        worst = max(worst, d)
print('max pad position difference file vs placer: %.4f mm' % worst)
