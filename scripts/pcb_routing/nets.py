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


def kind(net):
    if net in GND:
        return 'GND'
    if net in RAILS:
        return 'RAIL'
    if net == 'VDDA' or net.startswith('/Power/'):
        return 'POWER'
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


# width, clearance (mm). The H750's and the codec's pins are 0.2 mm apart, so no class asks for more than 0.18.
WIDTH = {'GND': 0.4, 'RAIL': 0.5, 'POWER': 0.5, 'AUDIO': 0.254, 'DIGITAL': 0.2, 'CTRL': 0.2}
CLEAR = {'GND': 0.18, 'RAIL': 0.18, 'POWER': 0.18, 'AUDIO': 0.18, 'DIGITAL': 0.15, 'CTRL': 0.15}
WIDE = {'+9V': 0.6, '/Power/DC_IN': 0.8, '/Power/DC_F': 0.8, '/Power/SW': 0.8,
        '/Power/BUCK_FB': 0.25, '/Power/BUCK_FBT': 0.25, '/Power/BUCK_BOOT': 0.3,
        'VDDA': 0.3,
        '/MCU/NRST': 0.1016}    # escapes the SWD needle pads (0.48 mm between pads, all six in use)
VIA = (0.6, 0.3)


def is_drive(net):
    """Digital lines out to the bottom-side LED and relay drivers (long, routed after audio)."""
    return net in ('LED_EFFECT_DRV', 'LED_HOLD_DRV', 'RELAY_DRV') or \
        net.startswith(('/Jacks and Bypass/LED_EFF_G', '/Jacks and Bypass/LED_HOLD_G', '/Jacks and Bypass/RELAY_G'))


def width(net):
    return WIDE.get(net, WIDTH[kind(net)])
