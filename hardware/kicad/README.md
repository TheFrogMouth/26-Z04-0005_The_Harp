# KiCad project — The Harp

`the_harp/` is the KiCad 10 project, seeded from The Relic
(`26-A03-0003_The_Relic/kicad/the_relic/`, 2026-10-04). Generated offline and
checked for balanced S-expressions only: **not yet opened in KiCad**, so run
ERC and DRC first.

## What was carried over

- **Board**: The Relic's 56 × 90 mm outline with the DC tab, four-layer stack
  (F.Cu / In1 GND / In2 PWR / B.Cu), the GND zone, the 125B face, cavity and
  corner-boss guides and the datum (enclosure centre = (148.5, 105)).
- **Schematic**: the root sheet and `Power and IO.kicad_sch` (relay bypass,
  jacks, DC jack, input and output stages). The PT2399, saturation, age
  filter, noise, modulation and mix sheets are dropped.
- **Footprints kept (41)**: everything on Power and IO, plus the face parts
  on The Relic's grid, renumbered to the plan in `docs/pcb-plan.md`:

| Relic | Harp | Role | Face (X, Y) |
|---|---|---|---|
| RV501 / RV502 / RV601 | RV101 / RV102 / RV103 | Tuning / Sustain / Strings | (−20, +38) / (0, +38) / (+20, +38) |
| RV201 / RV701 / RV301 | RV104 / RV105 / RV106 | Brightness / Jawari / Mix | (−20, +13) / (0, +13) / (+20, +13) |
| SW501 / SW602 / SW603 | SW101 / SW102 / SW103 | Snap-Glide / Bypass mode / Exp target | (−20, −5) / (0, −5) / (+20, −5) |
| D401L | D113 | Effect LED | (−20, −35) |
| J402 | J402 (IN) | Right wall, lower | axis Y −22.5 |
| J403 | J403 (OUT L) | Left wall, lower | axis Y −22.5 |
| — (new) | J404 (OUT R) | Left wall, upper | axis Y −3.5 |
| — (new) | J406 (EXP) | Right wall, upper | axis Y −3.5 |

The two new jacks are copies of the lower ones moved 20 mm up, the
Alchemist's upper-pair positions (J203 / J202).

## What was removed

All 92 other footprints, **all tracks and vias** (the GND vias belonged to the
dropped parts), and the Relic's pot/toggle/LED sheet links. Face labels on
`Cmts.User` are renamed to the Harp controls.

## First steps in KiCad

1. Open `The Harp.kicad_pro`; run ERC on `Power and IO`.
2. Pots, toggles and the LED have no schematic yet. Draw the Controls and LEDs
   sheet with those designators, then *Update PCB from Schematic* with
   **Re-link footprints to schematic symbols based on their reference
   designators** ticked.
3. J404 and J406 have no symbols yet: add them to Power and IO (OUT R, EXP).
4. Still to place: the 12 note LEDs (D101–D112, Y −18), the Hold footswitch
   header (+20, −49), the H750, codec, flash and buffers (see the zoning in
   `docs/pcb-plan.md`).
5. Rework Power and IO: it still carries the Relic's single-channel buffers,
   its 5 V rail for the PT2399 and the 3V3 LDO for the STM32C031. Per the
   design brief, the Harp needs a buck 9 V → 3V3, a quiet 5 VA and 3V3A.
6. Regenerate the GND vias per the Relic rule (one beside every SMD ground
   pad).
