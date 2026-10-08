# The Harp — design brief

Working title. Project number to be assigned. Written 2026-10-04 from the
concept discussion. Companion to `pcb-plan.md` (board, placement and
schematic sheet plan). Format follows The Relic's `docs/design-brief.md`.

## What it is

A sympathetic-string pedal. Behind the guitar sit up to 24 digitally
modelled strings that nobody plays: they ring when the guitar sounds a note
they are tuned to, as the taraf strings of a sitar or the under-strings of a
Hardanger fiddle do. The pedal listens to the chord being played and keeps
retuning the strings to it, so every note leaves a halo that is in the
player's own harmony. Tuned ambience, not reverb and not shimmer.

The category neighbours are Hologram Microcosm, Chase Bliss Mood and the
Strymon ambience pedals (300 to 450 EUR). Nothing in that category does
chord-following sympathetic strings.

## Why this hardware

The Harp is a cut-down Timekeeper on the Alchemist/Relic 125B hardware set:

- Same codec, flash, buck converter, input and output stages and relay
  bypass as the Timekeeper and the Relic, so the schematic is mostly copied.
- **No SDRAM.** The 24 strings need about 100 KB of delay memory; the
  STM32H750 has 1 MB internal. This removes the external memory bus and
  about 60 pins of MCU.
- **STM32H750VBT6, LQFP-100** instead of the Timekeeper's LQFP-144. Same
  core, same firmware, new pin map.
- **No TFT.** A thin 0.91 in 128×32 I²C OLED strip replaces the screen (decision 14, 2026-10-08).
- **Pots, not encoders.** Encoders only make sense with a screen that shows
  the value; the Timekeeper has one, this does not. Pots also keep the
  Relic's parts and feel. The H750 reads the four of them on ADC1 PA0,
  PA1, PA2 and PA4, with the DMA scan the Timekeeper's `controls.c`
  already runs.
- **Jacks and DC jack in the Alchemist's positions and heights.** See
  `pcb-plan.md`; this is the main reason the design is one board.

## Signal path

```
IN tip -> relay -> input buffer -> ADC (codec L) -> H750: chord tracker
                                                       string bank x24  -> DAC L -> out buffer -> relay -> OUT L
                                                       dry + wet mix    -> DAC R -> out buffer -> relay -> OUT R
IN ring -> input buffer -> ADC (codec R) -> H750 (mono plug: copy L)
EXP (TRS) -> buffer -> H750 ADC
```

Stereo in, stereo out, single-ended at every jack. IN is one TRS jack,
tip = left, ring = right; both channels are buffered (OPA2365 halves) and
driven into the AK4621EF's differential inputs by the two channels of the
THS4522, exactly as the Timekeeper does. A mono plug shorts the ring to the
sleeve, so the right channel reads silence; the firmware copies left to
right until the right channel carries signal. The relay isolates the left
input only, the right is muted by the DSP in true bypass. The dry signal goes through the codec: the
pedal's whole point is the wet sound, and converting the dry keeps the mix,
trails and output level in firmware. Latency is one block (about 6 ms at
44.1 kHz / 256 samples, as the Timekeeper).

## Engine

| Block | What it does | Reuse |
|---|---|---|
| String bank | 24 Karplus-Strong / waveguide strings, each a fractional delay line with a one-pole loss filter and an allpass for tuning. Guitar signal feeds each string through a narrow resonant band-pass at the string's pitch so a string only rings when its note or an overtone is played. No envelope trigger. | New |
| Jawari | Nonlinear bridge: a soft clip plus a short extra delay tap in the loop, depth on the Jawari knob. Zero is a harp, full is a sitar. | New |
| Chord tracker | FFT of the input (the Timekeeper's spectral bank already has the analysis), chroma vector, template match to a chord set with hysteresis. Only chords that last more than ~400 ms retune the strings. | Timekeeper spectral |
| Tuning manager | Assigns string pitches from the chord (Follow), a fixed key (Key) or an open tuning set (Drone, stacked fifths among the sets). Snap retunes only silent strings; Glide slides sounding strings to the new pitch; Lock stops retuning. | New |
| Stereo spread | Strings panned low-left to high-right. | New |
| Front end | Hum filter and noise gate before the strings. | Timekeeper |
| Framework | Effect chain, presets in QSPI flash, control smoothing, expression, UI simulator. | Timekeeper |

CPU: 24 strings at 44.1 kHz is a few MIPS each; the Timekeeper's spectral
bank alone is heavier. Comfortable on the H750 at 480 MHz, but **not yet
measured**.

## Controls

125B face laid out as The Alchemist's: 20 mm columns −20 / 0 / +20, rows
+38 and +13 (the same 20 × 25 mm pitch as The Gremlin and the Timekeeper),
plus one toggle at (0, −5); 12.5 mm knobs. Nothing through-hole sits over
the upper jacks (`pcb-plan.md`). The toggles are The Alchemist's Taiway
100-DP6 ON-ON-ON, so each one stages the effect in three steps.

| Position (face X, Y) | Control | Notes |
|---|---|---|
| (−20, +38) knob | Mix | Dry/wet |
| (0, +38) knob | Sustain | String decay time |
| (+20, +38) knob | Strings | 6 to 24 active strings |
| (−20, +13) toggle | Tuning | Follow / Key / Drone (key and drone set in the secondary layer) |
| (0, +13) knob | Jawari | Bridge buzz |
| (+20, +13) toggle | Brightness | Dark / Warm / Glassy loss-filter voicings |
| (0, −5) toggle | Retune | Snap / Glide / Lock |
| window at (0, −20) | 0.91 in OLED strip | Note names the strings are tuned to, chord, mode and the value of the knob last moved; behind a window in the face |
| (−20, −35) | Effect LED | |
| (−20, −49) | Bypass footswitch | Momentary SPST-NO soft-touch, wired to hand-solder pads |
| (+20, −49) | Hold footswitch | Freezes the tuning and sets infinite sustain while held or latched |
| right wall | IN, EXP | Alchemist jack positions |
| left wall | OUT L, OUT R | Alchemist jack positions |
| top wall | DC | Alchemist DC position |

All four pots and the three toggles go to the MCU; none is in the audio
path. There is no screen, so secondary settings (key, drone set, bypass
mode True / Trails, expression target Bend / Swell, latch behaviour) are
set by a footswitch gesture and a knob, with the OLED strip as the display.

## Bypass

Relay true bypass, one relay, The Relic's circuit (decision 7 in its brief)
with The Alchemist's relay: Omron G6K-2F-Y (DC5, 5.2 mm tall, SMD) driven by
a 2N7002 from the MCU, 5 V coil from +9V through 150 Ω, pull-down keeps it
off through boot. Pole A
switches OUT L between IN and the DSP; pole B disconnects the input buffer
from IN and grounds it. **OUT R is silent in true bypass**; stereo players
use Trails mode, where the relay stays energised and the DSP passes dry on
both outputs while the strings ring out. The pedal passes signal to OUT L
unpowered. Before every relay change the DSP fades its outputs to silence,
switches, waits for the contacts, and fades back in; no mute transistor.

## Cost target

Against The Relic's estimate (46.20 EUR at 100) the electronics roughly
double and the rest is the same:

| Group | EUR |
|---|---:|
| H750, codec, flash, buck, LDO, op-amps, passives | 22.00 |
| 4 pots, 3 ON-ON-ON toggles, 2 momentary footswitches, 4 knobs, 2 LEDs + 0.91 in OLED module (replaces 12 LEDs and 12 light pipes; price to confirm) | 19.00 |
| 5 jacks, relay, footswitch pads | 7.00 |
| 125B, Tayda drilled and UV printed | 9.20 |
| PCB (4-layer), SMT assembly, freight, packaging allocation | 9.00 |
| Estimate | 66.00 |

At 299 EUR, which the category supports, roughly 165 EUR gross before
labour. Nothing carted.

## Decisions taken on 2026-10-04

1. **One relay, true bypass on OUT L only**, Trails mode in firmware for
   stereo use. Two relays rejected as a cost and current increase for a
   case most players do not have.
2. **One board**, Alchemist outline, jacks and pots on it, unless the
   placement in `pcb-plan.md` does not fit; the fallback is a two-board
   stack with the face board keeping the jacks (see that document).
3. **Pots, not encoders.**
4. **Twelve top-side SMD LEDs with 3 mm light pipes** for the note display. *Superseded by decision 14.*
   They sit over the jack bodies, where through-hole parts are not allowed.
5. **STM32H750VBT6 (LQFP-100), no SDRAM.** Everything else in the digital
   and audio chain is the Timekeeper's.
6. **Dry through the codec.** No analog dry path.
7. **One face standard with The Alchemist and The Relic**: the same knob,
   toggle, jack, DC, LED and footswitch coordinates, each pedal using the
   subset it needs (table in `pcb-plan.md`).
8. **QUADSPI on bank 2** (PB2, PC11, PE7–PE10), so SAI1 keeps the
   Timekeeper's PE2–PE6 and the audio firmware ports unchanged.
9. **Mono in, stereo out** in hardware: one input buffer and one ADC driver *(superseded by decision 15: stereo in)*
   channel; the codec's right ADC input is parked at VCOM.
10. **Input op-amp OPA2365 on the 5 V rail** (zero-crossover rail-to-rail
    input), replacing the Timekeeper's OPA1656, whose input stops 2.25 V
    below the rail. With the Timekeeper's H2 fix (R705 49.9 Ω, R602 1.05 kΩ)
    and R603/R604 at 620 Ω, the gain from the jack to the ADC is 0.59, so a
    4.8 Vpp input just reaches full scale: guitar and synth both fit.
    Decided 2026-10-05; 9 V for the buffer was ruled out.
11. **No line/synth input pad.** The input takes up to 4.8 Vpp (about
    +7 dBu), in line with most Strymon pedals (+8 dBu). A +4 dBu synth
    peaks near −3 dBFS. Hotter sources (Eurorack at about 10 Vpp, a synth
    at full volume) are turned down at the source, or go through a passive
    inline attenuator, before the pedal. A switchable pad (as on the Strymon
    Night Sky, Eventide H90 or Meris pedals) was considered and rejected: it
    would put a switch at the high-impedance input, in the audio path, for a
    case the source's own volume control already covers. Decided 2026-10-05.
12. **Shared parts follow The Alchemist** (its main branch, 2026-10-05):
    Neutrik NMJ6HCD2 jacks (11.4 mm wall holes, same axis heights), Omron
    G6K-2F-Y relay, Alpha RD901F-40-15R1-B10K pots, Kingbright WP710A10ID
    panel LEDs fitted at final assembly, soft-touch footswitches on
    hand-solder pads, IN jack ring to ground. Each shared symbol carries
    the design part and the JLCPCB part (`LCSC`, `JLCPCB Manufacturer`,
    `JLCPCB Part #`) The Alchemist records.
13. **Face as The Alchemist's** (2026-10-06): four knobs (Mix, Sustain,
    Strings, Jawari) and three Taiway 100-DP6-T200B1M2QE ON-ON-ON toggles,
    Tuning (Follow / Key / Drone) and Brightness (Dark / Warm / Glassy) at
    (±20, +13) and Retune (Snap / Glide / Lock) at (0, −5). The Relic's six
    knobs and three toggles did not fit four jacks: the outer lower-row
    pots' pins land on the upper jacks' rear pads and the outer toggles sit
    over the jack bodies. Each toggle is read on two MCU inputs. Bypass mode
    and expression target move to the secondary layer; Fifths becomes a
    drone set.

## Still open

- Secondary layer: it now holds more settings than there are knobs (key
  or drone set, spread, bypass mode, expression target and range, Hold
  latching, Brightness trim, chord commit time, output trim). Pick a second
  page or drop some, on the prototype.
- [CONFIRM] items on the schematic: QUADSPI bank 2 alternate functions
  (the AK4621's right input and the THS4522's second channel are now used,
  so those two items are closed).
- OLED: choose the module (36–38 × 12–12.5 mm envelope, I²C, 3.3 V) and
  measure it; the 24.4 × 7.6 mm window and the face-mounted carrier follow
  from it (`pcb-plan.md`, *OLED mounting*). I²C address and refresh budget
  in firmware.

- Chord tracker quality on distorted or fast playing. Key and Drone modes do
  not depend on it, so the pedal works even if Follow is weak.
- Display: decided on 2026-10-08, a 0.91 in I²C OLED strip behind a
  Tayda rectangular cut (above).
- The Alchemist's side-wall and top-wall hole heights are still to be fixed
  from the NMJ6HCD2 and PJ-063AH drawings and the board depth; The Harp
  inherits whatever is measured.
- Expression jack: TRS wiring and buffer as the Timekeeper (MCP6001).
- Firmware prototype first: the whole engine can be developed and tested on
  the Timekeeper board before any Harp PCB exists.

## Risks

- Codec and H750 near a high-impedance guitar input on one 56 × 90 mm board.
  Mitigation: The Relic's four-layer stack with one unbroken ground plane,
  zoning in `pcb-plan.md`, buck converter at the DC end away from the input.
- AK4621EF lifecycle (already flagged in the Timekeeper's BOM audit).
- The OLED module hangs from the face over the relay zone; K401 was moved 2.15 mm towards the heel on 2026-10-08 so it no longer sits under the module (`pcb-plan.md`, *OLED mounting*). Parts placed under the module later must stay below about 6.8 mm.

## Decisions taken on 2026-10-08

14. **A 0.91 in 128×32 I²C OLED strip replaces the twelve note LEDs and
    their light pipes** (J408, PB6 SCL / PB7 SDA, 4.7 kΩ pull-ups). PD0–PD11
    are freed. Supersedes decision 4. The module is held by a 3D-printed
    carrier bonded under the face, behind a 24.4 × 7.6 mm Tayda rectangular
    cut centred at (0, −20), and wired to J408 by a 4-wire lead
    (`pcb-plan.md`, *OLED mounting*).
15. **Stereo in, single-ended at the jacks, stereo out.** IN is a TRS jack
    (tip left, ring right); the right channel gets its own OPA2365 half and
    the second THS4522 channel into AINR, so the AK4621's inputs are never
    parked. The AK4621EF has no single-ended mode (its inputs are fully
    differential); the Timekeeper's single-ended-to-differential THS4522
    driver does that job. A mono plug is detected by the right channel
    reading silence. Supersedes decision 9.
