"""ADC Driver: THS4522 channel A (left) and B (right) as single-ended to differential drivers into the AK4621 inputs."""
from layouts.common import u, U, shunt, series

# ref and pin names per channel (the two units of U601 have identical pin positions)
CH = {
    'A': dict(unit=1, in_net='EFFECT_IN_BUF', out='ADC_L', dy=0, pin={'PD': '1', 'INP': '2', 'INN': '3', 'VOCM': '4', 'VCC': '13', 'OUTP': '14', 'OUTN': '15', 'VSS': '16'},
              ref=dict(C601='C601', C602='C602', R601='R601', R602='R602', R603='R603', R604='R604', R605='R605', R606='R606',
                       C603='C603', C604='C604', C605='C605', C606='C606', C607='C607', C608='C608')),
    'B': dict(unit=2, in_net='EFFECT_IN_BUF_R', out='ADC_R', dy=48, pin={'PD': '5', 'INP': '6', 'INN': '7', 'VOCM': '8', 'VCC': '9', 'OUTP': '10', 'OUTN': '11', 'VSS': '12'},
              ref=dict(C601='C611', C602='C612', R601='R607', R602='R608', R603='R609', R604='R610', R605='R611', R606='R612',
                       C603='C613', C604='C614', C605='C615', C606='C616', C607='C617', C608=None)),
}


def channel(L, ch):
    c = CH[ch]
    un, dy, P, R = c['unit'], c['dy'], c['pin'], c['ref']
    Y = lambda n: u(n + dy)
    pn = lambda k: ('U601', P[k], un)
    X = u(60)
    L.at('U601', X, Y(40), unit=un, ref_pos=(u(50), Y(46.5), 'left'), val_pos=(u(50), Y(48), 'left'))
    # ---- inputs: input buffer (top) and VCOM_A reference (bottom)
    for y, net, cap, res, pin in ((34, c['in_net'], R['C601'], R['R601'], 'INP'), (46, 'VCOM_A', R['C602'], R['R602'], 'INN')):
        L.gl(net, (u(26), Y(y)), 'left')
        L.w((u(26), Y(y)), (u(34), Y(y)))
        shunt(L, cap, u(30), Y(y))
        series(L, res, u(35.5), Y(y))
        L.w((res, '2'), (u(50), Y(y)), 'V', pn(pin))
    # ---- outputs through 40.2R to ADC_x_N (top) / ADC_x_P (bottom)
    L.w(pn('OUTN'), (u(71), Y(38)))
    series(L, R['R605'], u(72.5), Y(38))
    L.w((R['R605'], '2'), (u(90), Y(38)))
    L.w(pn('OUTP'), (u(71), Y(42)))
    series(L, R['R606'], u(72.5), Y(42))
    L.w((R['R606'], '2'), (u(86), Y(42)))
    L.at(R['C605'], u(80), Y(40), ang=180)                          # across ADC_P (pin 1, below) / ADC_N
    L.w((u(80), Y(38)), (R['C605'], '2'))
    L.w((R['C605'], '1'), (u(80), Y(42)))
    shunt(L, R['C606'], u(83), Y(42))
    L.gl(c['out'] + '_P', (u(86), Y(42)), 'right')
    shunt(L, R['C607'], u(92), Y(38))
    L.w((u(90), Y(38)), (u(96), Y(38)))
    L.gl(c['out'] + '_N', (u(96), Y(38)), 'right')
    # ---- feedback: C603 / C604 to the outputs, R603 / R604 to the filtered outputs
    L.w((u(44), Y(34)), (u(44), Y(23)), (u(53), Y(23)))
    series(L, R['C603'], u(54.5), Y(23))
    L.w((R['C603'], '2'), (u(69), Y(23)), (u(69), Y(38)))
    L.w((u(40), Y(34)), (u(40), Y(19)), (u(60), Y(19)))
    series(L, R['R603'], u(61.5), Y(19))
    L.w((R['R603'], '2'), (u(78), Y(19)), (u(78), Y(38)))
    L.w((u(44), Y(46)), (u(44), Y(59)), (u(53), Y(59)))
    series(L, R['C604'], u(54.5), Y(59))
    L.w((R['C604'], '2'), (u(69), Y(59)), (u(69), Y(42)))
    L.w((u(40), Y(46)), (u(40), Y(63)), (u(60), Y(63)))
    series(L, R['R604'], u(61.5), Y(63))
    L.w((R['R604'], '2'), (u(78), Y(63)), (u(78), Y(42)))
    # ---- supply and VOCM
    L.w(pn('VCC'), (u(58.5), Y(29)))
    L.pwr('+5V', (u(58.5), Y(29)), 'up')
    L.w(pn('PD'), (u(60), Y(31)), (u(58.5), Y(31)))
    L.gnd(pn('VSS'), length=U)
    L.w(pn('VOCM'), (u(60), Y(51)), (u(53), Y(51)))
    if R['C608']:
        shunt(L, R['C608'], u(57), Y(51))
    L.gl('VCOM_B', (u(53), Y(51)), 'left')


def layout(L):
    L.text(L.sheet.notes[0], u(8), u(6))
    channel(L, 'A')
    channel(L, 'B')
    # ---- supply decoupling
    L.pwr('+5V', (u(90), u(22)), 'up')
    L.w((u(90), u(22)), (u(90), u(24)), (u(96), u(24)))
    shunt(L, 'C609', u(92), u(24))
    shunt(L, 'C610', u(96), u(24))
    L.pwr('+5V', (u(90), u(70)), 'up')
    L.w((u(90), u(70)), (u(90), u(72)), (u(92), u(72)))
    shunt(L, 'C618', u(92), u(72))
