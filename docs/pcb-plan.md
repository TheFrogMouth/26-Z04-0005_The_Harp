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

One face standard for The Alchemist, The Relic and The Harp: every
position below is a shared Tayda drill coordinate, and each pedal uses
the subset it needs.

| Position (face X, Y) | Alchemist | Relic | Harp |
|---|---|---|---|
| Knob row +38: (−20), (0), (+20) | Rate, Depth, Wave | Wow, Flutter, Age | RV101 Tuning, RV102 Sustain, RV103 Strings |
| Knob row +13: (−20), (0), (+20) | Mode toggle, Exp/offset pot, Resonance toggle | Saturation, Mix, Hiss | RV104 Brightness, RV105 Jawari, RV106 Mix |
| Toggle row −5: (−20), (0), (+20) | — | Dropout, Age range, Hiss on | SW101, SW102, SW103 (see the conflict below) |
| Right wall, lower jack, axis Y −22.5 | IN | IN | J402 IN |
| Right wall, upper jack, axis Y −3.5 | Expression | — | J406 EXP |
| Left wall, lower jack, axis Y −22.5 | OUT | OUT | J403 OUT L |
| Left wall, upper jack, axis Y −3.5 | Sync | — | J404 OUT R |
| Top wall DC, X 0 | DC | DC | J401 DC |
| LEDs (−20, −35), (+20, −35) | Effect, Rate | Effect, — | D113 Effect, D114 Hold |
| Footswitches (−20, −49), (+20, −49) | Bypass, Tap | Bypass, — | Bypass (J405), Hold (J407) |
| Note LED band, Y −18 | — | — | D101–D112, X −27.5 to +27.5 at 5 mm |

**Conflict: the upper jacks and the outer toggles.** The Relic's outer
toggles at (±20, −5) sit on top of the upper jack pair's pins (pin rows at
about Y +3.8 and −7.7, X ±12 to ±25). The Alchemist never hits this
because it has no toggle row. The Harp needs all four jacks, so it can
only use the **centre toggle (0, −5)**; SW101 (Snap/Glide) and SW103
(Exp target) have to move to footswitch-hold menus, or the pedal drops
OUT R or EXP. Recommendation: keep SW102 (Bypass mode) at the centre and
make Snap/Glide and Exp target hold-plus-knob settings. Both toggles are
still on the schematic until this is decided; deleting them is two
symbols and two GPIO.

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
       │ codec IC501 + U501, ADC driver U601    │  under the pot rows: codec, DFAs, OPA2348
       │ SW101        SW102        SW103        │  row −5
       │ ─── LED strip D101–D112 at −18 ─────── │  over the jack bodies: SMD only
       │ OUT U702  │   H750 U201     │ IN U701  │  band −18…−38: output side left, input side right
       │ relay K401│   flash U202    │ EXP U401 │
       │ D113 (−35)  J405  W201 SWD  J407  D114 │
 Y −38 ─────────────────────────────────────────
```

Signal runs right to left as on the Alchemist: IN and EXP enter on the
**right** wall, OUT L/R leave on the **left**. So the input and expression
buffers sit at the right-hand end of the lower band next to J402/J406, the
output buffers and the relay at the left-hand end next to J403/J404, and
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

## Schematic sheets (drawn 2026-10-04)

Root sheet plus seven, generated by `scripts/harp_schematic/build.py` from
`harp_spec.py` (see that folder's README). Circuits are the Timekeeper's
(`25-Z01-0001`, `hardware/kicad/dsp_board`) unless noted; the bypass is The
Relic's.

| # | Sheet | Designators | Contents |
|---|---|---|---|
| 1 | Controls and LEDs | RV101–106, R101–118, C101–106, SW101–103, D101–112 | Pots across +3V3, wipers through 1k / 100n to PA0–PA5; toggles to GND on PE12–PE14; 12 note LEDs on PD0–PD11 through 1k |
| 2 | MCU | U201, U202, C201–214, R201–204, FB201, Y201, W201 | STM32H750VBT6, five 100n + 4.7u, 2 × 2.2u VCAP, VDDA/VREF+ through 220R ferrite, 25 MHz HSE, NRST 100n, BOOT0 10k, Segger needle SWD with 22R, W25Q128 on QUADSPI bank 2 |
| 3 | Power | J401, D301–302, FB301–303, U301–302, L301, C301–312, R301–303 | Timekeeper power: SMAJ10CA, PMEG3010 series, TPS54202 → +3V3, NCP718 → +5V; +9V feeds relay and LEDs |
| 4 | Jacks and Bypass | J402–407, K401, Q401–403, D113–114, D402–406, R404–418, C408–412, U401 | Four jacks, ESD on each, Relic relay bypass on OUT L, effect and Hold LED drivers, two footswitch headers with RC, Timekeeper expression buffer (MCP6001) |
| 5 | Codec | IC501, U501, R501–505, C501–509 | AK4621EF, OPA2348 VCOM buffers (VCOM_A, VCOM_B), PDN RC, AINR parked at VCOM |
| 6 | ADC Driver | U601, R601–606, C601–610 | THS4522 channel A, single-ended to differential, gain 1; channel B powered down |
| 7 | Analog In and Out | U701–702, R701–719, C701–707 | OPA1656 input buffer, OPA1688 difference amplifiers L and R, 10u, 100R, 1M |

195 parts. Every pin carries a label or power symbol on a short stub, the
Relic convention, and the generator re-reads its own output and traces every
net against the spec (no shorts, no single-pin nets, every pin assigned).

Differences from the Timekeeper, all deliberate:

- **Mono in.** One input buffer and one ADC driver; AINR+/AINR− parked at
  VCOM through 1k each [CONFIRM against the AK4621 datasheet].
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
  the signal leg, so the THS4522 runs at its designed gain of 1 with balanced
  legs instead of about 0.16.
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
| Pots | PA0–PA5 (ADC1) | Same as the Timekeeper's six-channel scan |
| Expression | PB1 (ADC1) | Same as the Timekeeper |
| Toggles | PE12, PE13, PE14 | Internal pull-ups |
| Footswitches | PB12 bypass, PB13 hold | Internal pull-ups, 1k / 100n RC |
| Relay | PC10 | Same as the Timekeeper |
| LEDs | PC6 effect, PC7 hold (TIM3 CH1/CH2 PWM) | Through 2N7002 from +9V |
| Note LEDs | PD0–PD11 | One GPIOD write; about 1.4 mA each with red/amber LEDs and 1k |
| SWD | PA13, PA14, PB3 SWO, NRST | Segger 8.06.05 needle adapter |
| HSE | PH0, PH1 | 25 MHz, 8 pF |
| Free | PA6–PA12, PA15, PB0, PB5–PB7, PB9–PB11, PB14–PB15, PC0–PC5, PC8–PC9, PC12–PC13, PD12–PD15, PE0–PE1, PE11, PE15 | No-connect flags on the schematic |

## Order of work

1. **Firmware first on the Timekeeper board**: string bank, chord tracker,
   tuning manager, with the Timekeeper's pots/expression as stand-ins. This
   proves the sound before any Harp PCB is drawn and gives the CPU number.
2. ~~Create the repo and seed the KiCad project from The Relic.~~ Done
   2026-10-04.
3. ~~Draw the schematic.~~ First draft generated 2026-10-04 (sheets above).
   Open it in KiCad and run ERC.
4. Decide the toggle conflict (face schedule) and confirm the [CONFIRM]
   items: OPA2365 capacitive-load stability into C702 + C601 (about 320 pF)
   through R705 (49.9 Ω), its noise at 1 kHz, QUADSPI bank 2 AFs, AK4621 unused-input handling, THS4522
   unused-channel handling.
5. ERC, then *Update PCB from Schematic*; place the LED strip and check the
   light-pipe fit against the cavity; place MCU/flash in the centre band,
   codec under the pots, buffers at the jack ends, buck on the tab. **Go/no-go
   for Plan A here.**
6. GND vias per the Relic rule, route (F.Cu short, B.Cu long, In2 power),
   DRC with the Relic's `.kicad_dru`.
7. Export BOM with the adapted exporter; cost at 100; drill schedule for
   Tayda from the face table above (same tool as the Relic).
8. Fix the wall-hole heights from the measured Alchemist/Relic assembly.

## Timekeeper rework from the same findings

The Timekeeper (25-Z01-0001) carries all three input-stage issues; fixes for
built boards and the next revision:

| Issue | Timekeeper parts | Fix |
|---|---|---|
| OPA1656 input range on 5 V | U801 | Swap for OPA2365AIDR (same SOIC-8 pinout, both halves used, L and R) |
| H2, series resistor | R809, R810 | 5.1 kΩ → 49.9 Ω |
| H2, leg matching | R502 in both AnalogInputBuffer instances | 1 kΩ → 1.05 kΩ |
| H1, floating IN_N | IN_N of InputBufferA and InputBufferB (CODEC sheet) | Connect to VCOM_A: a wire on built boards, a schematic fix next revision |
