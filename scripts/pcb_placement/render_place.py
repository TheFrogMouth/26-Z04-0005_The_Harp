"""Draw the placement, top and bottom side by side (both seen from the top, face coordinates)."""
import os, sys, json, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'build'); os.makedirs(OUT, exist_ok=True)
sys.path.insert(0, HERE)
from place import bbox, L, padpos, SIDE, MODULE
pos = json.load(open(os.path.join(OUT, 'pos.json')))
groups = json.load(open(os.path.join(OUT, 'groups.json')))
OUTP = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.path.join(OUT, 'place')
COL = {'buck': '#cf222e', 'ldo': '#fa4549', 'codec': '#8250df', 'adc': '#a475f9', 'mcu': '#0969da', 'in': '#1a7f37',
       'out': '#2da44e', 'relay': '#d4a72c', 'leds': '#bf8700', 'exp': '#9a6700', 'pads': '#57606a', 'pots': '#6e7781', 'vcom': '#c297ff', 'fixed': '#8c959f'}
LEG = [('fixed', 'Face parts, jacks, U201'), ('mcu', 'MCU periphery, flash, OLED'), ('codec', 'Codec and its decoupling'), ('vcom', 'VCOM buffers, bulk caps'),
       ('adc', 'ADC driver (L + R)'), ('in', 'Input buffers, input ESD'), ('out', 'Output stages, output ESD'),
       ('relay', 'Relay bypass'), ('leds', 'LED and footswitch drivers'), ('exp', 'Expression buffer'),
       ('pads', 'SWD and footswitch pads'), ('pots', 'Pot RC filters'), ('buck', 'Buck 3V3'), ('ldo', 'LDO 5V')]
S = 8
def panel(ox, oy, side, title):
    P = lambda x, y: (ox + x * S, oy - y * S)
    o = [f"<text x='{ox}' y='{oy - 62 * S}' font-family='Helvetica' font-size='15' font-weight='bold' text-anchor='middle'>{title}</text>"]
    x, y = P(-28, 52); o.append(f"<rect x='{x}' y='{y}' width='{56*S}' height='{90*S}' rx='{2*S}' fill='#f6fff8' stroke='#1a7f37' stroke-width='2'/>")
    x, y = P(-9, 56.5); o.append(f"<rect x='{x}' y='{y}' width='{18*S}' height='{4.5*S}' fill='#f6fff8' stroke='#1a7f37' stroke-width='2'/>")
    if side == 'F':
        x, y = P(MODULE[0], MODULE[3]); o.append(f"<rect x='{x}' y='{y}' width='{(MODULE[1]-MODULE[0])*S}' height='{(MODULE[3]-MODULE[2])*S}' fill='none' stroke='#0969da' stroke-dasharray='6 4' stroke-width='1.5'/>")
    for r, v in pos.items():
        fx, fy, a, sd = v
        if sd != side:
            for p, px, py in padpos(r, fx, fy, a, sd):     # holes of the other side show through
                if p['kind'] in ('thru_hole', 'np_thru_hole'):
                    cx, cy = P(px, py); o.append(f"<circle cx='{cx:.1f}' cy='{cy:.1f}' r='{max(p['w'],p['h'])/2*S:.1f}' fill='#ffd8d3' stroke='#cf222e' stroke-width='0.8'/>")
            continue
        g = groups.get(r, 'fixed')
        b = bbox(r, fx, fy, a, sd)
        x0, y0 = P(b[0], b[3])
        o.append(f"<rect x='{x0:.1f}' y='{y0:.1f}' width='{(b[1]-b[0])*S:.1f}' height='{(b[3]-b[2])*S:.1f}' fill='{COL[g]}' fill-opacity='0.35' stroke='{COL[g]}'/>")
        if (b[1]-b[0]) * (b[3]-b[2]) > 6:
            cx, cy = P((b[0]+b[1])/2, (b[2]+b[3])/2)
            o.append(f"<text x='{cx:.1f}' y='{cy+3:.1f}' font-size='{7 if (b[1]-b[0])>3 else 5.5}' font-family='Helvetica' text-anchor='middle'>{r}</text>")
    return o
W, H = 1240, 1060
out = [f"<svg xmlns='http://www.w3.org/2000/svg' width='{W}' height='{H}'><rect width='100%' height='100%' fill='white'/>",
       "<text x='24' y='34' font-family='Helvetica' font-size='20' font-weight='bold'>The Harp - placement, top and bottom, 2026-10-09</text>",
       "<text x='24' y='56' font-family='Helvetica' font-size='12' fill='#57606a'>Both sides seen from the top (face coordinates). Red circles: through-holes from the other side. Dashed blue: OLED module.</text>"]
out += panel(260, 600, 'F', 'Top side')
out += panel(760, 600, 'B', 'Bottom side (seen through the board)')
for i, (k, t_) in enumerate(LEG):
    y = 120 + i * 22
    out.append(f"<rect x='1040' y='{y-12}' width='14' height='14' fill='{COL[k]}' fill-opacity='0.35' stroke='{COL[k]}'/>")
    out.append(f"<text x='1060' y='{y}' font-family='Helvetica' font-size='11'>{t_}</text>")
out.append('</svg>')
open(OUTP + '.svg', 'w').write('\n'.join(out))
C = os.environ.get('CHROME', 'chromium')
subprocess.run([C, '--headless', '--no-sandbox', '--disable-gpu', '--hide-scrollbars', '--force-device-scale-factor=2', f'--window-size={W},{H+100}',
                '--screenshot=' + OUTP + '.png', 'file://' + OUTP + '.svg'], stderr=subprocess.DEVNULL)
