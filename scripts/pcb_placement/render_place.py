import os
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'build'); os.makedirs(OUT, exist_ok=True)
import sys, json, subprocess, os
sys.path.insert(0, HERE)
from place import bbox, L, padpos
D = OUT + '/'
pos = json.load(open(D + 'pos.json'))
OUTP = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else D + 'place'
groups = json.load(open(D + 'groups.json')) if os.path.exists(D + 'groups.json') else {}
COL = {'buck': '#cf222e', 'ldo': '#fa4549', 'codec': '#8250df', 'adc': '#a475f9', 'mcu': '#0969da', 'in': '#1a7f37',
       'out': '#2da44e', 'io': '#bf8700', 'ctl': '#57606a', 'relay': '#d4a72c', 'fixed': '#8c959f'}
S, OX, OY = 9, 290, 600
P = lambda x, y: (OX + x * S, OY - y * S)
out = ["<svg xmlns='http://www.w3.org/2000/svg' width='900' height='1060'><rect width='100%' height='100%' fill='white'/>",
       "<text x='24' y='34' font-family='Helvetica' font-size='20' font-weight='bold'>The Harp - top-side placement, 2026-10-08</text>",
       "<text x='24' y='56' font-family='Helvetica' font-size='12' fill='#57606a'>Face coordinates, courtyards to scale. Red circles: through-hole pins of the underside jacks and DC jack. Dashed blue: OLED module outline.</text>"]
x, y = P(-28, 52); out.append(f"<rect x='{x}' y='{y}' width='{56*S}' height='{90*S}' rx='{2*S}' fill='#f6fff8' stroke='#1a7f37' stroke-width='2'/>")
x, y = P(-9, 56.5); out.append(f"<rect x='{x}' y='{y}' width='{18*S}' height='{4.5*S}' fill='#f6fff8' stroke='#1a7f37' stroke-width='2'/>")
x, y = P(-19, -13.75); out.append(f"<rect x='{x}' y='{y}' width='{38*S}' height='{12.5*S}' fill='none' stroke='#0969da' stroke-dasharray='6 4' stroke-width='1.5'/>")
for r, (fx, fy, a) in pos.items():
    g = groups.get(r, 'fixed')
    b = bbox(r, fx, fy, a)
    if L[r]['layer'] == 'B.Cu':
        for p, px, py in padpos(r, fx, fy, a):
            if p['kind'] == 'thru_hole':
                cx, cy = P(px, py); out.append(f"<circle cx='{cx:.1f}' cy='{cy:.1f}' r='{max(p['w'],p['h'])/2*S:.1f}' fill='#ffd8d3' stroke='#cf222e'/>")
        continue
    x0, y0 = P(b[0], b[3])
    out.append(f"<rect x='{x0:.1f}' y='{y0:.1f}' width='{(b[1]-b[0])*S:.1f}' height='{(b[3]-b[2])*S:.1f}' fill='{COL[g]}' fill-opacity='0.35' stroke='{COL[g]}'/>")
    if (b[1]-b[0]) * (b[3]-b[2]) > 6:
        cx, cy = P((b[0]+b[1])/2, (b[2]+b[3])/2)
        out.append(f"<text x='{cx:.1f}' y='{cy+3:.1f}' font-size='{8 if (b[1]-b[0])>3 else 6}' font-family='Helvetica' text-anchor='middle'>{r}</text>")
LEG = [('fixed', 'Face parts (pots, toggles, LEDs) and U201'), ('mcu', 'MCU periphery, flash, crystal'), ('codec', 'Codec, VCOM buffers'),
       ('adc', 'ADC driver (THS4522 L + R)'), ('in', 'Input buffers L + R'), ('out', 'Output stages'), ('relay', 'Relay bypass, SWD pads'),
       ('io', 'Jack ESD, LED drivers, FSW pads'), ('buck', 'Buck 3V3'), ('ldo', 'LDO 5V'), ('ctl', 'Pot RCs, OLED parts')]
for i, (k, t_) in enumerate(LEG):
    y = 120 + i * 24
    out.append(f"<rect x='640' y='{y-12}' width='16' height='16' fill='{COL[k]}' fill-opacity='0.35' stroke='{COL[k]}'/>")
    out.append(f"<text x='664' y='{y+1}' font-family='Helvetica' font-size='12'>{t_}</text>")
out.append('</svg>')
open(OUTP + '.svg', 'w').write('\n'.join(out))
C = os.environ.get('CHROME', 'chromium')
subprocess.run([C, '--headless', '--no-sandbox', '--disable-gpu', '--hide-scrollbars', '--force-device-scale-factor=2', '--window-size=900,1160',
                '--screenshot=' + OUTP + '.png', 'file://' + OUTP + '.svg'], stderr=subprocess.DEVNULL)
