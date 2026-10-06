# KiCad project — The Harp

`the_harp/` is the KiCad 10 project. The board was seeded from The Relic
(2026-10-04); the schematic is a first draft **generated** by
`scripts/harp_schematic/build.py` from the circuits of the Timekeeper DSP
board and The Relic's relay bypass. Nothing here has been opened in KiCad
yet: run ERC first.

## Sheets

| Sheet | File |
|---|---|
| Root | `The Harp.kicad_sch` |
| Controls and LEDs | `Controls and LEDs.kicad_sch` |
| MCU (STM32H750VBT6, W25Q128) | `MCU.kicad_sch` |
| Power | `Power.kicad_sch` |
| Jacks and Bypass | `Jacks and Bypass.kicad_sch` |
| Codec (AK4621EF) | `Codec.kicad_sch` |
| ADC Driver (THS4522) | `ADC Driver.kicad_sch` |
| Analog In and Out (OPA1656, OPA1688) | `Analog In and Out.kicad_sch` |

What each sheet holds, the pin map and the deliberate differences from the
Timekeeper are in `docs/pcb-plan.md`. The Relic's `Power and IO` sheet is
gone: its relay bypass is redrawn on Jacks and Bypass with the same
designators, and its regulators are replaced by the Timekeeper's buck and LDO.

## Board

The Relic's 56 × 90 mm outline with the DC tab, four-layer stack, GND zone
and 125B guides. 26 footprints are placed: the four pots, three toggles, the
effect LED, the five jacks (DC, IN, OUT L, OUT R, EXP), the relay and its
driver, the effect-LED driver and the bypass footswitch pads. The four
1/4 in jacks and the relay were replaced on 2026-10-05 with The Alchemist's
NMJ6HCD2 and G6K-2F-Y footprints at its positions. On 2026-10-06 the face
moved to The Alchemist's layout: RV104 and RV106 removed, the three toggles
on the Taiway 100-DP6 footprint at (−20, +13), (0, −5) and (+20, +13), the
bypass footswitch on hand-solder pads, and R405 / D402 moved off J403's
rear pads. The Relic's
regulator parts (C401–C407, D401, R401–R403, U401, U402) were removed. The
remaining footprints have no schematic links or pad nets yet.

## First steps in KiCad

1. Open `The Harp.kicad_pro`, open every sheet once, run ERC. Expect
   cosmetic warnings (label placement, overlapping text); anything about
   power pins or unconnected pins is real, report it.
2. Tools → Update PCB from Schematic, with **Re-link footprints to schematic
   symbols based on their reference designators** ticked. That keeps the 28
   placed footprints where they are and adds the other 161 parts.
3. Place the rest per the zoning in `docs/pcb-plan.md`. The go/no-go for a
   one-board build is this placement.
4. Regenerate the GND vias per the Relic rule, then route.

Once the schematic has been edited in KiCad, the KiCad files are the source
of truth; do not re-run the generator over them (see
`scripts/harp_schematic/README.md`).
