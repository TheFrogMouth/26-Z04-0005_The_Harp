"""Controls and LEDs: four B10K pots with RC filters, three ON-ON-ON toggles, twelve note LEDs."""
from layouts.common import u, U, shunt, series

NOTES = ['C', 'Cs', 'D', 'Ds', 'E', 'F', 'Fs', 'G', 'Gs', 'A', 'As', 'B']


def layout(L):
    L.text(L.sheet.notes[0], u(8), u(6))
    # ---- pots: +3V3 across, wiper through 1k / 100n to the MCU ADC
    Y = u(28)
    for n, X in ((1, 16), (2, 44), (3, 72), (5, 100)):
        X = u(X)
        L.at('RV10%d' % n, X, Y, ang=180, ref_pos=(round(X - 5 * U, 3), Y - 4 * U, 'left'), val_pos=(round(X - 5 * U, 3), Y + 2 * U, 'left'))
        L.w(('RV10%d' % n, '3'), (X + 2 * U, Y - 2 * U), (X + 2 * U, Y - 5 * U))
        L.pwr('+3V3', (X + 2 * U, Y - 5 * U), 'up')
        L.w(('RV10%d' % n, '1'), (X + 2 * U, Y), (X + 2 * U, Y + 2 * U))
        L.gnd((X + 2 * U, Y + 2 * U))
        L.w(('RV10%d' % n, '2'), (X + 4 * U, Y - U))
        series(L, 'R10%d' % n, X + 5.5 * U, Y - U)
        L.w(('R10%d' % n, '2'), (X + 13 * U, Y - U))
        shunt(L, 'C10%d' % n, X + 10 * U, Y - U)
        L.gl('POT%d' % n, (X + 13 * U, Y - U), 'right')
        L.w(('RV10%d' % n, 'MH1'), (X - 11 * U, Y), (X - 11 * U, Y + 2 * U))
        L.w(('RV10%d' % n, 'MH2'), (X - 11 * U, Y - U), (X - 11 * U, Y))
        L.gnd((X - 11 * U, Y + 2 * U))
    # ---- toggles: commons to GND, A and B to MCU inputs with pull-ups
    Y = u(46)
    for n, X in ((1, 24), (2, 56), (3, 88)):
        X = u(X)
        sw = 'SW10%d' % n
        L.at(sw, X, Y, unit=1, ref_pos=(X - 2 * U, Y - 3 * U, 'left'), val_pos=(X + 2 * U, Y - 3 * U, 'left'))
        L.at(sw, X, Y + 6 * U, unit=2, ref_pos=(X - 2 * U, Y + 3 * U, 'left'), val_pos=(X + 2 * U, Y + 3 * U, 'left'))
        L.nc(sw, '1', 1)
        L.nc(sw, '6', 2)
        L.w((sw, '2', 1), (X - 4 * U, Y), (X - 4 * U, Y + 6 * U), (sw, '5', 2))
        L.w((X - 4 * U, Y + 6 * U), (X - 4 * U, Y + 8 * U))
        L.gnd((X - 4 * U, Y + 8 * U))
        L.gl('TOG%d_A' % n, (sw, '3', 1), 'right', length=3 * U)
        L.gl('TOG%d_B' % n, (sw, '4', 2), 'right', length=3 * U)
    # ---- note LEDs: PDx through 1k into the anode, cathode to GND
    for i, nm in enumerate(NOTES):
        X = u(14 + 18 * (i % 6))
        Y = u(68 + 10 * (i // 6))
        L.gl('NOTE_%s' % nm, (X, Y), 'left')
        L.w((X, Y), (X + 2 * U, Y))
        series(L, 'R%d' % (107 + i), X + 3.5 * U, Y)
        L.w(('R%d' % (107 + i), '2'), (X + 7 * U, Y))
        L.at('D1%02d' % (i + 1), X + 8.5 * U, Y, ang=180,
             ref_pos=(X + 8.5 * U, Y - 1.6 * U, 'center'), val_pos=(X + 8.5 * U, Y + 1.6 * U, 'center'))
        L.w(('D1%02d' % (i + 1), '1'), (X + 11 * U, Y), (X + 11 * U, Y + 2 * U))
        L.gnd((X + 11 * U, Y + 2 * U))
