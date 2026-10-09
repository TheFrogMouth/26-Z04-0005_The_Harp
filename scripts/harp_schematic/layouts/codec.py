"""Codec: AK4621EF, its supplies and VCOM, the two OPA2348 VCOM buffers."""
from layouts.common import u, U, shunt, series


def layout(L):
    L.text(L.sheet.notes[0], u(8), u(6))
    X, Y = 56, 24
    L.at('IC501', u(X), u(Y), ref_pos=(u(44), u(24), 'left'), val_pos=(u(44), u(25.5), 'left'))
    # ---- digital interface, left side, from the MCU
    L.w(('IC501', '9'), (u(52), u(30)), (u(52), u(18)))                        # P/S high
    for pin, net in (('10', 'CODEC_MCLK'), ('11', 'CODEC_LRCK'), ('12', 'CODEC_BICK'), ('13', 'CODEC_SDTO'), ('14', 'CODEC_SDTI')):
        L.gl(net, ('IC501', pin), 'left', length=8 * U)
    L.nc('IC501', '15')
    # ---- +3V3: TVDD, DVDD, P/S, three 100n
    L.w(('IC501', '25'), (u(59.5), u(18)))
    L.w(('IC501', '24'), (u(62.5), u(18)))
    L.w((u(40), u(18)), (u(62.5), u(18)))
    L.pwr('+3V3', (u(40), u(18)), 'up')
    for ref, x in (('C504', 42), ('C505', 45), ('C506', 48)):
        shunt(L, ref, u(x), u(18))
    # ---- +5V: AVDD, VREF, 100n + 10u
    L.w(('IC501', '6'), (u(65), u(16)))
    L.w(('IC501', '8'), (u(66), u(16)))
    L.w((u(65), u(16)), (u(80), u(16)))
    L.pwr('+5V', (u(80), u(16)), 'up')
    shunt(L, 'C507', u(72), u(16))
    shunt(L, 'C508', u(76), u(16))
    # ---- DAC outputs to the output stages
    for pin, net in (('30', 'DAC_R_P'), ('29', 'DAC_R_N'), ('28', 'DAC_L_P'), ('27', 'DAC_L_N')):
        L.gl(net, ('IC501', pin), 'right', length=8 * U)
    # ---- mode pins: SDFIL, DEM0 and DFS0 low; PDN from the MCU through 5k1 with 100n
    L.w(('IC501', '23'), (u(76), u(29.5)), (u(76), u(28.5)), (u(88), u(28.5)))
    L.w(('IC501', '22'), (u(76), u(30.5)), (u(76), u(29.5)))
    L.gnd((u(88), u(28.5)))
    L.w(('IC501', '21'), (u(99), u(31.5)))                                     # PDN
    shunt(L, 'C501', u(96), u(31.5))
    series(L, 'R501', u(100.5), u(31.5), flip=True)
    L.w(('R501', '1'), (u(104), u(31.5)))
    L.gl('CODEC_PDN', (u(104), u(31.5)), 'right')
    L.w(('IC501', '20'), (u(92), u(32.5)), (u(92), u(36)))
    L.gnd((u(92), u(36)))
    for pin, net in (('19', 'CODEC_CSN'), ('18', 'CODEC_CCLK'), ('17', 'CODEC_CDTI')):
        L.gl(net, ('IC501', pin), 'right', length=8 * U)
    L.nc('IC501', '16')
    # ---- analogue inputs: AINL and AINR from the ADC driver channels
    L.gl('ADC_R_P', ('IC501', '2'), 'right', length=8 * U)
    L.gl('ADC_R_N', ('IC501', '3'), 'right', length=8 * U)
    L.gl('ADC_L_P', ('IC501', '4'), 'right', length=8 * U)
    L.gl('ADC_L_N', ('IC501', '5'), 'right', length=8 * U)
    # ---- ground and VCOM
    L.w(('IC501', '7'), (u(62), u(46)), (u(58), u(46)), (u(58), u(49)))
    L.w(('IC501', '26'), (u(64), u(46)), (u(62), u(46)))
    L.gnd((u(58), u(49)))
    L.w(('IC501', '1'), (u(67), u(48)), (u(77), u(48)))                        # VCOM bus
    shunt(L, 'C502', u(69), u(48))
    shunt(L, 'C503', u(73), u(48))
    # ---- VCOM buffers: U501A -> VCOM_A, U501B -> VCOM_B
    for unit, Yc, riser, pp, nn, oo, res, net in ((1, 62, 77, '3', '2', '1', 'R504', 'VCOM_A'), (2, 84, 74, '5', '6', '7', 'R505', 'VCOM_B')):
        L.at('U501', u(80), u(Yc), unit=unit, ref_pos=(u(78), u(Yc - 2.6), 'left'), val_pos=(u(78), u(Yc + 2.6), 'left'))
        L.w((u(riser), u(48)), (u(riser), u(Yc - 1)), ('U501', pp, unit))
        L.w(('U501', oo, unit), (u(90), u(Yc)), (u(90), u(Yc + 11)), (u(75), u(Yc + 11)), (u(75), u(Yc + 1)), ('U501', nn, unit))
        L.pwr('+5V', ('U501', '8', unit), 'up', length=U)
        L.gnd(('U501', '4', unit), length=U)
        L.w((u(90), u(Yc)), (u(92), u(Yc)))
        series(L, res, u(93.5), u(Yc))
        L.w((res, '2'), (u(97), u(Yc)))
        L.gl(net, (u(97), u(Yc)), 'right')
    L.pwr('+5V', (u(104), u(66)), 'up')
    L.w((u(104), u(66)), (u(104), u(68)))
    shunt(L, 'C509', u(104), u(68))
