"""Place and route the power section (top of the board, y < 70) by hand, in code.

Keeps the owner's 3V3 buck placement (U301, C305, C304, L301, C306, C307) and re-places the rest:
the DC input chain in one row at y = 56 (jack -> TVS -> FB301 -> D302 -> +9V) and the 5 V LDO chain
in a second row at y = 63, flowing back towards the +5V via (FB302 -> C308, C309 -> U302 -> C310,
C311 -> FB303 -> C312), the feedback divider beside the FB pin. Every track is at 0/45/90 degrees
and one of the Alchemist widths: 1.0 (input current), 0.762 (rails), 0.508 (GND stubs), 0.254
(signals). In2.Cu carries the three rails only; the buck's SW node to the BOOT cap crosses on B.Cu.

Tracks and vias of the power nets with both ends above y = 70 are replaced; the rail stalks that
cross y = 70 stay and are joined at their existing ends.
Usage: python3 power.py
"""
import os, sys, re, uuid
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, '..', 'pcb_placement'))
import kpcb, check
from write_pos import rewrite
from pcbread import footprints

Y_CUT = 70.0
W_IN, W_RAIL, W_GND, W_SIG = 1.0, 0.762, 0.508, 0.254
VIA = (0.6, 0.3)

# ref: (x, y, angle)  -- board coordinates, F.Cu
PLACE = {
    # DC input row, bus at y = 56
    'D301': (155.3, 57.2, 90),      # TVS hanging off the bus: DC_IN pad on the bus, GND pad below
    'FB301': (167.5, 56.0, 0),
    'C301': (165.938, 57.9, 180),   # DC_IN cap under FB301's input pad
    'C302': (169.062, 57.9, 0),     # DC_F cap under FB301's output pad
    'D302': (172.0375, 56.0, 180),  # +9V pad at x = 173.4375, over FB302's +9V pad
    # LDO row, bus at y = 63, flowing right to left
    'FB302': (172.65, 63.0, 180),
    'C308': (169.25, 61.525, 90),
    'C309': (166.8, 62.225, 90),
    'U302': (162.5, 62.05, 180),    # input pins face right, output faces left
    'C310': (158.6, 62.225, 90),
    'C311': (157.0, 62.225, 90),
    'FB303': (154.75, 63.0, 180),
    'C312': (152.4, 62.225, 90),
    # 3V3 buck: the feedback divider beside the FB pin
    'R302': (141.6, 58.75, 90),
    'R301': (141.6, 61.75, 90),
    'R303': (143.9, 58.75, -90),
    'C307': (126.75, 57.0, 90),     # was 57.025
}

POWER_NETS = {'+3V3', '+5V', '+9V', 'GND', 'Net-(U301-SW)', 'Net-(U301-FB)', 'Net-(U301-BOOT)',
              'Net-(R301-Pad2)', 'Net-(D301-A2)', 'Net-(D302-A)', 'Net-(U302-EN)', 'Net-(U302-OUT)'}


def uid():
    return str(uuid.uuid4())


def fmt(v):
    return ('%.4f' % v).rstrip('0').rstrip('.')


def seg(net, layer, w, *pts):
    out = []
    pts = [list(p) for p in pts]
    for a, b in zip(pts, pts[1:]):
        # the footprint positions are written to 0.001 mm, so pads meant to line up can be 0.0005 off: snap
        if abs(b[0] - a[0]) < 2e-3: b[0] = a[0]
        if abs(b[1] - a[1]) < 2e-3: b[1] = a[1]
        (x1, y1), (x2, y2) = a, b
        dx, dy = abs(x2 - x1), abs(y2 - y1)
        assert dx < 1e-6 or dy < 1e-6 or abs(dx - dy) < 1e-3, ('not 0/45/90', net, (x1, y1), (x2, y2))
        out.append('\t(segment\n\t\t(start %s %s)\n\t\t(end %s %s)\n\t\t(width %s)\n\t\t(layer "%s")\n'
                   '\t\t(net "%s")\n\t\t(uuid "%s")\n\t)' % (fmt(x1), fmt(y1), fmt(x2), fmt(y2), fmt(w), layer, net, uid()))
    return out


def via(net, x, y):
    return ['\t(via\n\t\t(at %s %s)\n\t\t(size %s)\n\t\t(drill %s)\n\t\t(layers "F.Cu" "B.Cu")\n'
            '\t\t(net "%s")\n\t\t(uuid "%s")\n\t)' % (fmt(x), fmt(y), fmt(VIA[0]), fmt(VIA[1]), net, uid())]


def place(t):
    n = 0
    for f in sorted(footprints(t), key=lambda f: -f['s']):
        if f['ref'] in PLACE:
            x, y, a = PLACE[f['ref']]
            nb = rewrite(f['b'], x, y, a, False)
            t = t[:f['s']] + nb + t[f['e']:]
            n += 1
    assert n == len(PLACE), n
    return t


def strip(t):
    """Remove power-net tracks and vias lying above y = 70 (both ends)."""
    def keep_seg(m):
        b = m.group(0)
        net = re.search(r'\(net "([^"]*)"\)', b).group(1)
        ys = [float(v) for v in re.findall(r'\((?:start|end) [-\d.]+ ([-\d.]+)\)', b)]
        return not (net in POWER_NETS and max(ys) < Y_CUT)
    def keep_via(m):
        b = m.group(0)
        net = re.search(r'\(net "([^"]*)"\)', b).group(1)
        y = float(re.search(r'\(at [-\d.]+ ([-\d.]+)\)', b).group(1))
        return not (net in POWER_NETS and y < Y_CUT)
    n0 = t.count('\n\t(segment') + t.count('\n\t(via')
    t = re.sub(r'\n\t\(segment\n.*?\n\t\)', lambda m: m.group(0) if keep_seg(m) else '', t, flags=re.S)
    t = re.sub(r'\n\t\(via\n.*?\n\t\)', lambda m: m.group(0) if keep_via(m) else '', t, flags=re.S)
    print('removed', n0 - t.count('\n\t(segment') - t.count('\n\t(via'), 'tracks and vias')
    return t


def routes(P):
    """P[(ref, pad)] -> (x, y). Returns the list of S-expression blocks."""
    o = []
    F, B, I = 'F.Cu', 'B.Cu', 'In2.Cu'
    DCIN, DCF, V9, V3, V5 = 'Net-(D301-A2)', 'Net-(D302-A)', '+9V', '+3V3', '+5V'
    SW, FB, BOOT, FBT = 'Net-(U301-SW)', 'Net-(U301-FB)', 'Net-(U301-BOOT)', 'Net-(R301-Pad2)'
    LIN, LOUT, G = 'Net-(U302-EN)', 'Net-(U302-OUT)', 'GND'

    def gnd(ref, pad, vx, vy, *mid):
        """GND pad to its own via, straight or with a 45 degree jog."""
        o.extend(seg(G, F, W_GND, P[ref, pad], *mid, (vx, vy)))
        o.extend(via(G, vx, vy))

    # ---------------- DC input row (y = 56)
    j2 = P['J401', '2']                                   # (148.5, 53.8)
    o += seg(DCIN, F, W_IN, j2, (j2[0] + 2.2, j2[1] + 2.2), (P['FB301', '1'][0], 56.0))
    o += seg(DCIN, F, W_IN, (P['C301', '1'][0], 56.0), P['C301', '1'])   # stub down to the DC_IN cap
    o += seg(DCF, F, W_IN, P['FB301', '2'], P['D302', '2'])
    o += seg(DCF, F, W_IN, (P['C302', '1'][0], 56.0), P['C302', '1'])
    gnd('D301', '1', 156.5, 59.2)                        # TVS return
    gnd('C301', '2', 164.113, 58.95)
    gnd('C302', '2', 170.887, 58.95)
    # +9V: D302 cathode straight down to FB302, via to In2 on the way
    x9 = P['D302', '1'][0]
    o += seg(V9, F, W_RAIL, P['D302', '1'], P['FB302', '1'])
    o += via(V9, x9, 57.5)

    # ---------------- LDO row (y = 63), right to left
    o += seg(LIN, F, W_RAIL, P['FB302', '2'], P['U302', '1'])             # through C308 and C309 pads
    o += seg(LIN, F, W_SIG, P['U302', '3'], (165.8, P['U302', '3'][1]), (165.8, 63.0))   # EN tied to IN
    gnd('C308', '2', 170.9, 59.9, (170.75, P['C308', '2'][1]))      # clear of C302's DC_F pad
    gnd('C309', '2', 166.8, 60.1)
    gnd('U302', '2', 164.95, P['U302', '2'][1])
    o += seg(LOUT, F, W_RAIL, P['U302', '5'], P['FB303', '1'])            # through C310 and C311 pads
    gnd('C310', '2', 158.6, 60.1)
    gnd('C311', '2', 157.0, 60.1)
    o += seg(V5, F, W_RAIL, P['FB303', '2'], P['C312', '1'], (151.1, 63.0))
    gnd('C312', '2', 152.4, 60.1)
    o += via(V5, 151.1, 63.0)
    o += seg(V5, I, W_RAIL, (151.1, 63.0), (154.511, 63.0), (158.258, 66.747))        # joins the +5V stalk, clear of RV102's mounting hole

    # ---------------- 3V3 buck (owner's placement)
    p1, p2, p3, p4, p6 = (P['U301', n] for n in '12346')
    o += seg(V9, F, W_RAIL, (137.0, P['C303', '1'][1]), (137.0, p3[1]))               # C303 -> C304 -> VIN
    o += via(V9, 137.0, 59.4)
    o += seg(SW, F, W_RAIL, p2, (135.0, p2[1]), P['L301', '1'])
    o += via(SW, 135.25, p2[1])
    o += seg(SW, B, W_GND, (135.25, p2[1]), (136.025, 56.525), (142.2, 56.525))
    o += via(SW, 142.2, 56.525)
    o += seg(SW, F, W_GND, (142.2, 56.525), P['C305', '2'])
    o += seg(BOOT, F, W_SIG, p6, (140.825, p6[1]), P['C305', '1'])
    o += seg(FB, F, W_SIG, p4, (p4[0], 57.2), (p4[0] + 0.725, 57.925), P['R303', '1'])   # through R302 pad 2
    o += seg(FBT, F, W_SIG, P['R302', '1'], P['R301', '2'])
    o += seg(V3, F, W_SIG, P['R301', '1'], (132.675, P['R301', '1'][1]), (128.575, 58.475))  # sense
    o += seg(V3, F, W_RAIL, P['L301', '2'], (128.575, 58.475), P['C306', '1'])          # through C307 pad 1
    o += seg(V3, F, W_RAIL, P['C306', '1'], (P['C306', '1'][0], 60.75))
    o += seg(V3, F, W_RAIL, P['C307', '1'], (P['C307', '1'][0], 60.75))
    o += via(V3, P['C306', '1'][0], 60.75)
    o += via(V3, P['C307', '1'][0], 60.75)
    gnd('U301', '1', p1[0], 53.95)
    gnd('C304', '2', P['C304', '2'][0], 59.3)
    gnd('C303', '2', 140.2, 59.3, (P['C303', '2'][0], 59.525))
    gnd('R303', '2', P['R303', '2'][0], 60.75)
    gnd('C306', '2', 121.9, P['C306', '2'][1])
    gnd('C307', '2', 125.1, P['C307', '2'][1])

    # ---------------- In2 rails
    o += seg(V9, I, W_RAIL, (x9, 57.5), (138.9, 57.5), (137.0, 59.4), (122.9, 59.4), (121.472, 60.828))
    o += seg(V9, I, W_RAIL, (137.0, 59.4), (138.1, 60.5), (139.201, 60.5))             # the +9V stalk
    o += seg(V3, I, W_RAIL, (P['C306', '1'][0], 60.75), (132.0, 60.75), (136.875, 65.625), (136.875, 68.625))   # the +3V3 stalk, clear of RV101's mounting hole
    return o


def main():
    t = open(kpcb.PCB).read()
    t = place(t)
    t = strip(t)
    open(kpcb.PCB, 'w').write(t)
    text, tree, fps, pads = kpcb.load()
    P = {(p['ref'], p['num']): (round(p['x'], 4), round(p['y'], 4)) for p in pads}
    body = routes(P)
    k = t.find('\n\t(gr_')
    t = t[:k] + '\n' + '\n'.join(body) + t[k:]
    open(kpcb.PCB, 'w').write(t)
    print('added', sum(b.startswith('\t(segment') for b in body), 'tracks and', sum(b.startswith('\t(via') for b in body), 'vias')


if __name__ == '__main__':
    main()
