"""Jacks and Bypass: the four jacks, the G6K relay true bypass and its driver, the effect and hold LEDs,
the two footswitch pads and the expression input buffer."""
from layouts.common import u, U, shunt, series


def jack(L, ref, X, Y, ring_gnd=False):
    """Jack at (X, Y) with pins to the right: sleeve to GND straight down, tip led down to a lane at Y+8u."""
    L.at(ref, u(X), u(Y), ref_pos=(u(X - 6), u(Y - 3), 'left'), val_pos=(u(X - 6), u(Y + 4.5), 'left'))
    L.w((ref, 'S'), (u(X + 6), u(Y - 2)), (u(X + 6), u(Y + 3)))
    L.gnd((u(X + 6), u(Y + 3)))
    if ring_gnd:
        L.w((ref, 'R'), (u(X + 6), u(Y)))
    L.w((ref, 'T'), (u(X + 4), u(Y + 2)), (u(X + 4), u(Y + 8)))
    for p in ('SN', 'RN', 'TN'):
        L.nc(ref, p)
    return (u(X + 4), u(Y + 8))


def layout(L):
    L.text(L.sheet.notes[0], u(8), u(6))
    # ================================================================ IN jack, relay, OUT L
    t = jack(L, 'J402', 14, 24, ring_gnd=True)                     # IN: tip lane at y = 32u
    L.w(t, (u(58), u(32)), (u(58), u(56)), (u(43), u(56)))
    shunt(L, 'D403', u(22), u(32), top='2', ang=90)
    L.at('K401', u(44), u(44), mirror='x', ref_pos=(u(51), u(42.5), 'left'), val_pos=(u(51), u(44), 'left'))
    L.w(('K401', '2'), (u(43), u(56)))                               # IN to both relay commons
    L.w(('K401', '5'), (u(49), u(56)))
    L.gl('EFFECT_OUT_L', ('K401', '4'), 'down', length=2 * U)
    L.gnd(('K401', '7'), length=U)
    L.gl('EFFECT_IN', ('K401', '6'), 'up', length=3 * U)
    t = jack(L, 'J403', 14, 44)                                     # OUT L: tip lane at y = 52u
    L.w(t, (u(27), u(52)), (u(27), u(36)), (u(44), u(36)), ('K401', '3'))
    shunt(L, 'D404', u(24), u(52), top='2', ang=90)
    # relay coil: +9V through R405, flyback D402, Q401 low side driven by RELAY_DRV
    L.w(('K401', '1'), (u(40), u(49)), (u(32), u(49)))              # RELAY_COIL lane
    L.at('R405', u(36), u(46.5))
    L.w(('R405', '2'), (u(36), u(49)))
    L.pwr('+9V', ('R405', '1'), 'up', length=U)
    L.at('D402', u(32), u(47.5), ang=90, ref_pos=(u(31.3), u(46.5), 'right'), val_pos=(u(31.3), u(48.6), 'right'))
    L.w(('D402', '2'), (u(32), u(44)), (u(29), u(44)))
    L.w(('K401', '8'), (u(40), u(39)), (u(29), u(39)), (u(29), u(58)), (u(32), u(58)))   # RELAY_LOW
    L.at('Q401', u(31), u(60), ref_pos=(u(34), u(59), 'left'), val_pos=(u(34), u(60.5), 'left'))
    L.gnd(('Q401', '2'), length=U)
    L.w(('Q401', '1'), (u(27), u(60)))
    series(L, 'R406', u(25.5), u(60))
    shunt(L, 'R407', u(28), u(60))
    L.w(('R406', '1'), (u(20), u(60)))
    L.gl('RELAY_DRV', (u(20), u(60)), 'left')
    # ================================================================ OUT R jack
    t = jack(L, 'J404', 14, 64)
    L.w(t, (u(30), u(72)))
    shunt(L, 'D405', u(24), u(72), top='2', ang=90)
    L.gl('EFFECT_OUT_R', (u(30), u(72)), 'right')
    # ================================================================ expression input
    L.at('J406', u(14), u(84), ref_pos=(u(8), u(81), 'left'), val_pos=(u(8), u(88.5), 'left'))
    L.w(('J406', 'S'), (u(22), u(82)), (u(22), u(84)))
    L.gnd((u(22), u(84)))
    L.w(('J406', 'R'), (u(20), u(84)), (u(20), u(90)), (u(26), u(90)))       # EXP_RING
    L.w(('J406', 'T'), (u(18), u(86)), (u(18), u(93)), (u(28), u(93)))       # EXP_TIP
    for p in ('SN', 'RN', 'TN'):
        L.nc('J406', p)
    L.at('R415', u(26), u(87.5))
    L.w(('R415', '2'), (u(26), u(90)))
    L.pwr('+3V3', ('R415', '1'), 'up', length=U)
    L.at('D406', u(22), u(94.5), ang=90, ref_pos=(u(21.3), u(95.3), 'right'), val_pos=(u(21.3), u(96.8), 'right'))
    L.gnd(('D406', '1'), length=2 * U)
    shunt(L, 'R417', u(25), u(93))
    series(L, 'R416', u(29.5), u(93))
    L.w(('R416', '2'), (u(40), u(93)))                                       # EXP_BUF_IN
    shunt(L, 'C410', u(34), u(93))
    L.at('U401', u(43), u(94), ref_pos=(u(41), u(89.4), 'right'), val_pos=(u(41), u(90.9), 'right'))
    L.w(('U401', '1'), (u(50), u(94)))                                       # EXP_BUF_OUT
    L.w((u(48), u(94)), (u(48), u(103)), (u(38), u(103)), (u(38), u(95)), ('U401', '4'))
    L.pwr('+3V3', ('U401', '5'), 'up', length=2 * U)
    L.gnd(('U401', '2'), length=U)
    series(L, 'R418', u(51.5), u(94))
    L.w(('R418', '2'), (u(60), u(94)))                                       # EXP
    shunt(L, 'C412', u(56), u(94))
    L.gl('EXP', (u(60), u(94)), 'right')
    L.pwr('+3V3', (u(67), u(87)), 'up')
    L.w((u(67), u(87)), (u(67), u(89)))
    shunt(L, 'C411', u(67), u(89))
    # ================================================================ effect and hold LEDs from +9V, low-side 2N7002
    for led, res, q, rg, rp, drv, X, Y in (('D113', 'R404', 'Q402', 'R408', 'R409', 'LED_EFFECT_DRV', 88, 28),
                                            ('D114', 'R411', 'Q403', 'R412', 'R413', 'LED_HOLD_DRV', 88, 50)):
        X, Y = u(X), u(Y)
        L.at(led, X, Y, ang=90)
        L.pwr('+9V', (led, '2'), 'up', length=U)
        L.at(res, X, Y + 4.5 * U)
        L.w((led, '1'), (res, '1'))
        L.at(q, X - U, Y + 9 * U, ref_pos=(X + 1.5 * U, Y + 8.3 * U, 'left'), val_pos=(X + 1.5 * U, Y + 9.8 * U, 'left'))
        L.w((res, '2'), (q, '3'))
        L.gnd((q, '2'), length=U)
        L.w((q, '1'), (X - 7 * U, Y + 9 * U))
        series(L, rg, X - 8.5 * U, Y + 9 * U)
        shunt(L, rp, X - 5 * U, Y + 9 * U)
        L.w((rg, '1'), (X - 12 * U, Y + 9 * U))
        L.gl(drv, (X - 12 * U, Y + 9 * U), 'left')
    # ================================================================ footswitch pads: 1k / 100n into the MCU
    for j, res, cap, net, X, Y in (('J405', 'R410', 'C408', 'FSW_BYPASS_IN', 76, 72), ('J407', 'R414', 'C409', 'FSW_HOLD_IN', 76, 88)):
        X, Y = u(X), u(Y)
        L.at(j, X, Y, ang=180, ref_pos=(X - 5 * U, Y - 2.4 * U, 'left'), val_pos=(X - 5 * U, Y + 2.6 * U, 'left'))
        L.w((j, '2'), (X + 5 * U, Y - U), (X + 5 * U, Y + U))
        L.gnd((X + 5 * U, Y + U))
        L.w((j, '1'), (X + 3 * U, Y), (X + 3 * U, Y + 5 * U), (X + 8 * U, Y + 5 * U))
        series(L, res, X + 9.5 * U, Y + 5 * U)
        L.w((res, '2'), (X + 17 * U, Y + 5 * U))
        shunt(L, cap, X + 14 * U, Y + 5 * U)
        L.gl(net, (X + 17 * U, Y + 5 * U), 'right')
