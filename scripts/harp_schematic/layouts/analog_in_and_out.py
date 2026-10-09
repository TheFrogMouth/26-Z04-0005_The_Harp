"""Analog In and Out: OPA2365 input buffer (U701A), its spare half, and the two OPA1688 output difference amplifiers."""
from layouts.common import u, U, shunt, series


def opamp_text(X, Y):
    return dict(ref_pos=(u(X - 3), u(Y - 4.6), 'left'), val_pos=(u(X - 3), u(Y - 3.1), 'left'))


def layout(L):
    L.text(L.sheet.notes[0], u(8), u(6))
    # ================================================================ input buffer
    X, Y = 38, 31
    L.at('U701', u(X), u(Y), unit=1, **opamp_text(X, Y))
    L.gl('EFFECT_IN', (u(16), u(30)), 'left')
    L.w((u(16), u(30)), (u(22), u(30)))
    shunt(L, 'R701', u(19), u(30))
    series(L, 'C701', u(23.5), u(30))
    L.w(('C701', '2'), ('U701', '3'))                                  # IN_AC
    L.at('R702', u(28), u(31.5))
    L.w(('R702', '2'), (u(28), u(34)))
    L.gl('VCOM_A', (u(28), u(34)), 'down')
    # feedback: R703 (0R) from the output back to the inverting input, R704 / C707 gain option (DNP)
    L.w(('U701', '2'), (u(33), u(32)), (u(33), u(43)))                 # IN_FB
    L.w((u(33), u(41)), (u(37), u(41)))
    series(L, 'R703', u(38.5), u(41), flip=True)
    L.w(('R703', '1'), (u(44), u(41)), (u(44), u(31)))
    L.at('R704', u(33), u(44.5))
    L.w(('R704', '2'), (u(33), u(48)))                                 # IN_GAIN
    L.at('C707', u(33), u(49.5))
    L.w(('C707', '2'), (u(33), u(52)))
    L.gl('VCOM_A', (u(33), u(52)), 'down')
    # output to the ADC driver
    L.w(('U701', '1'), (u(46), u(31)))                                 # IN_BUF_OUT
    series(L, 'R705', u(47.5), u(31))
    L.w(('R705', '2'), (u(56), u(31)))                                 # EFFECT_IN_BUF
    shunt(L, 'C702', u(52), u(31))
    L.gl('EFFECT_IN_BUF', (u(56), u(31)), 'right')
    # right input (IN ring): 1M to ground, 100n film, 1M bias to VCOM_A, follower U701B, 49.9R / 220p
    X, Y = 38, 62
    L.at('U701', u(X), u(Y), unit=2, **opamp_text(X, Y))
    L.gl('IN_R', (u(16), u(61)), 'left')
    L.w((u(16), u(61)), (u(22), u(61)))
    shunt(L, 'R720', u(19), u(61))
    series(L, 'C708', u(23.5), u(61))
    L.w(('C708', '2'), ('U701', '5'))                                  # IN_AC_R
    L.at('R721', u(28), u(59.5), ang=180)
    L.w(('R721', '2'), (u(28), u(56)))
    L.gl('VCOM_A', (u(28), u(56)), 'up')
    L.w(('U701', '7'), (u(44), u(62)), (u(44), u(68)), (u(32), u(68)), (u(32), u(63)), ('U701', '6'))
    L.w((u(44), u(62)), (u(46), u(62)))                                # IN_BUF_OUT_R
    series(L, 'R722', u(47.5), u(62))
    L.w(('R722', '2'), (u(56), u(62)))                                 # EFFECT_IN_BUF_R
    shunt(L, 'C709', u(52), u(62))
    L.gl('EFFECT_IN_BUF_R', (u(56), u(62)), 'right')
    # supply
    L.at('U701', u(54), u(77), unit=3, ref_pos=(u(50), u(81.5), 'left'), val_pos=(u(50), u(83), 'left'))
    L.pwr('+5V', ('U701', '8', 3), 'up', length=U)
    L.gnd(('U701', '4', 3), length=U)
    L.pwr('+5V', (u(60), u(72)), 'up')
    L.w((u(60), u(72)), (u(60), u(74)))
    shunt(L, 'C703', u(60), u(74))
    # ================================================================ output stages
    for ch, Y, unit, pp, nn, oo, base, cap in (('L', 32, 1, '3', '2', '1', 706, 'C704'), ('R', 52, 2, '5', '6', '7', 714, 'C705')):
        X = 88
        L.at('U702', u(X), u(Y), unit=unit, **opamp_text(X, Y))
        yp, yn = u(Y - 1), u(Y + 1)
        L.gl('DAC_%s_P' % ch, (u(70), yp), 'left')
        L.w((u(70), yp), (u(72), yp))
        series(L, 'R%d' % base, u(73.5), yp)
        L.w(('R%d' % base, '2'), ('U702', pp))                         # OUT_P
        L.at('R%d' % (base + 1), u(80), u(Y - 2.5), ang=180)           # to VCOM_B, upward
        L.w(('R%d' % (base + 1), '2'), (u(80), u(Y - 6)))
        L.gl('VCOM_B', (u(80), u(Y - 6)), 'up')
        L.gl('DAC_%s_N' % ch, (u(70), yn), 'left')
        L.w((u(70), yn), (u(76), yn))
        series(L, 'R%d' % (base + 2), u(77.5), yn)
        L.w(('R%d' % (base + 2), '2'), ('U702', nn))                   # OUT_N
        L.w((u(80), yn), (u(80), u(Y + 8)), (u(85), u(Y + 8)))
        series(L, 'R%d' % (base + 3), u(86.5), u(Y + 8))
        L.w(('R%d' % (base + 3), '2'), (u(94), u(Y + 8)), (u(94), u(Y)))
        L.w(('U702', oo), (u(96), u(Y)))                               # OUT_AMP
        series(L, cap, u(97.5), u(Y))
        L.w((cap, '2'), (u(101), u(Y)))                                 # OUT_AC
        series(L, 'R%d' % (base + 4), u(102.5), u(Y))
        L.w(('R%d' % (base + 4), '2'), (u(111), u(Y)))                 # EFFECT_OUT_x
        shunt(L, 'R%d' % (base + 5), u(107), u(Y))
        L.gl('EFFECT_OUT_%s' % ch, (u(111), u(Y)), 'right')
    L.at('U702', u(120), u(66), unit=3, ref_pos=(u(116), u(70.5), 'left'), val_pos=(u(116), u(72), 'left'))
    L.pwr('+5V', ('U702', '8', 3), 'up', length=U)
    L.gnd(('U702', '4', 3), length=U)
    L.pwr('+5V', (u(126), u(61)), 'up')
    L.w((u(126), u(61)), (u(126), u(63)))
    shunt(L, 'C706', u(126), u(63))
