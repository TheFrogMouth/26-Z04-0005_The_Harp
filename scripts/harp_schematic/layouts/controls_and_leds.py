"""Controls and LEDs: four B10K pots with RC filters, three ON-ON-ON toggles, the OLED connector with its I2C pull-ups."""
from layouts.common import u, U, shunt, series



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
    # ---- OLED: J408 (pin 1 GND, 2 +3V3, 3 SCL, 4 SDA), flipped so SDA is on top; I2C pull-ups on lanes above, 100n at the connector
    X, Y = u(30), u(72)
    L.at('J408', X, Y, mirror='x', ref_pos=(X + 1 * U, Y - 3 * U, 'left'), val_pos=(X + 1 * U, Y + 4 * U, 'left'))
    (x1, y1), (x2, y2), (x3, y3), (x4, y4) = [L.pin('J408', n) for n in '1234']
    L.gnd(('J408', '1'), dir='down', length=U)
    L.pwr('+3V3', ('J408', '2'), dir='left', length=U)
    a4, a3 = round(x4 - 4 * U, 3), round(x4 - 11 * U, 3)
    L.w(('J408', '4'), (a4, y4))
    L.gl('OLED_SDA', (a4, y4), 'left')
    L.w(('J408', '3'), (a3, y3))
    L.gl('OLED_SCL', (a3, y3), 'left')
    for ref, ax in (('R108', a4), ('R107', a3)):
        L.at(ref, ax, round(y4 - 3.5 * U, 3))
        L.pwr('+3V3', (ref, '1'), 'up', length=U)
    L.w(('R108', '2'), (a4, y4))
    L.w(('R107', '2'), (a3, y3))
    L.pwr('+3V3', (X + 8 * U, Y - 6 * U), 'up')
    L.w((X + 8 * U, Y - 6 * U), (X + 8 * U, Y - 4 * U))
    shunt(L, 'C104', X + 8 * U, Y - 4 * U)
