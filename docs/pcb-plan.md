# The Harp — schematic and PCB plan

2026-10-04, updated 2026-10-08 (schematic drawn, board synced and placed, see *Placement*). Companion to
`design-brief.md`. The starting point is The Relic's KiCad project
(`26-A03-0003_The_Relic/kicad/the_relic/`) for the board, the face guides,
the jacks, the pots and the relay bypass, and the Timekeeper's DSP board
(`25-Z01-0001_DSP_Development_Board/kicad/dsp_board/`) for the
MCU, codec, flash and power sheets.

## One board or two

The jacks decide it. The Alchemist and The Relic mount the four 1/4" jacks
and the DC jack on the **underside of the pot board**, so the wall-hole
heights are set by the board depth under the face (about 10–12 mm on the
pot bushings) plus the jack's axis height. To put The Harp's jacks at the
same positions **and heights**, they must sit on a board hanging at that
same depth, and that is the board the pots are on. So:

- **Plan A, one board (default).** The Alchemist/Relic 56 × 90 mm outline
  with the DC tab, four layers, pots, toggles, LEDs, jacks, relay, analog
  and the whole digital section on it. This is what the rest of this
  document plans.
- **Plan B, fallback.** If the parts do not fit, keep a *face board* with
  everything that touches the enclosure (pots, toggles, LEDs, jacks, DC,
  relay, input and output buffers) and move the H750, flash, codec and
  power onto a *DSP board* below it, joined by a 24-way 1.0 mm FFC as the
  Timekeeper's two boards are. The face board stays exactly the Relic's
  outline, so jacks and pots do not move. This costs a second PCB, two FFC
  connectors and the cable (about 3 EUR at 100 after the Relic's figures),
  and about 8 mm more depth, which the 125B has.

### Does Plan A fit? Estimate

| Section | Parts (approx.) | Source |
|---|---|---|
| H750VBT6, decoupling, crystal, NRST, BOOT0, SWD pads | 25 | Timekeeper U201 group, fewer VDD pins |
| W25Q128 QSPI flash | 3 | Timekeeper U901 |
| Power: TVS, series Schottky, buck TPS54202 (3.3 V), LDO NCP718 (5 VA), filters | 22 | Timekeeper U301/U302 |
| AK4621EF codec, reference buffer OPA2348, 2 × THS4522 DFA, passives | 55 | Timekeeper IC401, U401, U501, U601 |
| Input buffer OPA2365 + anti-alias, expression buffer MCP6001, ESD | 20 | Timekeeper U801, U702 |
| Output buffers OPA1688 L/R + reconstruction, ESD | 18 | Timekeeper U802 |
| Relay bypass: G6K-2F-Y, 2N7002 ×2, diode, resistors, RC on the footswitch inputs | 12 | Relic K401 group, Alchemist relay |
| 4 pots, 3 toggles, 2 LEDs, OLED connector and pull-ups | 22 | Alchemist + new |
| 5 jacks, 2 footswitch pad pairs | 7 | Alchemist |
| **Total** | **≈ 191** | |

The Relic places 120 parts on this outline with room to spare in the
digital zone; the Timekeeper's DSP board carries 145 (with SDRAM and a
144-pin MCU) on a larger board. About 190 parts, most of them 0402/0603
and the LQFP-100 at 14 × 14 mm, on 56 × 90 mm minus the DC tab is **tight
but expected to fit**, because SMD parts may sit over the jack bodies
(Relic rule) and the four-layer stack keeps the routing off the top. The
go/no-go is the placement step below; if the codec and MCU groups cannot
be zoned apart from the input buffer with the LEDs in place, go to Plan B
rather than squeeze.

## Enclosure and datum

Taken unchanged from The Relic (`docs/main-board-placement.md`):

- Tayda 125B, face 64.7 × 119.8, cavity 60.3 × 115.4, corner bosses
  avoided. Nominal until a casting is measured.
- Datum: enclosure centre = PCB (148.5, 105), face X right, face Y up;
  drill/place origin and grid origin there.
- Board: 56 × 90 mm, R2, face X ±28, Y +52 to −38, 18 mm tab to +56.5 under
  the DC jack. Top side components only, except the jacks; through-hole
  parts only where no jack body is underneath; SMD over the jack bodies is
  allowed.

## Face schedule

One face standard for The Alchemist, The Relic and The Harp: every
position below is a shared Tayda drill coordinate, and each pedal uses
the subset it needs.

| Position (face X, Y) | Alchemist | Relic | Harp |
|---|---|---|---|
| Knob row +38: (−20), (0), (+20) | Rate, Depth, Wave | Wow, Flutter, Age | RV101 Mix, RV102 Sustain, RV103 Strings |
| Knob row +13: (−20), (0), (+20) | Mode toggle, Exp/offset pot, Resonance toggle | Saturation, Mix, Hiss | SW101 Tuning toggle, RV105 Jawari, SW103 Brightness toggle |
| Toggle row −5: (−20), (0), (+20) | — | Dropout, Age range, Hiss on | none: the OLED window takes the centre (option 1, 2026-10-09) |
| Centre (0, −24) | — | — | SW102 Retune toggle (moved down from (0, −5) on 2026-10-09) |
| Right wall, lower jack, axis Y −22.5 | IN | IN | J402 IN |
| Right wall, upper jack, axis Y −3.5 | Expression | — | J406 EXP |
| Left wall, lower jack, axis Y −22.5 | OUT | OUT | J403 OUT L |
| Left wall, upper jack, axis Y −3.5 | Sync | — | J404 OUT R |
| Top wall DC, X 0 | DC | DC | J401 DC |
| LEDs (−20, −35), (+20, −35) | Effect, Rate | Effect, — | D113 Effect, D114 Hold |
| Footswitches (−20, −49), (+20, −49) | Bypass, Tap | Bypass, — | Bypass (J405), Hold (J407) |
| OLED window (0, −5) | — | — | 24.4 × 7.6 mm rectangular cut for the 0.91 in OLED; module on J408 (see *OLED mounting*) |

**Controls over the upper jacks (resolved 2026-10-06).** The upper jack
bodies sit on the underside at face X ±6.5 to ±30, Y +5.6 to −12.6, with
their rear pin row at Y +4.6. The first face (The Relic's six knobs and
three toggles) did not fit them: the outer lower-row pots RV104/RV106 had
their pins at Y +5.5, on the jacks' rear pads, and the outer toggles at
(±20, −5) put their pins over the jack bodies. The Harp now follows The
Alchemist (design brief, decision 13): the outer positions of the +13 row
carry the Tuning and Brightness toggles, whose pins start at Y +8.3, 1.3 mm
clear of the bodies; Jawari is the only knob in that row, at X 0 where
there is no jack body; the Retune toggle uses the Taiway footprint, pins
within X ±2.4, about 2.7 mm clear of the jack bodies (it moved from
(0, −5) to (0, −24) on 2026-10-09, still in the centre between the jacks). No through-hole pad sits
over a jack. All three toggles are Taiway 100-DP6-T200B1M2QE ON-ON-ON on The
Alchemist's `100DP3T1B2M2QE` footprint (shaft at origin + (−2.415, +4.7)).

## OLED mounting (2026-10-08)

![Face cut-out with the OLED window](images/oled-face-cutout.png)

![OLED module against the PCB: top view and section on X = 0](images/oled-pcb-relation.png)

Drawings generated by `scripts/oled_drawings/oled_drawings.py` from the
figures below and the footprint courtyards in `The Harp.kicad_pcb`.

- **Module.** A 0.91 in 128 × 32 SSD1306 I²C module, 4 pads (GND, VCC,
  SCL, SDA) on one short end, run from +3V3. Envelope 36–38 × 12–12.5 mm
  (Waveshare 36 × 12.5; generic boards up to 38 × 12); glass 30 × 11.5 ×
  1.45 mm; active area 22.384 × 5.584 mm. The SSD1306 and its charge pump
  are on the module, so the PCB carries only J408, the pull-ups and C104.
- **Window.** 24.4 × 7.6 mm, R0.5, centred at face (0, −5), a Tayda
  rectangular cut: the active area plus a 1 mm border. 8.0 mm below the edge
  of the Jawari knob (12.5 mm knob at (0, +13)), 11.9 mm above the Retune
  toggle hole, 17.9 mm from the cavity wall each side.
- **Why (0, −5) (option 1, 2026-10-09).** The first position, (0, −20), put
  the screen near the footswitches. At (0, −5) it sits in the middle of the
  face, under the Jawari knob and closer to eye line. The Retune toggle that
  was there moved down to (0, −24), and the MCU moved up into the space it
  left (*Placement*). The module spans Y +1.25 to −11.25, 5.7 mm clear of
  the toggle's body below it.
- **Fixing.** The module hangs from the face, not from the PCB. A small
  3D-printed carrier (a pocket for the module with a lip round the glass,
  as the Timekeeper's TFT frame) is bonded to the inside of the face with
  VHB tape and registered on the window edges; a 0.5 mm foam gasket
  between the glass and the face keeps dust out. Fallback: VHB foam on the
  glass rim straight onto the face. It is not screwed to the PCB because
  the lower jack bodies sit under the board at |X| > 6.5 (screws from below
  would hit them) and the MCU fills the middle; hanging it from the face
  also keeps the board-depth tolerance out of the glass position.
- **Wiring.** The module's pin header is left off. Four wires (28–30 AWG,
  about 40 mm with slack) run from its pads to J408, a JST SH 4-way
  (SM04B-SRSS-TB) on the top side at PCB (170.5, 108.5), rotation 270°,
  face (22.0, −3.5), cable entry facing −X towards the module. The module
  is mounted turned round, pads at its right-hand end (the codec sits at
  the left end), so the firmware flips the image (SSD1306 segment and COM
  remap). Courtyard X 18.72 to 25.28, Y −7.4 to +0.4: between the two pin
  rows of the right upper jack, 2.7 mm from the board edge, over the jack
  body where SMD parts are allowed. Mounting pads (MP) have no net. Pin 1 GND, 2 +3V3, 3 SCL,
  4 SDA. The PCB lifts out with the face, so the lead never has to be
  unplugged to open the box.
- **Heights.** Face 2.2 mm; below it the gasket 0.5, glass 1.45, module PCB
  1.0 and its parts about 1.2: the module hangs 4.15 mm, leaving 6.85 mm to
  the PCB at the provisional 11 mm face-to-PCB depth (10–12 mm).
- **Under the module.** After the placement (*Placement*, below) only flat
  parts sit under the module: U201 (1.6 mm, 5.25 mm clear at an 11 mm
  depth), its decoupling and part of the codec IC501. The relay K401 is on the bottom side
  and the electrolytics C502/C508 (5.8 mm) were kept out of the module's
  outline by the placer. Anything added there later must stay below about 6.8 mm.
- **Still to check.** Measure the bought module (pad end, glass position
  on its board, thickness) and the casting depth, then confirm the window
  centre lies on the active area and the carrier height.

## Zoning (top side, face coordinates)

Updated for option 1 (2026-10-09); *Placement* below has the drawing.

```
 Y +52 ─────────────────────────────────────────  DC tab: TVS, Schottky, buck (U301) and its inductor; LDO right
       │ RV101        RV102        RV103        │  row +38; buck output filter between the pots
       │ output stage U702 │ VCOM U501 │ bulk caps │  between the pot rows
       │ SW101        RV105        SW103        │  row +13
       │ codec IC501 │ OLED (0, −5) │ J408       │  module hangs from the face; MCU U201 under it at (0, −7)
       │ ADC driver  │ SW102 (0,−24)│ flash, IN  │  lower band: ADC driver left, input buffers and flash right
       │ D113 (−35)                    D114      │
 Y −38 ─────────────────────────────────────────  bottom side: relay under U201, LED drivers along the heel
```

Signal runs right to left as on the Alchemist: IN and EXP enter on the
**right** wall, OUT L/R leave on the **left**. So the input and expression
buffers sit at the right-hand end of the lower band next to J402/J406, the
output buffers and the relay at the left-hand end next to J403/J404, and
the H750 with the flash in the middle. The relay takes the Relic's K401
position (the Alchemist's old FFC spot).

Rules carried over from The Relic:

- Parts on both sides since 2026-10-08 (*Placement*); the bottom only where
  the jack bodies are not.
- Four layers, F.Cu signals and parts / In1.Cu solid GND, never cut /
  In2.Cu power (+9V, +3V3, +3V3A, +5VA) / B.Cu longer signals and the jacks.
- Every SMD GND pad gets its own via to In1.Cu; through-hole parts use their
  barrels. No via under the SWD needle pads.
- Analog and digital separated by placement, not by a split plane: the
  codec's analog side, the input buffer and the output buffers face the
  jacks; the MCU, flash and buck are kept to the centre and the DC end.
  Digital tracks (QSPI, SAI, SWD) stay inside the MCU zone.
- The buck converter and its inductor live on the DC tab, as far from the
  input buffer as the board allows; its switching node is kept off B.Cu over
  the jack bodies.

## Placement (option 1, 2026-10-09)

![Placement, top and bottom](images/pcb-placement.png)

All 181 footprints are placed, by script (`scripts/pcb_placement/`, see its
README), not in KiCad. Checked from the board file: no courtyard overlaps
on either side (apart from the stacked jacks, as on The Alchemist),
nothing on a through-hole from the other side, everything inside the
outline, nothing taller than about 4 mm under the OLED module, and every
footprint's pads where the placer put them. Parts sit on a 0.5 mm grid;
within each group like parts share an orientation and line up in rows
and columns where the space allows. Top-side courtyards cover about 59 %.

**Option 1.** The OLED window moved up to (0, −5) and the Retune toggle
down to (0, −24). With the toggle out of the middle, the H750 (17.5 mm
courtyard) moved up from (0, −21.5) to (0, −7), under the screen, 1.2 mm
clear of the Jawari pot and of the toggle. The rest was arranged round it:

| Top side | Where |
|---|---|
| H750 U201 and its decoupling, crystal | (0, −7), under the OLED, caps in columns along its sides |
| Codec IC501 and its decoupling | Left middle (−18, −4), next to the MCU's SAI pins; anti-alias caps at its input pins |
| ADC driver U601 (L and R) | Lower left (−17, −26), below the codec |
| Input buffers U701, input ESD | Lower right (20, −24), next to IN |
| Flash U202 | Lower right (12.5, −21), next to the QSPI pins |
| Output stages U702 | Between the pot rows, left (−18.5, 24) |
| VCOM buffers U501, bulk caps C502/C508 | Between the pot rows, centre and right |
| J408 (OLED) | (22, −3.5), at the module's right (pad) end |
| Buck, LDO | Top band either side of the DC jack |

| Bottom side | Where |
|---|---|
| Relay K401 and its driver | Centre strip under U201, (0, −8) |
| LED and footswitch drivers | Heel strip and centre strip |
| Expression buffer | Above the right upper jack |
| Pot RC filters | Centre strip, near the MCU's ADC pins |
| SWD pads W201, footswitch pads J405/J407 | Above the upper jacks (bare copper) |

Net lengths (half-perimeter of each net's pads, mm), 2026-10-08 → option 1:

| Net | 10-08 | Option 1 |
|---|---:|---:|
| SAI (MCLK, BICK, LRCK, SDTI, SDTO) | 15–17 | 11–16 |
| ADC driver to codec, L / R | 46–58 / 46–58 | 17–19 / 35–38 |
| ADC driver feedback (worst net) | 19 | 22 |
| Input buffer to ADC driver L / R | 16 / 12 | 26 / 32 |
| Codec DAC to output stage L / R | 5 / 17 | 5 / 24 |
| IN (jack to relay) | 28 | 44 |
| QSPI | 11 | 25 |

What option 1 costs: the relay can no longer sit low in the centre strip
(the Retune toggle's pins are there), so IN runs 44 mm from the jack to the
relay on the bottom, and the buffered input crosses under the toggle to the
ADC driver. Both are routable: IN on B.Cu next to the In2 plane is the
bypass path as before, and the buffer output is low impedance. In return
the codec sits next to the MCU and the ADC driver, so the left-channel ADC
pair is short and the SAI is the shortest it has been.

**Assembly.** Bottom-side parts (37, all 0603/0805, SOT-23 and the SMD
relay) need JLCPCB double-sided assembly or hand fitting; W201, J405 and
J407 are bare copper.

**Verdict.** Plan A fits. Before routing: ERC, *Update PCB from Schematic*
(expect net renames only), a look over the placement in KiCad, and DRC
(including the five face parts whose courtyards reach over jack pins, as
before).

## Routing (first pass, scripted, 2026-10-09)

![Routing, F.Cu, B.Cu and In2.Cu](images/pcb-routing.png)

Routed without KiCad by `scripts/pcb_routing/` (see its README): Freerouting
2.4.1, one net class at a time, each phase fixed before the next.

| Layer | Carries |
|---|---|
| F.Cu | Parts, short signals, the local power nets |
| In1.Cu | Solid GND (the zone; fill it in KiCad). Every SMD GND pad has its own via to it (106) |
| In2.Cu | The rails only, +3V3, +5V and +9V (0.762 mm); every SMD rail pad has its own via down to it. No signal uses In2 |
| B.Cu | Longer signals, the bypass paths to the relay, the bottom-side drivers |

Analog and digital: each point of F.Cu and B.Cu is worked out as audio,
digital or neutral from the nearest pads of each kind (a region reaches 5 mm
from its SMD pads, 1.5 mm from through-hole pins, with a 0.75 mm neutral
band). Audio tracks were kept out of the digital region and digital and
control tracks out of the audio region; under the MCU the bypass audio runs
on B.Cu with the In1 plane between it and the MCU. Vias cost more than
Freerouting's default, so most signals change side at most once; the price
is some long one-sided detours on B.Cu.

Order: GND fanout, rails, local power, digital round the MCU, audio, the LED
and relay drive lines, control (pots, toggles, footswitches, expression),
then a repair pass with the region keepouts lifted and the signal tracks
free to move.

**Result:** 1546 tracks, 302 vias; the scripted check (connectivity with GND
through the plane, clearances, 0.5 mm to the edge, 0.254 mm hole to hole)
finds no violations. 32 connections in 28 nets were left open.

### Power section and widths (2026-10-10)

The board has since been opened in KiCad (it is the source of truth now; the
unlabelled local nets carry KiCad's `Net-(...)` names). The buck was
re-placed by hand (U301, C305, C304, L301, C306, C307), and the rest of the
power section was re-placed and re-routed by `scripts/pcb_routing/power.py`:

- **DC input**, one bus at y = 56 from the jack pin: D301 (TVS) hangs off it,
  FB301 with C301 and C302 under its two pads, D302, then +9V straight down
  to the LDO and onto In2 (1.0 mm on F.Cu).
- **+5V LDO**, a second row at y = 63 flowing back towards the +5V via, in
  order: FB302, C308 and C309, U302 (input pins facing right), C310 and
  C311, FB303, C312. The Alchemist's U201 pattern: a cap 2.5 mm each side.
- **Buck feedback** R301–R303 in a column beside the FB pin instead of 6–10 mm
  below the chip; the SW node to the BOOT cap crosses under the chip on a
  short B.Cu link rather than on In2.
- **+5V** reaches the rest of the board on In2 (`rail.py`), hopping the +3V3
  and +9V In2 rails with two short via pairs.

**Widths** are the Alchemist's four, applied board-wide by `widths.py`:
1.0 mm (DC input, SW), 0.762 (rails, local power), 0.508 (GND stubs, VDDA),
0.254 (audio, control), 0.2 (digital, since 2026-10-10 evening: nothing on
the board needs 0.254 for a logic line and 0.2 passes between the MCU's
0.5 mm pads; NRST 0.1016 through the SWD needle pads), clearance 0.1524
everywhere. A track that could not be widened to its class steps down one
size (144 did). Every segment is at 0, 45 or 90 degrees (127 re-drawn). The
KiCad net classes carry the same values.

**Now:** 1623 tracks, 294 vias, no violations in the scripted check; **29
connections in 26 nets still open**, all signals bar VDDA:

| Class | Open |
|---|---|
| Control (15) | POT1, POT2, POT3, POT2_W (`Net-(R102-Pad1)`), POT3_W (`Net-(R103-Pad1)`), TOG1_A, TOG1_B, TOG2_B, TOG3_A, TOG3_B, EXP, EXP_RING (`Net-(J406-PadR)`), FSW_BYPASS (`Net-(J405-Pin_1)`), FSW_BYPASS_IN, FSW_HOLD_IN |
| Digital (7) | HSE_OUT (`Net-(U201-PH1)`), NRST (2), CODEC_BICK, CODEC_CCLK, LED_EFFECT_DRV, LED_HOLD_DRV, LED_HOLD_G (`Net-(Q403-G)`) |
| Audio (3) | OUT_L (`Net-(D404-A2)`), EFFECT_OUT_R, VCOM_A (2) |
| Power | VDDA (2, U201 pins 20/21) |

What to look at in KiCad besides the open ones: the long B.Cu detours (the
audio bundle down the right-hand edge, the loops over the output stage), the
digital and audio tracks that meet on B.Cu above the relay, and the GND and
rail vias between the codec and the MCU, which crowd the codec's control
lines. Thinning the per-pad rail vias (one via per decoupling pair instead
of per pad) is the change most likely to free room. The `W201` footprint
carries a stale 3.4 × 0.2 mm keepout from its library (off the board, also
on The Relic and the DSP board); it does no harm.

## Schematic sheets (drawn 2026-10-04)

Root sheet plus seven, generated by `scripts/harp_schematic/build_layout.py` from
`harp_spec.py` (see that folder's README). Circuits are the Timekeeper's
(`25-Z01-0001`, `kicad/dsp_board`) unless noted; the bypass is The
Relic's.

| # | Sheet | Designators | Contents |
|---|---|---|---|
| 1 | Controls and LEDs | RV101–103, RV105, R101–103, R105, R107–108, C101–105, SW101–103, J408 | Pots across +3V3, wipers through 1k / 100n to PA0, PA1, PA2, PA4; ON-ON-ON toggles, commons to GND, pins 3 and 4 to PE11–PE15 and PB10; J408 for the 0.91 in OLED on PB6 / PB7 (I²C1) with 4.7k pull-ups |
| 2 | MCU | U201, U202, C201–214, R201–204, FB201, Y201, W201 | STM32H750VBT6, five 100n + 4.7u, 2 × 2.2u VCAP, VDDA/VREF+ through 220R ferrite, 25 MHz HSE, NRST 100n, BOOT0 10k, Segger needle SWD with 22R, W25Q128 on QUADSPI bank 2 |
| 3 | Power | J401, D301–302, FB301–303, U301–302, L301, C301–312, R301–303 | Timekeeper power: SMAJ10CA, PMEG3010 series, TPS54202 → +3V3, NCP718 → +5V; +9V feeds relay and LEDs |
| 4 | Jacks and Bypass | J402–407, K401, Q401–403, D113–114, D402–407, R404–418, C408–412, U401 | Four NMJ6HCD2 jacks (IN is TRS: tip left, ring right), ESD on each, relay bypass on OUT L (Omron G6K-2F-Y), effect and Hold LED drivers, two footswitch pad pairs with RC, Timekeeper expression buffer (MCP6001) |
| 5 | Codec | IC501, U501, R501, R504–505, C501–509 | AK4621EF, OPA2348 VCOM buffers (VCOM_A, VCOM_B), PDN RC, AINL and AINR from the two ADC driver channels |
| 6 | ADC Driver | U601, R601–612, C601–618 | THS4522 channels A (left) and B (right), single-ended to differential, gain 0.59 (R603/R604 and R609/R610 620 Ω) |
| 7 | Analog In and Out | U701–702, R701–719, C701–707 | OPA2365 input buffer, OPA1688 difference amplifiers L and R, 10u, 100R, 1M |

190 parts. Each sheet is wired directly from a hand layout
(`scripts/harp_schematic/layouts/`) to the Frogmouth schematic standard:
global labels only for nets that leave the sheet, a power symbol at each
rail and ground point, and the generator re-reads its own output and traces
every net pin by pin against the spec (no shorts, every pin on its net).

Differences from the Timekeeper, all deliberate:

- **Stereo in.** The IN jack is TRS, tip left and ring right. Both channels
  have an input buffer (the two OPA2365 halves) and a THS4522 channel into
  the codec's AINL and AINR; nothing on the codec inputs is parked. The
  AK4621EF has no single-ended mode (differential inputs only), so the
  THS4522 does the single-ended to differential conversion for both
  channels, as on the Timekeeper. The relay isolates the left input only;
  the right is muted in firmware in true bypass. A mono plug grounds the
  ring: the right channel reads silence and the firmware copies left to
  right.
- **ADC driver reference.** The Timekeeper left the driver's IN_N open; here
  it goes to VCOM_A, the DC level of the input buffer output. This is the
  fix the Timekeeper's own input noise review recommends (finding H1).
  The THS4522 itself stays: it is made for the single 5 V analog rail
  (rail-to-rail output, VOCM pins the output common mode to the codec's
  VCOM). Replacing it with the spare OPA1656 half was tried and reverted
  on 2026-10-05.
- **Input op-amp: OPA2365, not OPA1656.** The OPA1656's input range is
  (V−) to (V+) − 2.25 V (datasheet SBOS901C, 6.6), so on the 5 V rail it
  stops at 2.75 V, only 0.25 V above the 2.5 V bias. The Timekeeper's own
  bench numbers (input noise review, H2 table: peaks at −16 dBFS with a gain
  of 0.152) put hard-played peaks at about ±1.5 V at the buffer, so its
  positive peaks run more than 1 V past that limit. The OPA2365 is a
  zero-crossover rail-to-rail-input part for 2.2–5.5 V, pin-compatible, so
  the 2.5 V bias, the THS4522 and the 5 V rail stay as they are. A 9 V
  buffer supply was ruled out; the OPA2156 (two input stages) was rejected
  because every positive peak would cross its handover step.
- **H2 fix from the Timekeeper's input noise review.** R705 (the
  Timekeeper's R810) is 49.9 Ω, not 5.1 kΩ, and R602 is 1.05 kΩ to match
  the signal leg, so the legs are balanced and the gain is no longer cut to
  about 0.16.
- **Gain 0.59, not 1: R603/R604 are 620 Ω.** At unity a hard-played
  humbucker already reaches ADC full scale and a synth or line source clips.
  At 620 Ω a 4.8 Vpp input, the most the OPA2365 can swing on 5 V, just
  reaches full scale: a normally played single coil lands near −18 dBFS, a
  hard humbucker near −4 dBFS, a +4 dBu synth near −3 dBFS. Decided
  2026-10-05 for both the Harp and the Timekeeper.
- **No input pad.** Sources above 4.8 Vpp (about +7 dBu) clip at the
  OPA2365 and are turned down at the source; no switchable pad in the audio
  path (design brief, decision 11).
- **Outputs not crossed.** The Timekeeper wired AOUTR to its left output; here
  AOUTL is OUT L. Swap the channels in firmware when porting.
- **Output pull-downs.** 100R series and 1M to GND after each 10u, the Relic
  convention, so the outputs sit at 0 V when the DSP is muted.
- **QUADSPI on bank 2** (next section).

## MCU pin map (LQFP-100)

| Function | Pins | Note |
|---|---|---|
| SAI1 to codec | PE2 MCLK_A, PE4 FS_A, PE5 SCK_A, PE6 SD_A (to SDTI), PE3 SD_B (from SDTO) | Same as the Timekeeper |
| Codec control | PC14 CCLK, PC15 CDTI, PB8 CSN, PB4 PDN | Same as the Timekeeper, bit-banged |
| QUADSPI bank 2 | PB2 CLK, PC11 BK2_NCS, PE7–PE10 BK2_IO0–3 | PF6–PF10 do not exist on LQFP-100, and bank 1 IO2 is only on PE2 (taken by SAI1 MCLK). Single flash on bank 2: FSEL = 1 in the QSPI init. **[CONFIRM AF9/AF10 in CubeMX]** |
| Pots | PA0 Mix, PA1 Sustain, PA2 Strings, PA4 Jawari (ADC1) | The Timekeeper's DMA scan; PA3 and PA5 free |
| Expression | PB1 (ADC1) | Same as the Timekeeper |
| Toggles | PE11/PE12 Tuning, PE13/PE14 Retune, PE15/PB10 Brightness | Two inputs each, internal pull-ups; up = A low B high, centre = both low, down = A high B low |
| Footswitches | PB12 bypass, PB13 hold | Internal pull-ups, 1k / 100n RC |
| Relay | PC10 | Same as the Timekeeper |
| LEDs | PC6 effect, PC7 hold (TIM3 CH1/CH2 PWM) | Through 2N7002 from +9V |
| OLED | PB6 SCL, PB7 SDA (I2C1) | 4.7k pull-ups to +3V3, J408 module connector |
| SWD | PA13, PA14, PB3 SWO, NRST | Segger 8.06.05 needle adapter |
| HSE | PH0, PH1 | 25 MHz, 8 pF |
| Free | PA6–PA12, PA15, PB0, PB5, PB9–PB11, PB14–PB15, PC0–PC5, PC8–PC9, PC12–PC13, PD0–PD15, PE0–PE1, PE11, PE15 | No-connect flags on the schematic |

## Order of work

1. **Firmware first on the Timekeeper board**: string bank, chord tracker,
   tuning manager, with the Timekeeper's pots/expression as stand-ins. This
   proves the sound before any Harp PCB is drawn and gives the CPU number.
2. ~~Create the repo and seed the KiCad project from The Relic.~~ Done
   2026-10-04.
3. ~~Draw the schematic.~~ First draft generated 2026-10-04 (sheets above).
   Open it in KiCad and run ERC.
4. Confirm the [CONFIRM]
   items: the OPA2365 1 kHz noise figure on its data sheet plot (estimated
   about 11 nV/√Hz; capacitive-load stability is checked, see below), QUADSPI bank 2 AFs, AK4621 unused-input handling, THS4522
   unused-channel handling.
5. ~~Place.~~ Synced and placed by script on 2026-10-08, both sides
   (*Placement*). **Go/no-go for Plan A: it fits.**
   Still to do in KiCad: ERC, *Update PCB from Schematic* (expect net
   renames only), review the placement by eye, then DRC.
6. ~~GND vias per the Relic rule, route (F.Cu short, B.Cu long, In2 power).~~
   First pass routed by script on 2026-10-09 (*Routing*): 32 connections
   still open. Finish them in KiCad, fill the GND zone, then DRC.
7. Export BOM with the adapted exporter; cost at 100; drill schedule for
   Tayda from the face table above (same tool as the Relic).
8. Fix the wall-hole heights from the measured Alchemist/Relic assembly.

## OPA2365 checks and simulation (2026-10-05)

The Harp's input stage is the Timekeeper's, mono, with the same values (U701 = U801,
R705 = R810, R601/R602 = R501/R502, C702 = C807), so the Timekeeper's input-chain
simulation covers it: `25-Z01-0001_DSP_Development_Board/simulations/InputChain`
(TheFrogMouth/25-Z01-0001_DSP_Development_Board#199).

- **Stability into about 320 pF through 49.9 Ω:** the OPA2365 data sheet gives unity-gain
  stability to about 1 nF and recommends 10–20 Ω isolation; simulated overshoot at the THS4522
  input is ≤ 0.5 % for open-loop output resistance 10–100 Ω (42–76 % without the resistor).
- **Noise:** about 11 nV/√Hz at 1 kHz estimated from the data sheet's 100 kHz and 0.1–10 Hz
  figures; it adds about 0.9 dB over the pickup and bias-resistor noise at the ADC.
- **Gain and headroom:** jack to ADC 0.59 with R603/R604 at 620 Ω (0.95 at 1 kΩ). Guitar and
  synth sources up to 4.8 Vpp reach the ADC without clipping; see the simulation's level table,
  gain against R503/R504, and the guitar and synth headroom graphs.

## Timekeeper rework from the same findings

The Timekeeper (25-Z01-0001) carries all three input-stage issues; fixes for
built boards and the next revision:

| Issue | Timekeeper parts | Fix |
|---|---|---|
| OPA1656 input range on 5 V | U801 | Swap for OPA2365AIDR (same SOIC-8 pinout, both halves used, L and R) |
| H2, series resistor | R809, R810 | 5.1 kΩ → 49.9 Ω |
| H2, leg matching | R502 in both AnalogInputBuffer instances | 1 kΩ → 1.05 kΩ |
| H1, floating IN_N | IN_N of InputBufferA and InputBufferB (CODEC sheet) | Connect to VCOM_A: a wire on built boards, a schematic fix next revision |

All four are applied to the Timekeeper schematic, PCB values and BOM in TheFrogMouth/25-Z01-0001_DSP_Development_Board#199 (the H1 connection still needs routing).
