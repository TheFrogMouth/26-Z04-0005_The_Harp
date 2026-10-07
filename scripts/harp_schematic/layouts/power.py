"""Power sheet: DC in, TVS and filter, PMEG3010 series diode, TPS54202 buck to +3V3, NCP718 LDO to +5V."""
U = 2.54


def u(n):
    return round(n * U, 3)


def layout(L):
    L.text(L.sheet.notes[0], u(8), u(6))
    # ---------------------------------------------------------------- row 1: DC in, +9V, buck
    Y = u(20)                                   # DC_IN / +9V rail
    L.at('J401', u(12), u(21), ang=180, ref_pos=(u(8), u(18.6), 'left'), val_pos=(u(8), u(23.6), 'left'))
    L.w(('J401', '1'), (u(17), u(21)), (u(17), u(24)))
    L.gnd((u(17), u(24)))
    L.gnd((u(10), u(28)))
    L.flag((u(10), u(28)))
    L.w(('J401', '2'), (u(36), Y))              # DC_IN rail
    for ref, x in (('C301', 21), ('D301', 27)):
        L.at(ref, u(x), u(21.5), ang=90 if ref == 'D301' else 0)
        L.w((u(x), Y), (ref, '2' if ref == 'D301' else '1'))
        L.gnd((ref, '1' if ref == 'D301' else '2'), length=U)
    L.at('FB301', u(37.5), Y, ang=90)
    L.w(('FB301', '2'), (u(45), Y))             # DC_F
    L.at('C302', u(42), u(21.5))
    L.gnd(('C302', '2'), length=U)
    L.at('D302', u(46.5), Y, ang=180)
    L.w(('D302', '1'), (u(66), Y))              # +9V rail to the buck
    for ref, x in (('C303', 51), ('C304', 55)):
        L.at(ref, u(x), u(21.5))
        L.gnd((ref, '2'), length=U)
    L.w((u(59), Y), (u(59), u(18)))
    L.pwr('+9V', (u(59), u(18)), 'up')
    L.flag((u(62), Y))
    # buck
    L.at('U301', u(70), u(21), ref_pos=(u(67), u(17.3), 'left'), val_pos=(u(67), u(25.6), 'left'))
    L.nc('U301', '5')
    L.gnd(('U301', '1'), length=U)
    L.w(('U301', '6'), (u(76), Y), (u(76), u(16)), (u(77), u(16)))        # BOOT
    L.at('C305', u(78.5), u(16), ang=90)
    L.w(('C305', '2'), (u(81), u(16)), (u(81), u(21)))
    L.w(('U301', '2'), (u(82), u(21)))                                      # SW
    L.at('L301', u(83.5), u(21), ang=90)
    L.w(('L301', '2'), (u(104), u(21)))                                     # +3V3
    for ref, x in (('C306', 89), ('C307', 93)):
        L.at(ref, u(x), u(22.5))
        L.gnd((ref, '2'), length=U)
    L.w((u(97), u(21)), (u(97), u(19)))
    L.pwr('+3V3', (u(97), u(19)), 'up')
    L.flag((u(100), u(21)))
    L.at('R301', u(104), u(22.5))
    L.w(('R301', '2'), (u(104), u(26)))                                     # BUCK_FBT
    L.at('R302', u(104), u(27.5))
    L.w(('R302', '2'), (u(104), u(31)))                                     # BUCK_FB
    L.at('R303', u(104), u(32.5))
    L.gnd(('R303', '2'), length=U)
    L.w(('U301', '4'), (u(77), u(22)), (u(77), u(30)), (u(104), u(30)))    # FB
    # ---------------------------------------------------------------- row 2: LDO
    Y2 = u(44)
    L.pwr('+9V', (u(14), Y2), 'up')
    L.w((u(14), Y2), (u(16), Y2))
    L.at('FB302', u(17.5), Y2, ang=90)
    L.w(('FB302', '2'), (u(33), Y2))                                        # LDO_IN
    for ref, x in (('C308', 23), ('C309', 27)):
        L.at(ref, u(x), u(45.5))
        L.gnd((ref, '2'), length=U)
    L.at('U302', u(36), u(45), ref_pos=(u(33), u(41.6), 'left'), val_pos=(u(33), u(49.6), 'left'))
    L.w(('U302', '3'), (u(31), u(45)), (u(31), Y2))                         # EN tied to IN
    L.nc('U302', '4')
    L.gnd(('U302', '2'), length=U)
    L.w(('U302', '5'), (u(50), Y2))                                         # LDO_OUT
    for ref, x in (('C310', 43), ('C311', 47)):
        L.at(ref, u(x), u(45.5))
        L.gnd((ref, '2'), length=U)
    L.at('FB303', u(51.5), Y2, ang=90)
    L.w(('FB303', '2'), (u(60), Y2))                                        # +5V
    L.at('C312', u(56), u(45.5))
    L.gnd(('C312', '2'), length=U)
    L.w((u(60), Y2), (u(60), u(42)))
    L.pwr('+5V', (u(60), u(42)), 'up')
    L.flag((u(58), Y2))
