"""Helpers shared by the sheet layouts."""
U = 2.54


def u(n):
    return round(n * U, 3)


def shunt(L, ref, x, y, top='1', length=U, gnd=True, ang=0):
    """Two-pin part hanging from the rail point (x, y): top pin on the rail, bottom pin to GND (or returned)."""
    x, y = round(x, 3), round(y, 3)
    L.at(ref, x, round(y + 1.5 * U, 3), ang=ang)
    bot = '2' if top == '1' else '1'
    if L.pin(ref, top)[1] != y:                     # part drawn the other way up
        L.at(ref, x, round(y + 1.5 * U, 3), ang=180 if ang == 0 else (ang + 180) % 360)
    if gnd:
        L.gnd((ref, bot), length=length)
        return None
    return L.pin(ref, bot)


def series(L, ref, xc, y, flip=False, **kw):
    """Two-pin part lying on a horizontal wire at y, centred at xc. pin 1 on the left unless flip."""
    return L.at(ref, xc, y, ang=270 if flip else 90, **kw)


def series_v(L, ref, x, yc, flip=False, **kw):
    """Two-pin part standing on a vertical wire at x, centred at yc. pin 1 on top unless flip."""
    return L.at(ref, x, yc, ang=180 if flip else 0, **kw)
