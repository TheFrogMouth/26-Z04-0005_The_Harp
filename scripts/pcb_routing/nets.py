"""Net classes for routing: what each net is and how wide it is routed.

GND     the In1.Cu plane; every SMD pad gets its own via to it
RAIL    +3V3, +5V, +9V: every SMD pad gets its own via, the rail itself runs on In2.Cu
POWER   local power nets (buck, LDO, DC input, VDDA, relay coil, LED current): wide, F/B
AUDIO   the analog signal path (jacks, buffers, ADC driver, codec analog side, VCOM)
DIGITAL MCU, flash, codec digital interface, SWD, OLED, LED/relay drive
CTRL    slow analog control voltages into the MCU (pots, expression)
"""
GND = {'GND'}
RAILS = {'+3V3', '+5V', '+9V'}


# KiCad's own names for the unlabelled local nets (after Update PCB from Schematic)
LOCAL_POWER = {'Net-(U301-SW)', 'Net-(U301-FB)', 'Net-(U301-BOOT)', 'Net-(R301-Pad2)', 'Net-(D301-A2)',
               'Net-(D302-A)', 'Net-(U302-EN)', 'Net-(U302-OUT)'}


def kind(net):
    if net in GND:
        return 'GND'
    if net in RAILS:
        return 'RAIL'
    if net == 'VDDA' or net.startswith('/Power/') or net in LOCAL_POWER:
        return 'POWER'
    if net.startswith(('Net-(U201-', 'Net-(U202-', 'Net-(IC501-PDN)', 'Net-(U203-', 'Net-(Y201-', 'Net-(J201-', 'Net-(W201-')):
        return 'DIGITAL'
    if net in ('/Jacks and Bypass/RELAY_COIL', '/Jacks and Bypass/RELAY_LOW',
               '/Jacks and Bypass/LED_EFF_K', '/Jacks and Bypass/LED_HOLD_K',
               '/Jacks and Bypass/LED_EFF_LOW', '/Jacks and Bypass/LED_HOLD_LOW'):
        return 'POWER'      # coil and LED currents
    if net.startswith(('POT', 'TOG', 'FSW_', '/Controls and LEDs/')) or net == 'EXP' \
            or net.startswith('/Jacks and Bypass/EXP_') or net.startswith('/Jacks and Bypass/FSW_'):
        return 'CTRL'
    if net.startswith(('CODEC_', '/MCU/', 'OLED_', 'LED_', 'RELAY_')) or net == '/Codec/PDN' \
            or net.startswith(('/Jacks and Bypass/LED_', '/Jacks and Bypass/RELAY_')):
        return 'DIGITAL'
    return 'AUDIO'


# width, clearance (mm): the Alchemist's set, 0.254 / 0.508 / 0.762 / 1.0 and 0.1524 everywhere
WIDTH = {'GND': 0.508, 'RAIL': 0.762, 'POWER': 0.762, 'AUDIO': 0.254, 'DIGITAL': 0.2, 'CTRL': 0.254}   # digital 0.2: passes between the MCU's 0.5 mm pads
CLEAR = {'GND': 0.1524, 'RAIL': 0.1524, 'POWER': 0.1524, 'AUDIO': 0.1524, 'DIGITAL': 0.1524, 'CTRL': 0.1524}
WIDE = {'Net-(D301-A2)': 1.0, 'Net-(D302-A)': 1.0, 'Net-(U301-SW)': 1.0,         # DC input and the buck's SW node
        'Net-(U301-FB)': 0.254, 'Net-(R301-Pad2)': 0.254, 'Net-(U301-BOOT)': 0.254,
        'VDDA': 0.508,
        'Net-(U201-NRST)': 0.1016}    # escapes the SWD needle pads (0.48 mm between pads, all six in use)
VIA = (0.6, 0.3)


def is_drive(net):
    """Digital lines out to the bottom-side LED and relay drivers (long, routed after audio)."""
    return net in ('LED_EFFECT_DRV', 'LED_HOLD_DRV', 'RELAY_DRV') or \
        net.startswith(('/Jacks and Bypass/LED_EFF_G', '/Jacks and Bypass/LED_HOLD_G', '/Jacks and Bypass/RELAY_G'))


def width(net):
    return WIDE.get(net, WIDTH[kind(net)])
