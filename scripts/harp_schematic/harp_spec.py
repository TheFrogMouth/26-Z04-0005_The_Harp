"""The Harp: schematic spec. Circuits after the Timekeeper DSP board
(25-Z01-0001) and The Relic's relay bypass (26-A03-0003). Parts shared with
The Alchemist (26-A02-0001) carry its design and JLCPCB part numbers, as of
its main branch on 2026-10-05."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from schgen import Part, Sheet

R = 'Device:R'
C = 'Device:C'
CP = 'Device:C_Polarized'
FB = 'Device:FerriteBead'
R0603, R0805, R1206 = 'Resistor_SMD:R_0603_1608Metric', 'Resistor_SMD:R_0805_2012Metric', 'Resistor_SMD:R_1206_3216Metric'
C0603, C0805, C1206, C1210 = ('Capacitor_SMD:C_0603_1608Metric', 'Capacitor_SMD:C_0805_2012Metric',
                              'Capacitor_SMD:C_1206_3216Metric', 'Capacitor_SMD:C_1210_3225Metric')
TANT = 'Capacitor_Tantalum_SMD:CP_EIA-3216-12_Kemet-S'
TVS = 'Device:D_TVS'
SOD523 = 'Diode_SMD:D_SOD-523'
JACK = 'Connector_Audio:NMJ6HCD2'
JACK_FP = 'Connector_Audio:Jack_6.35mm_Neutrik_NMJ6HCD2_Horizontal'
OPAMP = 'Amplifier_Operational:TL072'
SOIC8 = 'Package_SO:SOIC-8_3.9x4.9mm_P1.27mm'


def jlc(mfr, mpn, lcsc='', jmfr='', jpn='', supplier=''):
    """Design part plus the part JLCPCB fits, the fields The Alchemist uses."""
    d = {'Manufacturer': mfr, 'Mfg Part #': mpn}
    if lcsc:
        d['LCSC'] = lcsc
    d['JLCPCB Manufacturer'], d['JLCPCB Part #'] = jmfr, jpn
    if supplier:
        d['Supplier'] = supplier
    return d


# Parts shared with The Alchemist, numbers from its bom_system.csv / symbols (2026-10-05)
P_JACK = jlc('Neutrik', 'NMJ6HCD2', 'C309277', 'HOOYA', 'PJ-609BA', 'JLCPCB')
P_POT = jlc('Alpha (Taiwan)', 'RD901F-40-15R1-B10K', 'C20619174', 'Alpha (Taiwan)', 'RD901F-40-15R1-B10K', 'LMS')
P_RELAY = jlc('Omron', 'G6K-2F-Y DC5', 'C2982926', 'Omron Electronics', 'G6K-2F-Y-5V', 'JLCPCB')
P_2N7002 = jlc('onsemi', '2N7002LT1G', 'C7420321', 'hongjiacheng', '2N7002')
P_1N4148W = jlc('Diodes Incorporated', '1N4148W-7-F', 'C7420318', 'hongjiacheng', '1N4148W')
P_150R_1206 = jlc('YAGEO', 'RC1206FR-07150RL', 'C17917', 'UNI ROYAL Uniroyal Elec', '1206W4F1500T5E', 'JLCPCB')
P_100R_0805 = jlc('YAGEO', 'AC0805FR-07100RL', 'C7468571', 'FOJAN', 'FRQ0805F1000TS')
P_100K_0805 = jlc('YAGEO', 'AC0805FR-07100KL', 'C149504', 'UNI ROYAL Uniroyal Elec', '0805W8F1003T5E')
P_1K_0805 = jlc('YAGEO', 'AC0805FR-071KL', 'C17513', 'UNI ROYAL Uniroyal Elec', '0805W8F1001T5E')
P_100N_0603 = jlc('YAGEO', 'CC0603KRX7R9BB104', 'C14663', 'YAGEO', 'CC0603KRX7R9BB104')
P_PANEL_LED = jlc('Kingbright', 'WP710A10ID', supplier='Mouser')
P_DC_JACK = jlc('Same Sky (formerly CUI Devices)', 'PJ-063AH', 'C22434582', 'CUI', 'PJ-063AH', 'JLCPCB')
P_LDO5 = jlc('onsemi', 'NCP718ASN500T1G', 'C603786', 'onsemi', 'NCP718ASN500T1G')
FSW_PADS = 'Resistor_SMD:R_2816_7142Metric_Pad3.20x4.45mm_HandSolder'


def r(ref, val, a, b, fp=R0603, **kw):
    return Part(ref, R, val, fp, {'1': a, '2': b}, **kw)


def c(ref, val, a, b, fp=C0603, **kw):
    return Part(ref, C, val, fp, {'1': a, '2': b}, **kw)


def cp(ref, val, plus, minus, fp, **kw):
    return Part(ref, CP, val, fp, {'1': plus, '2': minus}, **kw)


def tvs(ref, sig):
    return Part(ref, TVS, 'PESD5V0U1BB,115', SOD523, {'1': 'GND', '2': sig},
                props={'Manufacturer': 'Nexperia', 'Mfg Part #': 'PESD5V0U1BB,115'})


SHEETS = []

# ===================================================================== 1 Controls
ctl = Sheet('Controls and LEDs', 'Controls and LEDs.kicad_sch', 'Controls and LEDs')
ctl.notes.append('Controls and display. Four B10K pots on the Alchemist grid: Mix, Sustain, Strings (row +38) and Jawari (0, +13), across +3V3, '
                 'wipers to ADC1 PA0, PA1, PA2, PA4 through 1k / 100n.\nThree Taiway 100-DP6 ON-ON-ON toggles, as The Alchemist: Tuning (-20, +13), '
                 'Brightness (+20, +13), Retune (0, -5). Commons (2, 5) to GND, pins 3 and 4 to two MCU inputs with internal pull-ups: '
                 'up = A low B high, centre = both low, down = A high B low.\nDisplay: a thin 0.91 in 128x32 SSD1306 OLED strip on I2C1 (PB6 SCL, PB7 SDA), '
                 '4.7k pull-ups to +3V3, behind a window at face Y -18. J408 is the module connector (GND, +3V3, SCL, SDA).')
POTS = {1: 'Mix', 2: 'Sustain', 3: 'Strings', 5: 'Jawari'}   # RV10n keeps its face position: 1-3 row +38, 5 = (0, +13)
for n, nm in POTS.items():
    ctl.add(Part('RV10%d' % n, 'POT:RD901F-40-15R1-B10K-00DL1', 'B10K', 'Potentiometer_THT:RD901F4015R1B10K00DL1',
                 {'1': 'GND', '2': 'POT%d_W' % n, '3': '+3V3', 'MH1': 'GND', 'MH2': 'GND'}, props=P_POT, note=nm))
    ctl.add(r('R10%d' % n, '1k', 'POT%d_W' % n, 'POT%d' % n))
    ctl.add(c('C10%d' % n, '100n', 'POT%d' % n, 'GND'))
P_TOGGLE = jlc('Taiway', '100-DP6-T200B1M2QE', supplier='LMS')
for i, nm in enumerate(['Tuning: Follow / Key / Drone', 'Retune: Snap / Glide / Lock', 'Brightness: Dark / Warm / Glassy']):
    n = i + 1
    for unit, pins in ((1, {'1': None, '2': 'GND', '3': 'TOG%d_A' % n}), (2, {'4': 'TOG%d_B' % n, '5': 'GND', '6': None})):
        ctl.add(Part('SW10%d' % n, 'Switch:SW_DPDT_x2', '100-DP6', 'SPDT Switches:100DP3T1B2M2QE', pins, unit=unit,
                     dnp=True, props=P_TOGGLE, note=nm if unit == 1 else None))
ctl.add(Part('J408', 'Connector:Conn_01x04_Socket', 'OLED 0.91 128x32', 'Connector_JST:JST_SH_SM04B-SRSS-TB_1x04-1MP_P1.00mm_Horizontal',
             {'1': 'GND', '2': '+3V3', '3': 'OLED_SCL', '4': 'OLED_SDA'}, props={'Manufacturer': 'JST', 'Mfg Part #': 'SM04B-SRSS-TB'},
             note='OLED module (GND, 3V3, SCL, SDA)'))
ctl.add(r('R107', '4.7k', '+3V3', 'OLED_SCL'), r('R108', '4.7k', '+3V3', 'OLED_SDA'))
ctl.add(c('C104', '100n', '+3V3', 'GND', note='OLED supply'))
SHEETS.append(ctl)

# ===================================================================== 2 MCU
mcu = Sheet('MCU', 'MCU.kicad_sch', 'MCU', paper='A3')
mcu.notes.append('STM32H750VBT6, LQFP-100: the smallest-pin-count H750. Pin map kept from the Timekeeper where the package allows: SAI1 on PE2-PE6, '
                 'codec control PC14/PC15/PB8/PB4, relay PC10, SWD PA13/PA14/PB3, HSE 25 MHz.\nQUADSPI moves to bank 2 (PB2 CLK, PC11 NCS, '
                 'PE7-PE10 IO0-3) because PF6-PF10 do not exist on LQFP-100 and bank 1 IO2 would take PE2 from SAI1: set FSEL=1 in firmware. '
                 '[CONFIRM AFs in CubeMX]')
PIN = {
    'PE2': 'CODEC_MCLK', 'PE3': 'CODEC_SDTO', 'PE4': 'CODEC_LRCK', 'PE5': 'CODEC_BICK', 'PE6': 'CODEC_SDTI',
    'PC14': 'CODEC_CCLK', 'PC15': 'CODEC_CDTI', 'PB8': 'CODEC_CSN', 'PB4': 'CODEC_PDN',
    'PB2': 'QSPI_CLK', 'PC11': 'QSPI_NCS', 'PE7': 'QSPI_IO0', 'PE8': 'QSPI_IO1', 'PE9': 'QSPI_IO2', 'PE10': 'QSPI_IO3',
    'PA0': 'POT1', 'PA1': 'POT2', 'PA2': 'POT3', 'PA4': 'POT5', 'PB1': 'EXP',
    'PE11': 'TOG1_A', 'PE12': 'TOG1_B', 'PE13': 'TOG2_A', 'PE14': 'TOG2_B', 'PE15': 'TOG3_A', 'PB10': 'TOG3_B',
    'PB6': 'OLED_SCL', 'PB7': 'OLED_SDA', 'PB12': 'FSW_BYPASS_IN', 'PB13': 'FSW_HOLD_IN', 'PC10': 'RELAY_DRV', 'PC6': 'LED_EFFECT_DRV', 'PC7': 'LED_HOLD_DRV',
    'PA13': 'SWDIO', 'PA14': 'SWCLK', 'PB3': 'SWO', 'PH0': 'HSE_IN', 'PH1': 'HSE_OUT', 'NRST': 'NRST', 'BOOT0': 'BOOT0',
    'VBAT': '+3V3', 'VDDA': 'VDDA', 'VREF+': 'VDDA', 'VSSA': 'GND', 'VDD': '+3V3', 'VSS': 'GND',
}
import schgen
from kisch import lib_pins
mpins = {}
vcap = 0
for nb, nm, *_ in lib_pins(schgen.libnode('MCU_ST_STM32H7:STM32H750VBTx')):
    if nm == 'VCAP':
        vcap += 1
        mpins[nb] = 'VCAP%d' % vcap
    else:
        mpins[nb] = PIN.get(nm)     # None = no-connect
mcu.add(Part('U201', 'MCU_ST_STM32H7:STM32H750VBTx', 'STM32H750VBT6', 'Package_QFP:LQFP-100_14x14mm_P0.5mm', mpins,
             props={'Manufacturer': 'STMicroelectronics', 'Mfg Part #': 'STM32H750VBT6'}))
mcu.add(c('C201', '2.2u', 'VCAP1', 'GND'), c('C202', '2.2u', 'VCAP2', 'GND'))
mcu.add(c('C203', '4.7u', '+3V3', 'GND', fp=C0805))
for k in range(5):
    mcu.add(c('C%d' % (204 + k), '100n', '+3V3', 'GND', note='VDD decoupling, one per VDD pin'))
mcu.add(Part('FB201', FB, '220R', 'Inductor_SMD:L_0603_1608Metric', {'1': '+3V3', '2': 'VDDA'}))
mcu.add(c('C209', '1u', 'VDDA', 'GND'), c('C210', '100n', 'VDDA', 'GND'))
mcu.add(Part('Y201', 'Device:Crystal_GND24', '25MHz 9pF', 'Crystal:Crystal_SMD_2016-4Pin_2.0x1.6mm',
             {'1': 'HSE_IN', '2': 'GND', '3': 'HSE_OUT', '4': 'GND'}))
mcu.add(c('C211', '8p', 'HSE_IN', 'GND'), c('C212', '8p', 'HSE_OUT', 'GND'))
mcu.add(c('C213', '100n', 'NRST', 'GND'), r('R201', '10k', 'BOOT0', 'GND'))
mcu.add(Part('W201', '8.06.05_10-PIN_NEEDLE_ADAPTER:8.06.05_6-PIN_NEEDLE_ADAPTER', 'SWD needle', 'LIB_STLINK:SEGGER_8.06.05_6-PIN_NEEDLE_ADAPTER',
             {'1': '+3V3', '2': 'SWDIO_N', '3': 'NRST', '4': 'SWCLK_N', '5': 'GND', '6': 'SWO'}))
mcu.add(r('R202', '22R', 'SWDIO_N', 'SWDIO'), r('R203', '22R', 'SWCLK_N', 'SWCLK'))
mcu.add(Part('U202', 'Memory_Flash:W25Q128JVS', 'W25Q128JVSIQ', 'Package_SO:SOIC-8_5.23x5.23mm_P1.27mm',
             {'1': 'QSPI_NCS', '2': 'QSPI_IO1', '3': 'QSPI_IO2', '4': 'GND', '5': 'QSPI_IO0', '6': 'QSPI_CLK', '7': 'QSPI_IO3', '8': '+3V3'},
             props={'Manufacturer': 'Winbond', 'Mfg Part #': 'W25Q128JVSIQ'}))
mcu.add(c('C214', '100n', '+3V3', 'GND'), r('R204', '10k', '+3V3', 'QSPI_NCS'))
mcu.flags = ['VDDA']
SHEETS.append(mcu)

# ===================================================================== 3 Power
pw = Sheet('Power', 'Power.kicad_sch', 'Power')
pw.notes.append('Power, after the Timekeeper: 9 V centre-negative on J401 (PJ-063AH, top wall), SMAJ10CA TVS, PMEG3010 series diode, '
                'TPS54202 buck to +3V3 (digital), NCP718 to +5V (codec analog and op-amps).\nThe relay coil and the LEDs run from +9V so the '
                'audio rails never carry their current.')
pw.add(Part('J401', 'Connector:Conn_01x02_Socket', 'PJ-063AH', 'Connector_BarrelJack:BarrelJack_CUI_PJ-063AH_Horizontal',
            {'1': 'GND', '2': 'DC_IN'}, props=P_DC_JACK))
pw.add(Part('FB301', FB, '600R', 'Inductor_SMD:L_0603_1608Metric', {'1': 'DC_IN', '2': 'DC_F'}))
pw.add(c('C301', '2.2u', 'DC_IN', 'GND'))
pw.add(Part('D301', TVS, 'SMAJ10CA', 'Diode_SMD:D_SMA', {'1': 'GND', '2': 'DC_IN'}, props={'Manufacturer': 'Littelfuse', 'Mfg Part #': 'SMAJ10CA'}))
pw.add(c('C302', '2.2u', 'DC_F', 'GND'))
pw.add(Part('D302', 'Diode:PMEG3010ER', 'PMEG3010ER', 'Diode_SMD:Nexperia_CFP3_SOD-123W', {'1': '+9V', '2': 'DC_F'},
            props={'Manufacturer': 'Nexperia', 'Mfg Part #': 'PMEG3010ER,115'}))
pw.add(c('C303', '10u', '+9V', 'GND', fp=C1206), c('C304', '100n', '+9V', 'GND'))
pw.add(Part('U301', 'Regulator_Switching:TPS54202DDC', 'TPS54202DDC', 'Package_TO_SOT_SMD:SOT-23-6',
            {'1': 'GND', '2': 'SW', '3': '+9V', '4': 'BUCK_FB', '5': None, '6': 'BUCK_BOOT'},
            props={'Manufacturer': 'Texas Instruments', 'Mfg Part #': 'TPS54202DDCR'}))
pw.add(c('C305', '100n', 'BUCK_BOOT', 'SW'))
pw.add(Part('L301', 'Device:L', '10u', 'Inductor_SMD:L_APV_ANR5020', {'1': 'SW', '2': '+3V3'}))
pw.add(r('R301', '49.9', '+3V3', 'BUCK_FBT'), r('R302', '100k', 'BUCK_FBT', 'BUCK_FB'), r('R303', '22k', 'BUCK_FB', 'GND'))
pw.add(c('C306', '22u', '+3V3', 'GND', fp=C1210), c('C307', '22u', '+3V3', 'GND', fp=C1210))
pw.add(Part('FB302', FB, '600R', 'Inductor_SMD:L_0603_1608Metric', {'1': '+9V', '2': 'LDO_IN'}))
pw.add(c('C308', '47u', 'LDO_IN', 'GND', fp=C1210), c('C309', '2.2u', 'LDO_IN', 'GND'))
pw.add(Part('U302', 'Regulator_Linear:NCP718xSN500', 'NCP718ASN500T1G', 'Package_TO_SOT_SMD:TSOT-23-5',
            {'1': 'LDO_IN', '2': 'GND', '3': 'LDO_IN', '4': None, '5': 'LDO_OUT'},
            props=P_LDO5))
pw.add(c('C310', '2.2u', 'LDO_OUT', 'GND'), c('C311', '2.2u', 'LDO_OUT', 'GND'))
pw.add(Part('FB303', FB, '600R', 'Inductor_SMD:L_0603_1608Metric', {'1': 'LDO_OUT', '2': '+5V'}))
pw.add(c('C312', '2.2u', '+5V', 'GND'))
pw.flags = ['GND', '+9V', '+3V3', '+5V']
SHEETS.append(pw)

# ===================================================================== 4 Jacks and bypass
io = Sheet('Jacks and Bypass', 'Jacks and Bypass.kicad_sch', 'Jacks and Bypass')
io.notes.append('Jacks on the Alchemist positions: IN (J402, right lower), EXP (J406, right upper), OUT L (J403, left lower), OUT R (J404, left upper).\n'
                'Relay true bypass after The Alchemist: K401 (Omron G6K-2F-Y, 5 V coil) at rest joins IN to OUT L (2-3) and grounds the effect input (6-7); '
                'energised it routes IN to the effect (5-6) and the effect to OUT L (3-4).\nIN is a TRS jack, tip = left, ring = right: a mono plug shorts the ring to the sleeve, the right channel reads silence and the firmware copies left to right. '
                'The relay isolates the left input only; the right input is muted by the DSP in true bypass. OUT R is driven straight from the DSP and is silent in true bypass; '
                'stereo players use Trails mode. The effect and Hold LEDs and the relay coil run from +9V.')
io.add(Part('J402', JACK, 'NMJ6HCD2', JACK_FP, {'T': 'IN', 'S': 'GND', 'R': 'IN_R', 'RN': None, 'SN': None, 'TN': None}, props=P_JACK, note='IN (TRS: tip L, ring R)'))
io.add(Part('J403', JACK, 'NMJ6HCD2', JACK_FP, {'T': 'OUT_L', 'S': 'GND', 'R': None, 'RN': None, 'SN': None, 'TN': None}, props=P_JACK, note='OUT L'))
io.add(Part('J404', JACK, 'NMJ6HCD2', JACK_FP, {'T': 'EFFECT_OUT_R', 'S': 'GND', 'R': None, 'RN': None, 'SN': None, 'TN': None}, props=P_JACK, note='OUT R'))
io.add(Part('J406', JACK, 'NMJ6HCD2', JACK_FP, {'T': 'EXP_TIP', 'S': 'GND', 'R': 'EXP_RING', 'RN': None, 'SN': None, 'TN': None}, props=P_JACK, note='EXP (TRS)'))
io.add(tvs('D407', 'IN_R'), tvs('D403', 'IN'), tvs('D404', 'OUT_L'), tvs('D405', 'EFFECT_OUT_R'), tvs('D406', 'EXP_TIP'))
io.add(Part('K401', 'Relay:G6K-2', 'G6K-2F-Y', 'Relay_SMD:Relay_DPDT_Omron_G6K-2F-Y',
            {'1': 'RELAY_COIL', '8': 'RELAY_LOW', '2': 'IN', '3': 'OUT_L', '4': 'EFFECT_OUT_L', '5': 'IN', '6': 'EFFECT_IN', '7': 'GND'},
            props=P_RELAY, note='5 V coil (178R) from +9V through R405'))
io.add(r('R405', '150R', '+9V', 'RELAY_COIL', fp=R1206, props=P_150R_1206))
io.add(Part('D402', 'Device:D', '1N4148W', 'Diode_SMD:D_SOD-123', {'1': 'RELAY_COIL', '2': 'RELAY_LOW'}, props=P_1N4148W))
io.add(Part('Q401', 'Transistor_FET:2N7002', '2N7002', 'Package_TO_SOT_SMD:SOT-23', {'1': 'RELAY_G', '2': 'GND', '3': 'RELAY_LOW'}, props=P_2N7002))
io.add(r('R406', '100R', 'RELAY_DRV', 'RELAY_G', fp=R0805, props=P_100R_0805), r('R407', '100k', 'RELAY_G', 'GND', fp=R0805, props=P_100K_0805))
# effect LED (D113, left heel) and Hold LED (D114, right heel)
io.add(Part('D113', 'Device:LED', 'RED_LED', 'LED_THT:LED_D3.0mm', {'1': 'LED_EFF_K', '2': '+9V'}, dnp=True, props=P_PANEL_LED,
            note='Effect LED (-20, -35), fitted at final assembly'))
io.add(r('R404', '1k', 'LED_EFF_K', 'LED_EFF_LOW', fp=R0805, props=P_1K_0805))
io.add(Part('Q402', 'Transistor_FET:2N7002', '2N7002', 'Package_TO_SOT_SMD:SOT-23', {'1': 'LED_EFF_G', '2': 'GND', '3': 'LED_EFF_LOW'}, props=P_2N7002))
io.add(r('R408', '100R', 'LED_EFFECT_DRV', 'LED_EFF_G', fp=R0805, props=P_100R_0805), r('R409', '100k', 'LED_EFF_G', 'GND', fp=R0805, props=P_100K_0805))
io.add(Part('D114', 'Device:LED', 'RED_LED', 'LED_THT:LED_D3.0mm', {'1': 'LED_HOLD_K', '2': '+9V'}, dnp=True, props=P_PANEL_LED,
            note='Hold LED (+20, -35), fitted at final assembly'))
io.add(r('R411', '1k', 'LED_HOLD_K', 'LED_HOLD_LOW', fp=R0805, props=P_1K_0805))
io.add(Part('Q403', 'Transistor_FET:2N7002', '2N7002', 'Package_TO_SOT_SMD:SOT-23', {'1': 'LED_HOLD_G', '2': 'GND', '3': 'LED_HOLD_LOW'}, props=P_2N7002))
io.add(r('R412', '100R', 'LED_HOLD_DRV', 'LED_HOLD_G', fp=R0805, props=P_100R_0805), r('R413', '100k', 'LED_HOLD_G', 'GND', fp=R0805, props=P_100K_0805))
# footswitches: momentary SPST-NO soft-touch, two wires each to hand-solder pads, as The Alchemist's J502
io.add(Part('J405', 'Connector:Conn_01x02_Socket', 'Bypass FSW', FSW_PADS,
            {'1': 'FSW_BYPASS', '2': 'GND'}, dnp=True, props={'Supplier': 'none'}, note='Bypass footswitch (-20, -49), wire pads'))
io.add(r('R410', '1k', 'FSW_BYPASS', 'FSW_BYPASS_IN', fp=R0805, props=P_1K_0805), c('C408', '100n', 'FSW_BYPASS_IN', 'GND', props=P_100N_0603))
io.add(Part('J407', 'Connector:Conn_01x02_Socket', 'Hold FSW', FSW_PADS,
            {'1': 'FSW_HOLD', '2': 'GND'}, dnp=True, props={'Supplier': 'none'}, note='Hold footswitch (+20, -49), wire pads'))
io.add(r('R414', '1k', 'FSW_HOLD', 'FSW_HOLD_IN', fp=R0805, props=P_1K_0805), c('C409', '100n', 'FSW_HOLD_IN', 'GND', props=P_100N_0603))
# expression input, after the Timekeeper (U702)
io.add(r('R415', '100R', '+3V3', 'EXP_RING'))
io.add(r('R416', '1k', 'EXP_TIP', 'EXP_BUF_IN'), r('R417', '100k', 'EXP_TIP', 'GND', note='reads 0 with no pedal'))
io.add(c('C410', '100n', 'EXP_BUF_IN', 'GND'))
io.add(Part('U401', 'Amplifier_Operational:MCP6001-OT', 'MCP6001T-I/OT', 'Package_TO_SOT_SMD:SOT-23-5',
            {'1': 'EXP_BUF_OUT', '2': 'GND', '3': 'EXP_BUF_IN', '4': 'EXP_BUF_OUT', '5': '+3V3'},
            props={'Manufacturer': 'Microchip', 'Mfg Part #': 'MCP6001T-I/OT'}))
io.add(c('C411', '100n', '+3V3', 'GND'))
io.add(r('R418', '100R', 'EXP_BUF_OUT', 'EXP'), c('C412', '2.7n', 'EXP', 'GND'))
SHEETS.append(io)

# ===================================================================== 5 Codec
cd = Sheet('Codec', 'Codec.kicad_sch', 'Codec')
cd.notes.append('AK4621EF codec, as the Timekeeper (IC401). Serial control (P/S high) bit-banged on CSN/CCLK/CDTI. PDN reset by RC.\n'
                'Stereo in, single-ended at the jack: AINL and AINR come from the two THS4522 driver channels (single-ended to differential), as the Timekeeper. '
                'Stereo out: AOUTL/AOUTR to the output stages (the Timekeeper wired them crossed; here L is L).\n'
                'U501 buffers VCOM: VCOM_A biases the input buffer and the ADC driver input reference, VCOM_B the ADC driver VOCM and the output stages.')
cd.add(Part('IC501', 'Audio:AK4621EF', 'AK4621EF', 'Audio_Module:SOP65P760X150-30N',
            {'1': 'VCOM', '2': 'ADC_R_P', '3': 'ADC_R_N', '4': 'ADC_L_P', '5': 'ADC_L_N', '6': '+5V', '7': 'GND', '8': '+5V',
             '9': '+3V3', '10': 'CODEC_MCLK', '11': 'CODEC_LRCK', '12': 'CODEC_BICK', '13': 'CODEC_SDTO', '14': 'CODEC_SDTI',
             '15': None, '16': None, '17': 'CODEC_CDTI', '18': 'CODEC_CCLK', '19': 'CODEC_CSN', '20': 'GND', '21': 'PDN',
             '22': 'GND', '23': 'GND', '24': '+3V3', '25': '+3V3', '26': 'GND',
             '27': 'DAC_L_N', '28': 'DAC_L_P', '29': 'DAC_R_N', '30': 'DAC_R_P'},
            props={'Manufacturer': 'Asahi Kasei Microdevices', 'Mfg Part #': 'AK4621EF'}))
cd.add(r('R501', '5k1', 'CODEC_PDN', 'PDN'), c('C501', '100n', 'PDN', 'GND'))
cd.add(cp('C502', '10u', 'VCOM', 'GND', 'Capacitor_SMD:CP_Elec_4x5.8'), c('C503', '100n', 'VCOM', 'GND'))
cd.add(c('C504', '100n', '+3V3', 'GND', note='TVDD'), c('C505', '100n', '+3V3', 'GND', note='DVDD'), c('C506', '100n', '+3V3', 'GND'))
cd.add(c('C507', '100n', '+5V', 'GND', note='AVDD/VREF'), cp('C508', '10u', '+5V', 'GND', 'Capacitor_SMD:CP_Elec_4x5.8'))
for unit, (vin, vout, rr) in enumerate([('VCOM', 'VCOM_A_RAW', 'R504'), ('VCOM', 'VCOM_B_RAW', 'R505')], start=1):
    pins = {'1': 'VCOM_A_RAW', '2': 'VCOM_A_RAW', '3': 'VCOM'} if unit == 1 else {'7': 'VCOM_B_RAW', '6': 'VCOM_B_RAW', '5': 'VCOM'}
    pins.update({'4': 'GND', '8': '+5V'})
    cd.add(Part('U501', 'SuperAudioBoard-rescue:OPA2348', 'OPA2348AIDR', SOIC8, pins, unit=unit,
                props={'Manufacturer': 'Texas Instruments', 'Mfg Part #': 'OPA2348AIDR'}))
cd.add(r('R504', '10R', 'VCOM_A_RAW', 'VCOM_A'), r('R505', '10R', 'VCOM_B_RAW', 'VCOM_B'))
cd.add(c('C509', '100n', '+5V', 'GND', note='U501 supply'))
SHEETS.append(cd)

# ===================================================================== 6 ADC driver
ad = Sheet('ADC Driver', 'ADC Driver.kicad_sch', 'ADC Driver')
ad.notes.append('Single-ended to differential ADC drivers, the Timekeeper\'s AnalogInputBuffer: THS4522 channel A (left) and B (right), gain 0.59 (620R / 1.05k), 40.2R + 2.7n '
                'differential filter, VOCM from VCOM_B.\nThe input reference (INN side) goes to VCOM_A, the DC level of the input buffer output '
                '(the Timekeeper left it open). Channel B drives the right channel the same way (R607-R612, C611-C618), from the IN ring buffer U701B.')
THS = 'SuperAudioBoard-rescue:THS4521'
ad.add(Part('U601', THS, 'THS4522IPW', 'Package_SO:TSSOP-16_4.4x5mm_P0.65mm',
            {'1': '+5V', '2': 'FDA_INP', '3': 'FDA_INN', '4': 'VCOM_B', '13': '+5V', '14': 'FDA_OUTP', '15': 'FDA_OUTN', '16': 'GND'},
            unit=1, props={'Manufacturer': 'Texas Instruments', 'Mfg Part #': 'THS4522IPWR'}))
ad.add(Part('U601', THS, 'THS4522IPW', 'Package_SO:TSSOP-16_4.4x5mm_P0.65mm',
            {'5': '+5V', '6': 'FDB_INP', '7': 'FDB_INN', '8': 'VCOM_B', '9': '+5V', '10': 'FDB_OUTP', '11': 'FDB_OUTN', '12': 'GND'},
            unit=2, props={'Manufacturer': 'Texas Instruments', 'Mfg Part #': 'THS4522IPWR'}))
ad.add(c('C601', '100p', 'EFFECT_IN_BUF', 'GND'), r('R601', '1k', 'EFFECT_IN_BUF', 'FDA_INP'))
ad.add(c('C602', '100p', 'VCOM_A', 'GND'), r('R602', '1.05k', 'VCOM_A', 'FDA_INN', note='= R601 + R705: matches the signal leg (Timekeeper review H2)'))
ad.add(r('R603', '620', 'FDA_INP', 'ADC_L_N', note='gain 0.59: a 4.8 Vpp input just reaches ADC full scale'), c('C603', '1n', 'FDA_INP', 'FDA_OUTN'))
ad.add(r('R604', '620', 'FDA_INN', 'ADC_L_P', note='gain 0.59: a 4.8 Vpp input just reaches ADC full scale'), c('C604', '1n', 'FDA_INN', 'FDA_OUTP'))
ad.add(r('R605', '40.2', 'FDA_OUTN', 'ADC_L_N'), r('R606', '40.2', 'FDA_OUTP', 'ADC_L_P'))
ad.add(c('C605', '2.7n', 'ADC_L_P', 'ADC_L_N'), c('C606', '100p', 'ADC_L_P', 'GND'), c('C607', '100p', 'ADC_L_N', 'GND'))
ad.add(c('C608', '100n', 'VCOM_B', 'GND'), c('C609', '100n', '+5V', 'GND'), c('C610', '100n', '+5V', 'GND'))
ad.add(c('C611', '100p', 'EFFECT_IN_BUF_R', 'GND'), r('R607', '1k', 'EFFECT_IN_BUF_R', 'FDB_INP'))
ad.add(c('C612', '100p', 'VCOM_A', 'GND'), r('R608', '1.05k', 'VCOM_A', 'FDB_INN', note='= R607 + R722: matches the signal leg'))
ad.add(r('R609', '620', 'FDB_INP', 'ADC_R_N', note='gain 0.59, as channel A'), c('C613', '1n', 'FDB_INP', 'FDB_OUTN'))
ad.add(r('R610', '620', 'FDB_INN', 'ADC_R_P', note='gain 0.59, as channel A'), c('C614', '1n', 'FDB_INN', 'FDB_OUTP'))
ad.add(r('R611', '40.2', 'FDB_OUTN', 'ADC_R_N'), r('R612', '40.2', 'FDB_OUTP', 'ADC_R_P'))
ad.add(c('C615', '2.7n', 'ADC_R_P', 'ADC_R_N'), c('C616', '100p', 'ADC_R_P', 'GND'), c('C617', '100p', 'ADC_R_N', 'GND'))
ad.add(c('C618', '100n', '+5V', 'GND'))
SHEETS.append(ad)

# ===================================================================== 7 Analog in/out
an = Sheet('Analog In and Out', 'Analog In and Out.kicad_sch', 'Analog In and Out')
an.notes.append('Input buffer (U701A, OPA2365) and output stages (U702, OPA1688), the Timekeeper\'s ANALOG_FRONT on one 5 V rail biased at VCOM.\n'
                'U701 is an OPA2365 (zero-crossover rail-to-rail input) instead of the Timekeeper\'s OPA1656, whose input stops at (V+) - 2.25 V = 2.75 V on 5 V, '
                '0.25 V above the 2.5 V bias; hard-played guitar peaks reach about +/-1.5 V here. R705 is 49.9R, not 5k1 (Timekeeper review H2).\n'
                'In (left): 1M to ground at the relay, 100n film, 1M bias to VCOM_A, follower (R703 0R; R704 + C707 to VCOM_A, both DNP, set gain), 49.9R / 220p to the ADC driver.\nIn (right, from the IN ring): the same chain on U701B without the relay or gain option: 1M to ground, 100n film, 1M bias to VCOM_A, follower, 49.9R / 220p to the ADC driver.\n'
                'Out: unity-gain difference amplifier per channel (10k x4) referenced to VCOM_B, 10u out, 100R series, 1M pull-down.')
an.add(r('R701', '1M', 'EFFECT_IN', 'GND'))
an.add(Part('C701', C, '100n', C1206, {'1': 'EFFECT_IN', '2': 'IN_AC'}, note='film/C0G'))
an.add(r('R702', '1M', 'IN_AC', 'VCOM_A'))
an.add(Part('U701', OPAMP, 'OPA2365AIDR', SOIC8, {'3': 'IN_AC', '2': 'IN_FB', '1': 'IN_BUF_OUT'}, unit=1,
            props={'Manufacturer': 'Texas Instruments', 'Mfg Part #': 'OPA2365AIDR'}))
an.add(Part('U701', OPAMP, 'OPA2365AIDR', SOIC8, {'5': 'IN_AC_R', '6': 'IN_BUF_OUT_R', '7': 'IN_BUF_OUT_R'}, unit=2,
            props={'Manufacturer': 'Texas Instruments', 'Mfg Part #': 'OPA2365AIDR'}, note='right input follower'))
an.add(Part('U701', OPAMP, 'OPA2365AIDR', SOIC8, {'4': 'GND', '8': '+5V'}, unit=3,
            props={'Manufacturer': 'Texas Instruments', 'Mfg Part #': 'OPA2365AIDR'}))
an.add(r('R703', '0R', 'IN_BUF_OUT', 'IN_FB'), r('R704', '0R', 'IN_FB', 'IN_GAIN', dnp=True, note='gain option, DNP'), c('C707', '10u', 'IN_GAIN', 'VCOM_A', fp=C0805, dnp=True, note='gain option, DNP'))
an.add(r('R705', '49.9', 'IN_BUF_OUT', 'EFFECT_IN_BUF', note='isolates U701A from C702 + C601; was 5k1 (Timekeeper review H2)'), c('C702', '220p', 'EFFECT_IN_BUF', 'GND'))
an.add(r('R720', '1M', 'IN_R', 'GND'))
an.add(Part('C708', C, '100n', C1206, {'1': 'IN_R', '2': 'IN_AC_R'}, note='film/C0G'))
an.add(r('R721', '1M', 'IN_AC_R', 'VCOM_A'))
an.add(r('R722', '49.9', 'IN_BUF_OUT_R', 'EFFECT_IN_BUF_R', note='isolates U701B from C709 + C611'), c('C709', '220p', 'EFFECT_IN_BUF_R', 'GND'))
an.add(c('C703', '100n', '+5V', 'GND'))
for ch, base, unit, (pp, nn, oo) in (('L', 706, 1, ('3', '2', '1')), ('R', 714, 2, ('5', '6', '7'))):
    an.add(Part('U702', OPAMP, 'OPA1688IDR', SOIC8, {pp: 'OUT%s_P' % ch, nn: 'OUT%s_N' % ch, oo: 'OUT%s_AMP' % ch}, unit=unit,
                props={'Manufacturer': 'Texas Instruments', 'Mfg Part #': 'OPA1688IDR'}))
    an.add(r('R%d' % base, '10k', 'DAC_%s_P' % ch, 'OUT%s_P' % ch), r('R%d' % (base + 1), '10k', 'OUT%s_P' % ch, 'VCOM_B'))
    an.add(r('R%d' % (base + 2), '10k', 'DAC_%s_N' % ch, 'OUT%s_N' % ch), r('R%d' % (base + 3), '10k', 'OUT%s_N' % ch, 'OUT%s_AMP' % ch))
    an.add(cp('C%d' % (704 if ch == 'L' else 705), '10u', 'OUT%s_AMP' % ch, 'OUT%s_AC' % ch, TANT))
    an.add(r('R%d' % (base + 4), '100R', 'OUT%s_AC' % ch, 'EFFECT_OUT_%s' % ch), r('R%d' % (base + 5), '1M', 'EFFECT_OUT_%s' % ch, 'GND'))
an.add(Part('U702', OPAMP, 'OPA1688IDR', SOIC8, {'4': 'GND', '8': '+5V'}, unit=3,
            props={'Manufacturer': 'Texas Instruments', 'Mfg Part #': 'OPA1688IDR'}))
an.add(c('C706', '100n', '+5V', 'GND'))
SHEETS.append(an)
