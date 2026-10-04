# The Harp — schematic and PCB plan

2026-10-04. Planning only: nothing drawn yet. Companion to
`design-brief.md`. The starting point is The Relic's KiCad project
(`26-A03-0003_The_Relic/kicad/the_relic/`) for the board, the face guides,
the jacks, the pots and the relay bypass, and the Timekeeper's DSP board
(`25-Z01-0001_DSP_Development_Board/hardware/kicad/dsp_board/`) for the
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
| Input buffer OPA1656 + anti-alias, expression buffer MCP6001, ESD | 20 | Timekeeper U801, U702 |
| Output buffers OPA1688 L/R + reconstruction, ESD | 18 | Timekeeper U802 |
| Relay bypass: EE2-5NU, 2N7002 ×2, diode, resistors, RC on the footswitch inputs | 12 | Relic K401 group |
| 6 pots, 3 toggles, 13 LEDs, LED resistors | 35 | Relic + new |
| 5 jacks, 2 footswitch headers | 7 | Alchemist/Relic |
| **Total** | **≈ 195** | |

The Relic places 120 parts on this outline with room to spare in the
digital zone; the Timekeeper's DSP board carries 145 (with SDRAM and a
144-pin MCU) on a larger board. About 195 parts, most of them 0402/0603
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

| Part | Face (X, Y) | Notes |
|---|---|---|
| RV101 Tuning, RV102 Sustain, RV103 Strings | (−20, +38), (0, +38), (+20, +38) | B10K to ADC1 |
| RV104 Brightness, RV105 Jawari, RV106 Mix | (−20, +13), (0, +13), (+20, +13) | B10K to ADC1 |
| SW101 Snap/Glide, SW102 Bypass mode, SW103 Exp target | (−20, −5), (0, −5), (+20, −5) | SPDT on-on to GPIO |
| D101–D112 note LEDs | X −27.5 to +27.5 at 5 mm pitch, Y −18 | 0603 SMD, top side, 3 mm light pipes in the face |
| D113 effect LED | (−20, −35) | Relic position |
| Bypass footswitch | (−20, −49) | Momentary, wired to J105 |
| Hold footswitch | (+20, −49) | Momentary, wired to J106 (the Relic's free position) |
| J201 IN (right wall, lower), J202 EXP (right wall, upper) | axis Y −22.5, −3.5 | NRJ6HM-1 on B.Cu, Alchemist J807/J202 positions |
| J203 OUT L (left wall, lower), J204 OUT R (left wall, upper) | axis Y −22.5, −3.5 | Alchemist J301/J203 positions |
| J301 DC | X 0, opening Y +57.2 | PJ-063AH on B.Cu on the tab |

The LED band at Y −18 lies between the two jack rows (bodies span Y +6.3 to
−32.3 on both walls, X ±5 to ±30), which is why the LEDs must be SMD. The
outer LEDs at X ±27.5 are 2.6 mm from the cavity wall at ±30.15; check the
light-pipe flange diameter (Bivar PLP1-xxx / Dialight 515 series, 3 mm)
against the 5 mm pitch and the wall. If it does not fit, use 11 LEDs for
the chromatic notes with C at the centre, or 4.5 mm pitch.

## Zoning (top side, face coordinates)

```
 Y +52 ─────────────────────────────────────────  DC tab: TVS, Schottky, buck (U301) and its inductor
       │ RV101        RV102        RV103        │  row +38; buck output filter between the pots
       │   LDO 5VA, +3V3 distribution           │
       │ RV104        RV105        RV106        │  row +13; 3.3 V analog filter, pot RC filters
       │ codec IC401 + refs (centre)            │  under the pot rows: codec, DFAs, OPA2348
       │ SW101        SW102        SW103        │  row −5
       │ ─── LED strip D101–D112 at −18 ─────── │  over the jack bodies: SMD only
       │ OUT bufs  │   H750 U401     │ IN buffer│  band −18…−38: output side left, input side right
       │ relay K201│   QSPI flash    │ EXP buf  │
       │ D113 (−35)  J105   SWD pads   J106     │
 Y −38 ─────────────────────────────────────────
```

Signal runs right to left as on the Alchemist: IN and EXP enter on the
**right** wall, OUT L/R leave on the **left**. So the input and expression
buffers sit at the right-hand end of the lower band next to J201/J202, the
output buffers and the relay at the left-hand end next to J203/J204, and
the H750 with the flash in the middle. The relay takes the Relic's K401
position (the Alchemist's old FFC spot).

Rules carried over from The Relic:

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

## Schematic sheets

Root sheet plus seven, Relic-style, with designator ranges per sheet:

| # | Sheet | Designators | Copied from | Changes |
|---|---|---|---|---|
| 1 | Controls and LEDs | RV1xx, SW1xx, D1xx, J105–J106 | Relic (pots, toggles, LED, footswitch header) | Six pots to ADC1 PA0–PA5 via RC; three toggles to GPIO with pull-ups; 12 note LEDs on GPIO through 1 kΩ (direct drive, 12 pins; a 74HC595 pair is the fallback if pins run short); effect LED on a PWM pin |
| 2 | Audio IO and Bypass | J2xx, K201, Q2xx | Relic Power and IO (relay, footswitches) + Alchemist jacks | Four NRJ6HM-1 plus relay as the brief; EXP jack TRS: tip to buffer, ring +3V3A via 1 kΩ, sleeve GND |
| 3 | Power | J301, D3xx, U301, U302, L301 | Timekeeper power sheet | 9 V in, SMAJ10CA, PMEG3010, TPS54202 → +3V3 (digital), NCP718 5 V → +5VA for the codec analog side and op-amps, ferrite-fed +3V3A for the codec digital/ADC reference and pot supply. Relay coil from +9V via 150 Ω |
| 4 | MCU | U401, Y401, SW401, W401 | Timekeeper MCU sheet | STM32H750VBT6; QSPI bank 1 on PB2/PB6/PD11–PD13; SAI1 to the codec; I2C for codec control; SWD on Segger pogo pads (Relic W501 footprint); BOOT0 pad; no FMC |
| 5 | Codec | IC501, U5xx | Timekeeper codec sheet | AK4621EF, OPA2348 reference buffer, THS4522 ADC driver (L only populated; R DNP but on the board) and THS4522 DAC filter L/R, unchanged |
| 6 | Analog In | U601, U602, D6xx | Timekeeper input sheet | OPA1656 input buffer + 2-pole anti-alias; MCP6001 expression buffer; PESD5V0U1 on each jack line |
| 7 | Analog Out | U701, D7xx | Timekeeper output sheet | OPA1688 L and R reconstruction and output buffers; 100 Ω series, 1 M pull-down; ESD |

Symbol properties (Manufacturer, Mfg Part #, LCSC) go on every symbol as
in the Relic so `scripts/export_bom.py` can be adapted straight across.

## MCU pin budget (LQFP-100)

| Function | Pins |
|---|---|
| Power, VCAP, VREF, NRST, BOOT0, oscillator | ~22 |
| QSPI (CLK, NCS, IO0–IO3) | 6 |
| SAI1 (MCLK, SCK, FS, SD_A, SD_B) | 5 |
| I2C1 to codec, codec reset/PDN | 3 |
| SWD (SWDIO, SWCLK) + SWO | 3 |
| ADC1 pots PA0–PA5, expression PA6 | 7 |
| Toggles ×3, footswitches ×2 | 5 |
| Note LEDs ×12, effect LED (PWM) | 13 |
| Relay drive | 1 |
| UART (debug / future MIDI), spare | 4 + |
| **Used** | **≈ 69 of 100** |

Enough headroom for direct LED drive; no shift register needed.

## Order of work

1. **Firmware first on the Timekeeper board**: string bank, chord tracker,
   tuning manager, with the Timekeeper's pots/expression as stand-ins. This
   proves the sound before any Harp PCB is drawn and gives the CPU number.
2. Create the repo (`26-A0x-000x_The_Harp`), copy The Relic's
   `kicad/the_relic/` as the project seed: keep the PCB (outline, Cmts.User
   guides, jacks, pots, toggles, LED, relay), delete the PT2399 and analog
   sheets, keep Power and IO.
3. Draw sheets 3–7 by copying the Timekeeper's sheets and deleting the
   SDRAM, TFT, USB-C, MIDI and FFC parts; swap the MCU symbol to the VBT6
   and re-pin.
4. Draw sheet 1 (controls, LEDs) and finish sheet 2 (bypass, four jacks).
5. ERC, then *Update PCB from Schematic*; place the LED strip and check the
   light-pipe fit against the cavity; place MCU/flash in the centre band,
   codec under the pots, buffers at the jack ends, buck on the tab. **Go/no-go
   for Plan A here.**
6. GND vias per the Relic rule, route (F.Cu short, B.Cu long, In2 power),
   DRC with the Relic's `.kicad_dru`.
7. Export BOM with the adapted exporter; cost at 100; drill schedule for
   Tayda from the face table above (same tool as the Relic).
8. Fix the wall-hole heights from the measured Alchemist/Relic assembly.
