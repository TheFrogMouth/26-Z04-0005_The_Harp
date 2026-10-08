"""The Harp top sheet: block diagram in the Frogmouth style (docs/schematic-standard.md section 4)."""
import os, re
from schgen import uid, POWER_NETS
from layout import oswald

RELIC_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '26-A03-0003_The_Relic', 'kicad', 'the_relic', 'The Relic.kicad_sch')
RED, GREEN, BLUE, GREY = (214, 39, 40), (0, 140, 0), (0, 90, 220), (90, 90, 90)
W, H = 45.72, 38.1


def _font(size, bold=False, color=None):
    b = '\n\t\t\t\t(bold yes)' if bold else ''
    c = '\n\t\t\t\t(color %d %d %d 1)' % color if color else ''
    return '(font\n\t\t\t\t(size %s %s)%s%s\n\t\t\t)' % (size, size, b, c)


def text(s, x, y, size=1.5, bold=False, color=None, justify='left bottom'):
    return ('\t(text "%s"\n\t\t(exclude_from_sim no)\n\t\t(at %s %s 0)\n\t\t(effects\n\t\t\t%s\n\t\t\t(justify %s)\n\t\t)\n\t\t(uuid "%s")\n\t)'
            % (s.replace('"', '\\"').replace('\n', '\\n'), x, y, _font(size, bold, color), justify, uid()))


def rect(x0, y0, x1, y1, color, width=0.3, dash=False, fill_alpha=0):
    fill = '(fill\n\t\t\t(type none)\n\t\t)' if not fill_alpha else '(fill\n\t\t\t(type color)\n\t\t\t(color %d %d %d %s)\n\t\t)' % (color + (fill_alpha,))
    return ('\t(rectangle\n\t\t(start %s %s)\n\t\t(end %s %s)\n\t\t(stroke\n\t\t\t(width %s)\n\t\t\t(type %s)\n\t\t\t(color %d %d %d 1)\n\t\t)\n\t\t%s\n\t\t(uuid "%s")\n\t)'
            % (x0, y0, x1, y1, width, 'dash' if dash else 'solid', color[0], color[1], color[2], fill, uid()))


def poly(pts, color, width=0.6):
    xy = ' '.join('(xy %s %s)' % p for p in pts)
    return ('\t(polyline\n\t\t(pts\n\t\t\t%s\n\t\t)\n\t\t(stroke\n\t\t\t(width %s)\n\t\t\t(type default)\n\t\t\t(color %d %d %d 1)\n\t\t)\n\t\t(fill\n\t\t\t(type none)\n\t\t)\n\t\t(uuid "%s")\n\t)'
            % (xy, width, color[0], color[1], color[2], uid()))


def arrow(tip, dir, color):
    x, y = tip
    s = 1.524
    if dir == 'right':
        pts = [(x - s, y - s * 0.58), (x, y), (x - s, y + s * 0.58)]
    elif dir == 'left':
        pts = [(x + s, y - s * 0.58), (x, y), (x + s, y + s * 0.58)]
    elif dir == 'up':
        pts = [(x - s * 0.58, y + s), (x, y), (x + s * 0.58, y + s)]
    else:
        pts = [(x - s * 0.58, y - s), (x, y), (x + s * 0.58, y - s)]
    return poly([(round(a, 3), round(b, 3)) for a, b in pts], color)


def line(pts, color, arrows=(), label=None, label_at=None, label_justify='left bottom', label_size=1.27):
    out = [poly(pts, color)]
    for which in arrows:
        if which == 'end':
            a, b = pts[-2], pts[-1]
        else:
            a, b = pts[1], pts[0]
        if b[0] > a[0]:
            d = 'right'
        elif b[0] < a[0]:
            d = 'left'
        elif b[1] < a[1]:
            d = 'up'
        else:
            d = 'down'
        out.append(arrow(b, d, color))
    if label:
        lx, ly = label_at or ((pts[0][0] + pts[1][0]) / 2, pts[0][1] - 0.8)
        out.append(text(label, lx, ly, label_size, color=color, justify=label_justify))
    return out


def sheet_block(sh, x, y, color, summary, page, w=W, h=H, root_uuid=None, project='The Harp'):
    return ('\t(sheet\n\t\t(at %s %s)\n\t\t(size %s %s)\n\t\t(exclude_from_sim no)\n\t\t(in_bom yes)\n\t\t(on_board yes)\n\t\t(dnp no)\n'
            '\t\t(fields_autoplaced yes)\n\t\t(stroke\n\t\t\t(width 0.3)\n\t\t\t(type solid)\n\t\t\t(color %d %d %d 1)\n\t\t)\n\t\t(fill\n\t\t\t(color %d %d %d 0.08)\n\t\t)\n'
            '\t\t(uuid "%s")\n'
            '\t\t(property "Sheetname" "%s"\n\t\t\t(at %s %s 0)\n\t\t\t(show_name no)\n\t\t\t(do_not_autoplace no)\n\t\t\t(effects\n\t\t\t\t%s\n\t\t\t\t(justify left bottom)\n\t\t\t)\n\t\t)\n'
            '\t\t(property "Sheetfile" "%s"\n\t\t\t(at %s %s 0)\n\t\t\t(show_name no)\n\t\t\t(do_not_autoplace no)\n\t\t\t(effects\n\t\t\t\t%s\n\t\t\t\t(justify left top)\n\t\t\t)\n\t\t)\n'
            '\t\t(instances\n\t\t\t(project "%s"\n\t\t\t\t(path "/%s"\n\t\t\t\t\t(page "%d")\n\t\t\t\t)\n\t\t\t)\n\t\t)\n\t)'
            % (x, y, w, h, color[0], color[1], color[2], color[0], color[1], color[2], sh.uuid,
               sh.name, x, round(y - 0.762, 3), _font(2.032, True), sh.fname, x, round(y + h + 0.762, 3), _font(1.27, False, (110, 110, 110)),
               project, root_uuid, page),
            text(summary, round(x + 2, 3), round(y + 5, 3), 1.5, justify='left top'))


def embedded_files():
    t = open(RELIC_ROOT).read()
    i = t.index('\t(embedded_files')
    blk = t[i:]
    # take up to the end of the embedded_files block (bracket balanced, data as one token)
    depth, j, n = 0, i, len(t)
    while j < n:
        c = t[j]
        if c == '|':
            j = t.index('|', j + 1) + 1
            continue
        if c == '"':
            j += 1
            while t[j] != '"':
                j += 2 if t[j] == '\\' else 1
        elif c == '(':
            depth += 1
        elif c == ')':
            depth -= 1
            if depth == 0:
                return t[i:j + 1]
        j += 1
    raise SystemExit('embedded_files block not closed')


def build(sheets, root_uuid, project='The Harp'):
    S = {s.name: s for s in sheets}
    pages = {s.name: i + 2 for i, s in enumerate(sheets)}
    body = []
    # ---- header
    body.append(text('THE HARP  26-Z04-0005  SYMPATHETIC-STRING DIGITAL PEDAL', 20.32, 40.64, 3.5, True, (40, 40, 40)))
    body.append(text('One four-layer main board in a Hammond 125B on the Alchemist / Relic grid; pots, toggles, LEDs and jacks board-mounted.\n'
                     'Signal: IN -> K401 relay bypass -> 1M / 100n -> OPA2365 buffer -> THS4522 ADC driver -> AK4621 ADC -> STM32H750VBT6 (SAI1) -> '
                     'AK4621 DAC -> OPA1688 difference amps -> OUT L (through K401) and OUT R.\n'
                     'Design notes: docs/design-brief.md, docs/pcb-plan.md. The schematic is written by scripts/harp_schematic/build_layout.py from harp_spec.py '
                     'and the layouts in layouts/; after the first edit in KiCad the KiCad files are the source of truth.',
                     20.32, 44, 1.5, justify='left top'))
    # ---- frames
    body.append(rect(22, 58, 285, 128, GREY, dash=True))
    body.append(text('AUDIO / ANALOG', 25, 64.5, 3.5, justify='left bottom'))
    body.append(rect(22, 150, 88, 228, GREY, dash=True))
    body.append(text('POWER', 25, 156.5, 3.5, justify='left bottom'))
    body.append(rect(212, 150, 365, 228, GREY, dash=True))
    body.append(text('CONTROL / DIGITAL', 215, 156.5, 3.5, justify='left bottom'))
    # ---- sheet blocks
    blocks = [
        ('Jacks and Bypass', 30, 78, GREEN, 'IN (TRS), OUT L, OUT R, EXP jacks (J402-J406)\nK401 relay true bypass, Q401 driver\nEffect / Hold LEDs, footswitch pads\nMCP6001 expression buffer'),
        ('Analog In and Out', 95, 78, GREEN, 'U701A/B OPA2365 L and R input buffers\n1M / 100n in, 49.9R / 220p out\nU702 OPA1688 difference amps\n10u out, 100R, 1M'),
        ('ADC Driver', 160, 78, GREEN, 'U601 THS4522 channel A (L), B (R)\nsingle-ended to differential\ngain 0.59, 40.2R / 2.7n filter'),
        ('Codec', 225, 78, GREEN, 'IC501 AK4621EF\nstereo in, stereo out\nU501 OPA2348 VCOM buffers\n-> VCOM_A, VCOM_B'),
        ('MCU', 225, 168, BLUE, 'U201 STM32H750VBT6\nSAI1 to the codec, QSPI flash U202\nHSE 25 MHz, SWD needle pads W201'),
        ('Controls and LEDs', 300, 168, BLUE, 'RV101-RV105 B10K pots, 1k / 100n\nSW101-SW103 ON-ON-ON toggles\nJ408 0.91 in OLED, I2C pull-ups'),
        ('Power', 30, 168, RED, 'J401 9 V DC in, SMAJ10CA, PMEG3010\nU301 TPS54202 buck -> +3V3\nU302 NCP718 LDO -> +5V'),
    ]
    for name, x, y, col, summ in blocks:
        body.extend(sheet_block(S[name], x, y, col, summ, pages[name], root_uuid=root_uuid, project=project))
    # ---- audio path (green)
    body += line([(75.72, 88), (95, 88)], GREEN, ['end'], 'EFFECT_IN', (76.5, 87))
    body += line([(140.72, 88), (160, 88)], GREEN, ['end'], 'EFFECT_IN_BUF', (141.5, 87))
    body += line([(205.72, 88), (225, 88)], GREEN, ['end'], 'ADC_L_P/N, ADC_R_P/N', (206.5, 87))
    body += line([(248, 116.1), (248, 122), (130, 122), (130, 116.1)], GREEN, ['end'], 'DAC_L_P/N, DAC_R_P/N  (codec DAC to the output stages)', (135, 123), 'left top')
    body += line([(95, 104), (75.72, 104)], GREEN, ['end'], 'EFFECT_OUT_L, EFFECT_OUT_R', (76.5, 103))
    # ---- bias (red) from the codec VCOM buffers
    body += line([(238, 116.1), (238, 119), (120, 119), (120, 116.1)], RED, ['end'], 'VCOM_A, VCOM_B  (codec bias to the input buffer, ADC driver and output stages)', (182, 118.2))
    body += line([(176, 119), (176, 116.1)], RED, ['end'])
    # ---- MCU control (blue)
    body += line([(262, 168), (262, 116.1)], BLUE, ['end', 'start'], 'CODEC_MCLK, LRCK, BICK, SDTI, SDTO\nCODEC_CCLK, CDTI, CSN, PDN', (263.5, 136), 'left bottom')
    body += line([(300, 182), (270.72, 182)], BLUE, ['end'], 'POT1, POT2, POT3, POT5 / TOG1-3 A, B', (271.5, 181))
    body += line([(270.72, 196), (300, 196)], BLUE, ['end'], 'OLED_SCL, OLED_SDA  (I2C to the OLED)', (271.5, 195))
    body += line([(225, 176), (206, 176), (206, 136), (56, 136), (56, 116.1)], BLUE, ['end'], 'RELAY_DRV, LED_EFFECT_DRV, LED_HOLD_DRV', (60, 135))
    body += line([(62, 116.1), (62, 140), (202, 140), (202, 182), (225, 182)], BLUE, ['end'], 'FSW_BYPASS_IN, FSW_HOLD_IN, EXP', (120, 139), 'left top')
    body[-2:] = body[-2:]
    # ---- supply rails (red): one line from the Power block, a short line into each sheet
    body += line([(40, 168), (40, 145), (18, 145), (18, 72), (295, 72), (295, 160), (262.5, 160), (262.5, 168)], RED, ['end'], '+9V, +5V, +3V3 from Power', (41, 150), 'left bottom')
    body += line([(295, 160), (322, 160), (322, 168)], RED, ['end'])
    for x, lbl in ((52, '+9V, +3V3'), (118, '+5V'), (182, '+5V'), (248, '+5V, +3V3')):
        body += line([(x, 72), (x, 78)], RED, ['end'], lbl, (x + 1, 77), 'left bottom')
    body.append(text('+3V3', 263.5, 167, 1.27, color=RED))
    body.append(text('+3V3', 323, 167, 1.27, color=RED))
    # ---- legend
    body.append(text('CONNECTIONS', 20.32, 245, 2.0, True))
    for i, (col, name) in enumerate(((GREEN, 'Audio signal'), (BLUE, 'MCU control'), (RED, 'Supply rails and bias'))):
        y = 250 + i * 5
        body.append(poly([(20.32, y), (40, y)], col))
        body.append(text(name, 43, y + 0.6, 1.5, color=col))
    body.append(text('Drawing only: the sheets connect through global labels of the same names.\n'
                     'Arrows point from the sheet that drives a net to the sheet that uses it; a line with a name list carries one label per name.',
                     20.32, 272, 1.27))
    hdr = ('(kicad_sch\n\t(version 20260306)\n\t(generator "eeschema")\n\t(generator_version "10.0")\n\t(uuid "%s")\n\t(paper "A3")\n'
           '\t(title_block\n\t\t(title "The Harp")\n\t\t(rev "A")\n\t\t(company "The Frogmouth")\n\t)\n\t(lib_symbols)\n' % root_uuid)
    tail = '\t(sheet_instances\n\t\t(path "/"\n\t\t\t(page "1")\n\t\t)\n\t)\n\t(embedded_fonts yes)\n%s\n)\n' % embedded_files()
    return oswald(hdr + '\n'.join(body) + '\n') + tail
