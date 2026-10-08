"""Face cut-out and OLED-to-PCB drawings for The Harp (docs/images/oled-*.svg).

Face coordinates throughout: X right, Y up, origin at the enclosure centre =
PCB (148.5, 105), as docs/pcb-plan.md. Hole schedule from the shared 125B face
(The Relic / Alchemist sizes in 26-F01-0001_Frogmouth/scripts/fusion_face_cuts).
Footprint courtyards from kicad/the_harp/The Harp.kicad_pcb (2026-10-08).
Run: python3 scripts/oled_drawings/oled_drawings.py
"""
import os

OUT = os.path.join(os.path.dirname(__file__), '..', '..', 'docs', 'images')

# ---- data (mm, face coordinates) -------------------------------------------
FACE_W, FACE_H, FACE_R = 64.7, 119.8, 5.5          # Tayda 125B face
CAV_W, CAV_H = 60.3, 115.4                          # cavity
FACE_T = 2.2                                        # wall / face thickness (Tayda)
BOARD_GAP = 11.0                                    # face underside to board top, PROVISIONAL (10-12 mm)
BOARD_T = 1.6
OLED_Y = -20.0                                      # active-area centre
ACTIVE = (22.384, 5.584)
WINDOW = (24.4, 7.6)                                # viewable area, cut in the face
MODULE = (38.0, 12.5)                               # module board envelope (Waveshare 36 x 12.5, generic up to 38 x 12)
GASKET, GLASS, MOD_PCB, MOD_PARTS = 0.5, 1.45, 1.0, 1.2
HOLES = [  # (label, x, y, diameter)
    ('RV101 Mix', -20, 38, 7.0), ('RV102 Sustain', 0, 38, 7.0), ('RV103 Strings', 20, 38, 7.0),
    ('SW101 Tuning', -20, 13, 6.5), ('RV105 Jawari', 0, 13, 7.0), ('SW103 Brightness', 20, 13, 6.5),
    ('SW102 Retune', 0, -5, 6.5),
    ('D113 Effect', -20, -35, 6.0), ('D114 Hold', 20, -35, 6.0),
    ('Bypass FSW', -20, -49, 12.0), ('Hold FSW', 20, -49, 12.0),
]
# courtyards on the board (face X0, X1, Y0, Y1) and part height above the board
SW102_CY = (-7.35, 7.35, -12.45, 2.09)
K401_CY = (-9.25, 0.05, -37.25, -26.75); K401_H = 5.2       # moved 2026-10-08, PCB (143.9, 137)
D113_CY = (-22.42, -17.58, -37.21, -32.79)
D114_CY = (17.58, 22.42, -37.21, -32.79)
JACK_LO = [(-30.0, -6.5, -31.6, -13.4), (6.5, 30.0, -31.6, -13.4)]     # lower jack bodies, underside
J408 = (-24.0, -20.0)                                                   # proposed, provisional

INK, MUTED, ACCENT, WARN, BOARD, FILL = '#1f2328', '#6e7781', '#0969da', '#cf222e', '#2da44e', '#f6f8fa'
FONT = "font-family='Helvetica, Arial, sans-serif'"


class Svg:
    def __init__(self, w, h):
        self.w, self.h, self.items = w, h, []

    def add(self, s):
        self.items.append(s)

    def text(self, x, y, s, size=11, color=INK, anchor='start', weight='normal'):
        s = s.replace('&', '&amp;').replace('<', '&lt;')
        self.add(f"<text x='{x:.1f}' y='{y:.1f}' {FONT} font-size='{size}' fill='{color}' text-anchor='{anchor}' font-weight='{weight}'>{s}</text>")

    def line(self, x0, y0, x1, y1, color=INK, w=1, dash=None):
        d = f" stroke-dasharray='{dash}'" if dash else ''
        self.add(f"<line x1='{x0:.1f}' y1='{y0:.1f}' x2='{x1:.1f}' y2='{y1:.1f}' stroke='{color}' stroke-width='{w}'{d}/>")

    def rect(self, x, y, w, h, stroke=INK, fill='none', sw=1, dash=None, r=0, op=1):
        d = f" stroke-dasharray='{dash}'" if dash else ''
        self.add(f"<rect x='{x:.1f}' y='{y:.1f}' width='{w:.1f}' height='{h:.1f}' rx='{r:.1f}' stroke='{stroke}' fill='{fill}' fill-opacity='{op}' stroke-width='{sw}'{d}/>")

    def circle(self, x, y, r, stroke=INK, fill='none', sw=1):
        self.add(f"<circle cx='{x:.1f}' cy='{y:.1f}' r='{r:.1f}' stroke='{stroke}' fill='{fill}' stroke-width='{sw}'/>")

    def dim_h(self, x0, x1, y, label, color=ACCENT):
        self.line(x0, y, x1, y, color)
        for x in (x0, x1):
            self.line(x, y - 4, x, y + 4, color)
        self.text((x0 + x1) / 2, y - 5, label, 10, color, 'middle')

    def dim_v(self, x, y0, y1, label, color=ACCENT, side='right'):
        self.line(x, y0, x, y1, color)
        for y in (y0, y1):
            self.line(x - 4, y, x + 4, y, color)
        self.text(x + (6 if side == 'right' else -6), (y0 + y1) / 2 + 4, label, 10, color, 'start' if side == 'right' else 'end')

    def save(self, name):
        body = '\n'.join(self.items)
        svg = (f"<svg xmlns='http://www.w3.org/2000/svg' width='{self.w}' height='{self.h}' viewBox='0 0 {self.w} {self.h}'>\n"
               f"<rect width='100%' height='100%' fill='white'/>\n{body}\n</svg>\n")
        with open(os.path.join(OUT, name), 'w') as f:
            f.write(svg)


def face_cutout():
    S, OX, OY = 5.0, 230, 380          # px per mm, face origin in px
    P = lambda x, y: (OX + x * S, OY - y * S)
    s = Svg(760, 760)
    s.text(24, 32, 'The Harp - face cut-out (Tayda 125B, viewed from the front)', 17, INK, weight='bold')
    s.text(24, 52, 'Face coordinates in mm, origin at the enclosure centre. OLED window is new; every other hole is the shared 125B schedule.', 11, MUTED)
    x, y = P(-FACE_W / 2, FACE_H / 2)
    s.rect(x, y, FACE_W * S, FACE_H * S, INK, FILL, 1.5, r=FACE_R * S)
    x, y = P(-CAV_W / 2, CAV_H / 2)
    s.rect(x, y, CAV_W * S, CAV_H * S, MUTED, sw=0.8, dash='4 3', r=3 * S)
    s.line(*P(-FACE_W / 2 - 3, 0), *P(FACE_W / 2 + 3, 0), MUTED, 0.6, '8 3 2 3')
    s.line(*P(0, FACE_H / 2 + 3), *P(0, -FACE_H / 2 - 3), MUTED, 0.6, '8 3 2 3')
    for label, hx, hy, d in HOLES:
        cx, cy = P(hx, hy)
        s.circle(cx, cy, d / 2 * S, INK, 'white', 1.2)
        s.line(cx - 3, cy, cx + 3, cy, MUTED, 0.6); s.line(cx, cy - 3, cx, cy + 3, MUTED, 0.6)
        if hy < -30:                      # heel: short label beside the hole, towards the centre
            side = 1 if hx < 0 else -1
            tx, anc = cx + side * (d / 2 * S + 5), 'start' if side > 0 else 'end'
            s.text(tx, cy - 1, label.split()[0], 9, INK, anc)
            s.text(tx, cy + 10, f'Ø{d:g}', 9, MUTED, anc)
        else:
            s.text(cx, cy + d / 2 * S + 12, f'{label}', 9, INK, 'middle')
            s.text(cx, cy + d / 2 * S + 23, f'Ø{d:g} at ({hx:g}, {hy:g})', 9, MUTED, 'middle')
    # window
    wx, wy = P(-WINDOW[0] / 2, OLED_Y + WINDOW[1] / 2)
    s.rect(wx, wy, WINDOW[0] * S, WINDOW[1] * S, ACCENT, '#ddf4ff', 1.8, r=0.5 * S)
    ax, ay = P(-ACTIVE[0] / 2, OLED_Y + ACTIVE[1] / 2)
    s.rect(ax, ay, ACTIVE[0] * S, ACTIVE[1] * S, ACCENT, sw=0.6, dash='3 2')
    s.text(OX, OY - OLED_Y * S + 4, 'OLED window', 10, ACCENT, 'middle', 'bold')
    s.dim_h(wx, wx + WINDOW[0] * S, wy + WINDOW[1] * S + 16, f'{WINDOW[0]} mm')
    s.dim_v(wx + WINDOW[0] * S + 10, wy, wy + WINDOW[1] * S, f'{WINDOW[1]} mm')
    # callout
    tx = OX + FACE_W / 2 * S + 30
    s.text(tx, 120, 'OLED window (new)', 13, ACCENT, weight='bold')
    for i, t in enumerate([
        f'Rectangle {WINDOW[0]} x {WINDOW[1]} mm, R0.5 corners',
        f'Centre (0, {OLED_Y:g}), Tayda rectangular cut',
        f'Active area {ACTIVE[0]} x {ACTIVE[1]} mm (dashed)',
        '1 mm border round the active area',
        '',
        'Clearances on the face:',
        f'  to Retune toggle hole  {(-5 - 3.25) - (OLED_Y + WINDOW[1] / 2):.1f} mm',
        f'  to LED holes  {(OLED_Y - WINDOW[1] / 2) - (-35 + 3.0):.1f} mm',
        f'  to cavity wall  {CAV_W / 2 - WINDOW[0] / 2:.1f} mm each side',
        '',
        'Hole sizes: pots Ø7.0 (RD901F M7),',
        'toggles Ø6.5, LED bezels Ø6.0,',
        'footswitches Ø12.0, as The Relic.',
        'Heel: D113 (-20, -35), D114 (20, -35),',
        'Bypass FSW (-20, -49), Hold FSW (20, -49).',
        '',
        'Face 64.7 x 119.8 R5.5 (solid);',
        'cavity 60.3 x 115.4 (dashed).',
        'Nominal Tayda figures, not measured.',
    ]):
        s.text(tx, 142 + i * 16, t, 11, INK if i < 5 else MUTED)
    s.save('oled-face-cutout.svg')


def pcb_relation():
    s = Svg(1420, 800)
    s.text(24, 32, 'The Harp - OLED module against the PCB', 17, INK, weight='bold')
    s.text(24, 52, 'Left: top view in face coordinates (looking through the face). Right: section on X = 0, seen from the left wall. Millimetres.', 11, MUTED)
    # ------------------------------------------------ top view
    S, OX, OY = 5.0, 220, 410
    P = lambda x, y: (OX + x * S, OY - y * S)
    def box(cy, stroke, fill, dash=None, op=0.35, sw=1):
        x0, x1, y0, y1 = cy
        px, py = P(x0, y1)
        s.rect(px, py, (x1 - x0) * S, (y1 - y0) * S, stroke, fill, sw, dash, op=op)
    px, py = P(-CAV_W / 2, CAV_H / 2)
    s.rect(px, py, CAV_W * S, CAV_H * S, MUTED, sw=0.8, dash='4 3', r=3 * S)
    s.text(OX + CAV_W / 2 * S - 4, OY - CAV_H / 2 * S + 14, 'cavity', 9, MUTED, 'end')
    px, py = P(-28, 52)
    s.rect(px, py, 56 * S, 90 * S, BOARD, '#dafbe1', 1.5, r=2 * S, op=0.5)
    px, py = P(-9, 56.5)
    s.rect(px, py, 18 * S, 4.5 * S, BOARD, '#dafbe1', 1.5, op=0.5)
    s.text(OX - 28 * S + 6, OY - 52 * S + 16, 'PCB 56 x 90, top side', 10, BOARD, weight='bold')
    for j in JACK_LO:
        box(j, WARN, 'none', '3 3', sw=1)
    s.text(*P(-29.3, -30.6), 'jack body, underside', 8, WARN)
    s.text(*P(7.0, -30.6), 'jack body, underside', 8, WARN)
    box(SW102_CY, INK, '#eaeef2', op=0.9)
    s.text(*P(0, -2.5), 'SW102 Retune', 9, INK, 'middle')
    s.text(*P(0, -5.5), 'courtyard to Y -12.45', 8, MUTED, 'middle')
    box(K401_CY, INK, '#eaeef2', op=0.9)
    s.text(*P(-4.6, -31.4), 'K401 relay', 9, INK, 'middle')
    s.text(*P(-4.6, -33.8), '5.2 mm tall', 8, MUTED, 'middle')
    for cy, lb in ((D113_CY, 'D113'), (D114_CY, 'D114')):
        box(cy, INK, '#eaeef2', op=0.9)
        s.text(*P((cy[0] + cy[1]) / 2, cy[2] - 3.2), lb, 9, INK, 'middle')
    mx0, mx1, my0, my1 = -MODULE[0] / 2, MODULE[0] / 2, OLED_Y - MODULE[1] / 2, OLED_Y + MODULE[1] / 2
    box((mx0, mx1, my0, my1), ACCENT, '#ddf4ff', op=0.55, sw=1.8)
    box((-WINDOW[0] / 2, WINDOW[0] / 2, OLED_Y - WINDOW[1] / 2, OLED_Y + WINDOW[1] / 2), ACCENT, 'white', op=0.9, sw=1)
    s.text(*P(0, OLED_Y - 1), 'window / active area', 9, ACCENT, 'middle', 'bold')
    s.text(*P(mx1 - 0.6, my1 - 2.4), 'OLED module', 9, ACCENT, 'end')
    for k in range(4):
        s.circle(*P(mx0 + 1.3, OLED_Y + 3.81 - k * 2.54), 0.5 * S, ACCENT, 'white')
    s.line(*P(mx0 + 0.8, OLED_Y), *P(J408[0] + 2.5, J408[1]), ACCENT, 2.2)
    jx, jy = P(J408[0] - 2.5, J408[1] + 3)
    s.rect(jx, jy, 5 * S, 6 * S, INK, '#fff8c5', 1.2, op=1)
    s.text(*P(J408[0] - 2.5, J408[1] + 7.9), 'J408', 9, INK, 'start', 'bold')
    # vertical dims on the right
    s.dim_v(P(mx1, 0)[0] + 40, P(0, my1)[1], P(0, my0)[1], f'{MODULE[1]}')
    s.line(P(SW102_CY[1], 0)[0], P(0, SW102_CY[2])[1], P(mx1, 0)[0] + 24, P(0, SW102_CY[2])[1], WARN, 0.6, '2 2')
    s.dim_v(P(mx1, 0)[0] + 20, P(0, SW102_CY[2])[1], P(0, my1)[1], '', WARN)
    s.text(P(mx1, 0)[0] + 26, P(0, my1)[1] - 2, f'{SW102_CY[2] - my1:.1f} to SW102', 9, WARN)
    notes = [f'Module {MODULE[0]:g} x {MODULE[1]} envelope (36-38 x 12-12.5), Y {my1:.2f} to {my0:.2f}; window centre (0, {OLED_Y:g}).',
             'Pads on the left short end; J408 at (-24, -20) on the top side. Both provisional until placement.',
             'K401 moved to PCB (143.9, 137) on 2026-10-08: courtyard Y -26.75 to -37.25, 0.5 mm clear of the module in plan.']
    for k, t in enumerate(notes):
        s.text(OX - CAV_W / 2 * S, OY + CAV_H / 2 * S + 22 + 15 * k, t, 9.5, MUTED)
    # ------------------------------------------------ section on X = 0
    S2, SX, SY = 10.0, 720, 210          # px/mm; SX = face Y 0; SY = face underside
    Q = lambda fy, z: (SX - fy * S2, SY + z * S2)   # z = depth below the face underside; +Y to the left
    def slab(ya, yb, z0, z1, stroke, fill, op=1, sw=1.2):
        xa, za = Q(ya, z0); xb, zb = Q(yb, z1)
        s.rect(min(xa, xb), min(za, zb), abs(xb - xa), abs(zb - za), stroke, fill, sw, op=op)
    YL, YR = 4, -40
    w0, w1 = OLED_Y + WINDOW[1] / 2, OLED_Y - WINDOW[1] / 2
    slab(YL, w0, -FACE_T, 0, INK, '#d0d7de')
    slab(w1, YR, -FACE_T, 0, INK, '#d0d7de')
    s.text(*Q(YL - 0.3, -FACE_T - 1.0), f'face {FACE_T}', 10, INK)
    s.text(*Q(OLED_Y, -FACE_T - 1.0), 'window', 10, ACCENT, 'middle', 'bold')
    for fy in (0, -10, -20, -30):
        s.line(*Q(fy, -FACE_T - 4.2), *Q(fy, -FACE_T - 3.4), MUTED)
        s.text(*Q(fy, -FACE_T - 4.8), f'Y {fy:g}', 9, MUTED, 'middle')
    ya, yb = OLED_Y + MODULE[1] / 2, OLED_Y - MODULE[1] / 2
    layers = [(GASKET, 'foam gasket / VHB 0.5', '#fff8c5'), (GLASS, 'OLED glass 1.45', '#ddf4ff'),
              (MOD_PCB, 'module PCB 1.0', '#dafbe1'), (MOD_PARTS, 'module parts ~1.2', '#eaeef2')]
    z = 0
    for k, (th, lab, fill) in enumerate(layers):
        if th == GASKET:
            slab(ya + 0.5, w0 + 0.3, z, z + th, INK, fill); slab(w1 - 0.3, yb - 0.5, z, z + th, INK, fill)
        elif th == GLASS:
            slab(OLED_Y + 5.75, OLED_Y - 5.75, z, z + th, ACCENT, fill)
        elif th == MOD_PARTS:
            slab(OLED_Y + 4, OLED_Y - 4, z, z + th, INK, fill)
        else:
            slab(ya, yb, z, z + th, BOARD, fill)
        lx, ly = Q(-50, k * 1.6)
        s.text(lx + 8, ly + 4, lab, 9.5, INK)
        s.add(f"<polyline points='{Q(yb + 0.3, z + th / 2)[0]:.1f},{Q(0, z + th / 2)[1]:.1f} {lx - 30:.1f},{ly:.1f} {lx + 4:.1f},{ly:.1f}' stroke='{MUTED}' stroke-width='0.6' fill='none'/>")
        z += th
    hang = z
    slab(YL, YR, BOARD_GAP, BOARD_GAP + BOARD_T, BOARD, '#dafbe1')
    s.text(*Q(YL - 0.3, BOARD_GAP + BOARD_T + 1.6), 'PCB 1.6', 10, BOARD, weight='bold')
    slab(SW102_CY[3], SW102_CY[2], 0, BOARD_GAP, INK, '#eaeef2', 0.9)
    s.text(*Q((SW102_CY[2] + SW102_CY[3]) / 2, 5.2), 'SW102 body', 9, INK, 'middle')
    slab(K401_CY[3], K401_CY[2], BOARD_GAP - K401_H, BOARD_GAP, INK, '#eaeef2', 0.9)
    s.text(*Q(-32, BOARD_GAP - 2.4), 'K401 5.2', 9, INK, 'middle')
    xa, za = Q(-13.4, BOARD_GAP + BOARD_T); xb, zb = Q(-31.6, BOARD_GAP + BOARD_T + 11)
    s.rect(xa, za, xb - xa, zb - za, WARN, 'none', 1, '3 3')
    s.text(*Q(-22.5, BOARD_GAP + BOARD_T + 5.5), 'lower jacks, underside', 9, WARN, 'middle')
    s.text(*Q(-22.5, BOARD_GAP + BOARD_T + 7.0), '(|X| > 6.5, behind this plane)', 8, WARN, 'middle')
    # lead and J408, drawn in this plane for clarity
    a = Q(yb + 0.6, GASKET + GLASS + 0.5); b = Q(-19.0, BOARD_GAP - 1.2)
    s.add(f"<path d='M {a[0]:.1f} {a[1]:.1f} C {a[0] - 10:.1f} {a[1] + 25:.1f} {b[0] + 10:.1f} {b[1] - 25:.1f} {b[0]:.1f} {b[1]:.1f}' stroke='{ACCENT}' stroke-width='2' fill='none'/>")
    slab(-17.5, -20.5, BOARD_GAP - 1.5, BOARD_GAP, INK, '#fff8c5')
    s.text(*Q(-19, BOARD_GAP + BOARD_T + 1.6), 'J408 + lead (really at X -24)', 9, INK, 'middle')
    # dims at the right end, beyond the relay
    dx = Q(-37.5, 0)[0]
    s.dim_v(dx, Q(0, 0)[1], Q(0, hang)[1], f'{hang:.2f} module hang', ACCENT)
    s.dim_v(dx, Q(0, hang)[1], Q(0, BOARD_GAP)[1], f'{BOARD_GAP - hang:.2f} free', ACCENT)
    s.dim_v(Q(YL + 1.5, 0)[0], Q(0, 0)[1], Q(0, BOARD_GAP)[1], f'{BOARD_GAP:g} face to PCB', MUTED, 'left')
    s.text(Q(YL + 1.5, 0)[0] - 6, Q(0, BOARD_GAP / 2)[1] + 18, '(10-12, provisional)', 9, MUTED, 'end')
    ty = Q(0, BOARD_GAP + BOARD_T + 15)[1]
    for k, (t, c) in enumerate([
        ('K401 moved 2.15 mm towards the heel and 0.5 mm right (2026-10-08): it no longer sits under the module,', INK),
        (f'which ends at Y {OLED_Y - MODULE[1] / 2:g}. Nothing else under the module is taller than {BOARD_GAP - hang:.2f} mm.', INK),
        ('Layer thicknesses are typical module figures; measure the bought module and the casting before cutting.', MUTED)]):
        s.text(Q(YL, 0)[0], ty + 16 * k, t, 10, c)
    s.save('oled-pcb-relation.svg')


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    face_cutout()
    pcb_relation()
    print('wrote', os.path.abspath(OUT))
