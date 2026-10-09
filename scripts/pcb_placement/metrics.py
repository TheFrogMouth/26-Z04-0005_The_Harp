"""Net-length and decoupling metrics of build/pos.json (half-perimeter of each net's pads)."""
import os, sys, json, math
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import place
from collections import defaultdict
pos = json.load(open(os.path.join(HERE, 'build', 'pos.json')))
P = defaultdict(list)
for r, (x, y, a, sd) in pos.items():
    for p, px, py in place.padpos(r, x, y, a, sd):
        if p['net']: P[p['net']].append((r, px, py))
def find(n):
    for k in P:
        if k == n or k.endswith('/' + n): return k
def hp(n):
    v = P[find(n)]; xs = [p[1] for p in v]; ys = [p[2] for p in v]
    return round(max(xs) - min(xs) + max(ys) - min(ys), 1)
KEY = ['IN', 'EFFECT_IN', 'IN_R', 'EFFECT_IN_BUF', 'EFFECT_IN_BUF_R', 'FDA_INP', 'FDB_INP', 'FDA_INN', 'FDB_INN',
       'ADC_L_P', 'ADC_L_N', 'ADC_R_P', 'ADC_R_N', 'DAC_L_P', 'DAC_R_P', 'EFFECT_OUT_L', 'EFFECT_OUT_R', 'OUT_L',
       'CODEC_BICK', 'CODEC_SDTI', 'CODEC_SDTO', 'CODEC_LRCK', 'CODEC_MCLK', 'VCOM_A', 'VCOM_B', 'QSPI_IO0']
if __name__ == '__main__':
    for n in KEY: print(f'{n:16} {hp(n):6}')
    tot = sum((max(p[1] for p in v) - min(p[1] for p in v)) + (max(p[2] for p in v) - min(p[2] for p in v))
              for n, v in P.items() if n not in ('GND', '+3V3', '+5V', '+9V', 'VDDA') and not n.startswith('unconnected') and len(v) > 1)
    print('total signal half-perimeter', round(tot))
