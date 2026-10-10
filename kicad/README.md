# KiCad project — The Harp

`the_harp/` is the KiCad 10 project. The board was seeded from The Relic
(2026-10-04); the schematic is **generated** by
`scripts/harp_schematic/build_layout.py` from the circuits of the Timekeeper
DSP board and The Relic's relay bypass (`harp_spec.py`) and a hand layout per
sheet (`layouts/`), drawn to the Frogmouth schematic standard
(`docs/schematic-standard.md` in 26-F01-0001_Frogmouth, 2026-10-07). Nothing
here has been opened in KiCad yet: run ERC first.

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
on the Taiway 100-DP6 footprint at (−20, +13), (0, −5) and (+20, +13) (Retune moved to (0, −24) on 2026-10-09), the
bypass footswitch on hand-solder pads, and R405 / D402 moved off J403's
rear pads. The Relic's
regulator parts (C401–C407, D401, R401–R403, U401, U402) were removed. On
2026-10-08 the board was synced to the schematic (see step 2 below): every
footprint is linked to its symbol with its pad nets, the twelve note LEDs
and their resistors are gone. All 181 footprints were then placed on the
top side by script (`scripts/pcb_placement/`, `docs/pcb-plan.md` *Placement*).

## First steps in KiCad

1. Open `The Harp.kicad_pro`, open every sheet once, run ERC. Expect
   cosmetic warnings (label placement, overlapping text); anything about
   power pins or unconnected pins is real, report it.
2. The board was synced to the schematic on 2026-10-08 without KiCad (no
   KiCad in that session): 181 footprints (190 symbol units), each linked to its symbol, values
   and pad nets checked pin by pin against `harp_spec.py`. Run Tools → Update PCB from
   Schematic once anyway: it should report no changes apart from net
   renames (KiCad names unlabelled nets `Net-(...)`) and footprint library
   refreshes. Anything else it reports is a sync miss: note it.
3. Every part is placed on both sides (scripted, 2026-10-08; see *Placement*
   in `docs/pcb-plan.md`). Look it over, then run DRC.
4. The board was routed by script on 2026-10-09 (`scripts/pcb_routing/`,
   *Routing* in `docs/pcb-plan.md`): GND vias per the Relic rule, rails on
   In2. On 2026-10-10 the power section was re-placed and re-routed and
   every track brought to the Alchemist widths (0.254 / 0.508 / 0.762 /
   1.0 mm, digital 0.1524) and to 0/45/90°. Fill the In1 GND zone (B), finish the 29 open
   connections listed there, then DRC. The net classes (GND, Rail, Power,
   Audio, Digital, Control, clearance 0.1524) are in the project.

Once the schematic has been edited in KiCad, the KiCad files are the source
of truth; do not re-run the generator over them (see
`scripts/harp_schematic/README.md`).
