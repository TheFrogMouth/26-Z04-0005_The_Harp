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
- **No TFT.** Twelve note LEDs replace the screen.
- **Pots, not encoders.** Encoders only make sense with a screen that shows
  the value; the Timekeeper has one, this does not. Pots also keep the
  Relic's face, parts and feel. The H750 reads them on ADC1 PA0–PA5, the
  same six-channel DMA scan the Timekeeper's `controls.c` already runs.
- **Jacks and DC jack in the Alchemist's positions and heights.** See
  `pcb-plan.md`; this is the main reason the design is one board.

## Signal path

```
IN -> relay -> input buffer -> ADC (codec L) -> H750: chord tracker
                                                       string bank x24  -> DAC L -> out buffer -> relay -> OUT L
                                                       dry + wet mix    -> DAC R -> out buffer -> relay -> OUT R
EXP (TRS) -> buffer -> H750 ADC
```

Mono in, stereo out. The codec's second ADC channel is unused (left for a
later return or aux input). The dry signal goes through the codec: the
pedal's whole point is the wet sound, and converting the dry keeps the mix,
trails and output level in firmware. Latency is one block (about 6 ms at
44.1 kHz / 256 samples, as the Timekeeper).

## Engine

| Block | What it does | Reuse |
|---|---|---|
| String bank | 24 Karplus-Strong / waveguide strings, each a fractional delay line with a one-pole loss filter and an allpass for tuning. Guitar signal feeds each string through a narrow resonant band-pass at the string's pitch so a string only rings when its note or an overtone is played. No envelope trigger. | New |
| Jawari | Nonlinear bridge: a soft clip plus a short extra delay tap in the loop, depth on the Jawari knob. Zero is a harp, full is a sitar. | New |
| Chord tracker | FFT of the input (the Timekeeper's spectral bank already has the analysis), chroma vector, template match to a chord set with hysteresis. Only chords that last more than ~400 ms retune the strings. | Timekeeper spectral |
| Tuning manager | Assigns string pitches from the chord (Follow), a fixed key (Key), an open tuning set (Drone) or stacked fifths. Snap retunes only silent strings; Glide slides sounding strings to the new pitch. | New |
| Stereo spread | Strings panned low-left to high-right. | New |
| Front end | Hum filter and noise gate before the strings. | Timekeeper |
| Framework | Effect chain, presets in QSPI flash, control smoothing, expression, UI simulator. | Timekeeper |

CPU: 24 strings at 44.1 kHz is a few MIPS each; the Timekeeper's spectral
bank alone is heavier. Comfortable on the H750 at 480 MHz, but **not yet
measured**.

## Controls

125B face on The Relic's grid: 20 mm columns −20 / 0 / +20, knob rows +38
and +13, toggles at −5, 12.5 mm knobs.

| Position (face X, Y) | Control | Notes |
|---|---|---|
| (−20, +38) | Tuning | Follow / Key / Drone / Fifths, with sub-positions (key, drone set) inside each |
| (0, +38) | Sustain | String decay time |
| (+20, +38) | Strings | 6 to 24 active strings |
| (−20, +13) | Brightness | Loss-filter cutoff, dark to glassy |
| (0, +13) | Jawari | Bridge buzz |
| (+20, +13) | Mix | Dry/wet |
| (−20, −5) | Snap / Glide | Retune behaviour |
| (0, −5) | Bypass mode | True (relay) / Trails (buffered, strings ring out) |
| (+20, −5) | Expression target | Bend / Swell |
| band at −18 | 12 note LEDs | C to B, lit for the notes the strings are tuned to |
| (−20, −35) | Effect LED | |
| (−20, −49) | Bypass footswitch | Momentary SPST-NO, wired to a header |
| (+20, −49) | Hold footswitch | Freezes the tuning and sets infinite sustain while held or latched |
| right wall | IN, EXP | Alchemist jack positions |
| left wall | OUT L, OUT R | Alchemist jack positions |
| top wall | DC | Alchemist DC position |

All six pots go to the MCU; no pot is in the audio path. There is no
screen, so secondary settings (key, drone set, latch behaviour) are set by
holding a footswitch and turning a knob, with the note LEDs as the display.

## Bypass

Relay true bypass, one relay, exactly The Relic's circuit (decision 7 in its
brief): KEMET EE2-5NU DPDT driven by a 2N7002 from the MCU, coil from +9V
through a series resistor, pull-down keeps it off through boot. Pole A
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
| 6 pots, 3 toggles, 2 momentary footswitches, 6 knobs, 13 LEDs + 12 light pipes | 19.00 |
| 5 jacks, relay, headers | 7.00 |
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
4. **Twelve top-side SMD LEDs with 3 mm light pipes** for the note display.
   They sit over the jack bodies, where through-hole parts are not allowed.
5. **STM32H750VBT6 (LQFP-100), no SDRAM.** Everything else in the digital
   and audio chain is the Timekeeper's.
6. **Dry through the codec.** No analog dry path.
7. **One face standard with The Alchemist and The Relic**: the same knob,
   toggle, jack, DC, LED and footswitch coordinates, each pedal using the
   subset it needs (table in `pcb-plan.md`). Open consequence: with four
   jacks, only the centre toggle position is usable on the Harp.
8. **QUADSPI on bank 2** (PB2, PC11, PE7–PE10), so SAI1 keeps the
   Timekeeper's PE2–PE6 and the audio firmware ports unchanged.
9. **Mono in, stereo out** in hardware: one input buffer and one ADC driver
   channel; the codec's right ADC input is parked at VCOM.

## Still open

- Toggle row: keep only the centre toggle, or give up a jack (see
  `pcb-plan.md`, face schedule).
- [CONFIRM] items on the schematic: QUADSPI bank 2 alternate functions,
  AK4621 unused right input, THS4522 unused channel.

- Chord tracker quality on distorted or fast playing. Key and Drone modes do
  not depend on it, so the pedal works even if Follow is weak.
- Whether 12 LEDs are enough display, or a small I2C OLED in the same band is
  worth the window cut. Decide after the first firmware prototype on the
  Timekeeper hardware.
- The Alchemist's side-wall and top-wall hole heights are still to be fixed
  from the NRJ6HM-1 and PJ-063AH drawings and the board depth; The Harp
  inherits whatever is measured.
- Expression jack: TRS wiring and buffer as the Timekeeper (MCP6001).
- Firmware prototype first: the whole engine can be developed and tested on
  the Timekeeper board before any Harp PCB exists.

## Risks

- Codec and H750 near a high-impedance guitar input on one 56 × 90 mm board.
  Mitigation: The Relic's four-layer stack with one unbroken ground plane,
  zoning in `pcb-plan.md`, buck converter at the DC end away from the input.
- AK4621EF lifecycle (already flagged in the Timekeeper's BOM audit).
- Light pipes add a hand-assembly step and a part to source.
