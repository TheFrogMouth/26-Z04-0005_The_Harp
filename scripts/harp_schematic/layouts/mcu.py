"""MCU: STM32H750VBT6 with its supplies, HSE crystal, reset and boot, SWD needle pads and the W25Q128 QSPI flash.

Two nets get local labels: QSPI_CLK (PB2, right side) and QSPI_NCS (PC11, right side) go to the flash on the
left; the flash sits on the left so its four IO lines run straight into PE7-PE10."""
from layouts.common import u, U, shunt, series

NOTES = ['C', 'Cs', 'D', 'Ds', 'E', 'F', 'Fs', 'G', 'Gs', 'A', 'As', 'B']
LEFT = {'PE2': 'CODEC_MCLK', 'PE3': 'CODEC_SDTO', 'PE4': 'CODEC_LRCK', 'PE5': 'CODEC_BICK', 'PE6': 'CODEC_SDTI',
        'PE7': None, 'PE8': None, 'PE9': None, 'PE10': None,
        'PE11': 'TOG1_A', 'PE12': 'TOG1_B', 'PE13': 'TOG2_A', 'PE14': 'TOG2_B', 'PE15': 'TOG3_A'}
RIGHT = {'PA0': 'POT1', 'PA1': 'POT2', 'PA2': 'POT3', 'PA4': 'POT5', 'PB1': 'EXP', 'PB4': 'CODEC_PDN', 'PB8': 'CODEC_CSN',
         'PB10': 'TOG3_B', 'PB12': 'FSW_BYPASS_IN', 'PB13': 'FSW_HOLD_IN', 'PC6': 'LED_EFFECT_DRV', 'PC7': 'LED_HOLD_DRV',
         'PC10': 'RELAY_DRV', 'PC14': 'CODEC_CCLK', 'PC15': 'CODEC_CDTI'}


def layout(L):
    L.allow_local = {'QSPI_CLK', 'QSPI_NCS'}
    L.text(L.sheet.notes[0], u(8), u(6))
    X, Y = u(70), u(56)
    P = L.at('U201', X, Y, ref_pos=(u(64), u(92), 'left'), val_pos=(u(64), u(93.5), 'left'))
    byname = {}
    from kisch import lib_pins
    for nb, nm, *_ in lib_pins(P.lib, P.part.unit):
        byname.setdefault(nm, []).append(nb)
    pinno = {nm: nbs[0] for nm, nbs in byname.items()}
    # ---- port pins to other sheets
    for nm, net in LEFT.items():
        if net:
            L.gl(net, ('U201', pinno[nm]), 'left', length=4 * U)
    for i, nm in enumerate(NOTES):
        L.gl('NOTE_%s' % nm, ('U201', pinno['PD%d' % i]), 'left', length=4 * U)
    for nm, net in RIGHT.items():
        L.gl(net, ('U201', pinno[nm]), 'right', length=4 * U)
    L.local('QSPI_CLK', ('U201', pinno['PB2']), 'right', length=4 * U)
    L.local('QSPI_NCS', ('U201', pinno['PC11']), 'right', length=4 * U)
    for nm in ('PE0', 'PE1', 'PD12', 'PD13', 'PD14', 'PD15', 'PA3', 'PA5', 'PA6', 'PA7', 'PA8', 'PA9', 'PA10', 'PA11', 'PA12',
               'PA15', 'PB0', 'PB5', 'PB6', 'PB7', 'PB9', 'PB11', 'PB14', 'PB15', 'PC0', 'PC1', 'PC2_C', 'PC3_C', 'PC4', 'PC5',
               'PC8', 'PC9', 'PC12', 'PC13'):
        L.nc('U201', pinno[nm])
    # ---- supplies: VDD x5 + VBAT on a +3V3 rail with six decoupling caps; VDDA through FB201 with 1u + 100n
    top = u(22)
    for nb in byname['VDD'] + byname['VBAT']:
        x, y = L.pin('U201', nb)
        L.w((x, y), (x, top))
    L.w((u(46), top), (u(72), top))
    L.pwr('+3V3', (u(46), top), 'up')
    for i, ref in enumerate(('C203', 'C204', 'C205', 'C206', 'C207', 'C208')):
        shunt(L, ref, u(48 + 3 * i), top)
    xa, ya = L.pin('U201', pinno['VDDA'])
    L.w((xa, ya), (xa, u(25)), (u(75), u(25)), (u(75), u(18)), (u(92), u(18)))          # VDDA
    L.flag((u(78), u(18)))
    L.w((u(81), u(18)), (u(81), u(16)))
    L.pwr('VDDA', (u(81), u(16)), 'up')
    shunt(L, 'C209', u(85), u(18))
    shunt(L, 'C210', u(89), u(18))
    series(L, 'FB201', u(93.5), u(18), flip=True)
    L.w(('FB201', '1'), (u(97), u(18)))
    L.pwr('+3V3', (u(97), u(18)), 'up')
    # VSS x5 (stacked) and VSSA
    xs, ys = L.pin('U201', byname['VSS'][0])
    L.w((xs, ys), (xs, u(88)))
    L.gnd((xs, u(88)))
    xsa, ysa = L.pin('U201', pinno['VSSA'])
    L.w((xsa, ysa), (xsa, u(87)), (xs, u(87)))
    # VCAP
    L.w(('U201', byname['VCAP'][0]), (u(54), u(74)))
    shunt(L, 'C201', u(54), u(74))
    L.w(('U201', byname['VCAP'][1]), (u(58), u(75)), (u(58), u(80)))
    L.at('C202', u(58), u(81.5))
    L.gnd(('C202', '2'), length=U)
    # ---- reset, boot, VREF+
    L.w(('U201', pinno['NRST']), (u(20), u(31)), (u(20), u(10)), (u(110), u(10)), (u(110), u(44)), (u(106), u(44)))
    shunt(L, 'C213', u(30), u(10))
    L.w(('U201', pinno['BOOT0']), (u(11), u(33)))
    shunt(L, 'R201', u(11), u(33))
    L.w(('U201', pinno['VREF+']), (u(52), u(35)))
    L.pwr('VDDA', (u(52), u(35)), 'left')
    # ---- HSE crystal: pin 1 (HSE_IN) below, pin 3 (HSE_OUT) above, GND pins left and right
    L.at('Y201', u(30), u(41), ang=90, ref_pos=(u(40), u(42), 'left'), val_pos=(u(40), u(43.4), 'left'))
    L.w(('U201', pinno['PH1']), (u(30), u(38)), ('Y201', '3'))                                   # HSE_OUT
    L.w(('U201', pinno['PH0']), (u(24), u(37)), (u(24), u(44)), (u(30), u(44)), ('Y201', '1'))   # HSE_IN
    shunt(L, 'C211', u(27), u(37))
    L.w(('Y201', '2'), (u(27), u(41)))
    L.w(('Y201', '4'), (u(33), u(41)))
    L.gnd((u(33), u(41)))
    shunt(L, 'C212', u(36), u(38))
    # ---- QSPI flash on the left: IO0-IO3 straight into PE7-PE10, CS and CLK by local label, 10k pull-up on CS
    L.at('U202', u(14), u(48), mirror='y', ref_pos=(u(18), u(36.8), 'center'), val_pos=(u(18), u(38.2), 'center'))
    for nm, nb in (('PE7', '5'), ('PE8', '2'), ('PE9', '3'), ('PE10', '7')):
        L.w(('U201', pinno[nm]), ('U202', nb))
    L.w(('U202', '1'), (u(22), u(45)))
    L.local('QSPI_NCS', (u(22), u(45)), 'right')
    L.w(('U202', '6'), (u(22), u(46)))
    L.local('QSPI_CLK', (u(22), u(46)), 'right')
    L.w((u(20), u(45)), (u(20), u(44)))
    L.at('R204', u(20), u(42.5), ref_pos=(u(20.8), u(41.8), 'left'), val_pos=(u(20.8), u(43.2), 'left'))
    L.w(('R204', '1'), (u(20), u(40)), (u(6), u(40)))
    L.w(('U202', '8'), (u(14), u(40)))
    L.pwr('+3V3', (u(6), u(40)), 'up')
    shunt(L, 'C214', u(9), u(40))
    L.gnd(('U202', '4'), length=U)
    # ---- SWD needle pads on the right: SWDIO / SWCLK through 22R, SWO, NRST, +3V3, GND
    L.at('W201', u(100), u(46), mirror='y')
    L.w(('U201', pinno['PA13']), (u(82), u(44)))
    series(L, 'R202', u(83.5), u(44), flip=True, ref_pos=(u(83.5), u(42.4), 'center'), val_pos=(u(83.5), u(43.4), 'center'))
    L.w(('R202', '1'), (u(92), u(44)), (u(92), u(45)), ('W201', '2'))
    L.w(('U201', pinno['PA14']), (u(86), u(45)))
    series(L, 'R203', u(87.5), u(45), flip=True, ref_pos=(u(87.5), u(46.6), 'center'), val_pos=(u(87.5), u(47.6), 'center'))
    L.w(('R203', '1'), (u(90), u(45)), (u(90), u(42)), (u(94), u(42)), ('W201', '4'))
    L.w(('U201', pinno['PB3']), (u(91), u(51)), (u(91), u(46)), ('W201', '6'))
    L.w(('W201', '1'), (u(112), u(46)), (u(112), u(42)))
    L.pwr('+3V3', (u(112), u(42)), 'up')
    L.gnd(('W201', '5'), length=U)
