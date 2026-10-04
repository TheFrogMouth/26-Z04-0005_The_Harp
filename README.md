# 26-Z04-0005 — The Harp

Frogmouth digital sympathetic-string guitar pedal. Up to 24 modelled strings
that nobody plays ring when the guitar sounds their note, retuned continuously
to the chord being played. STM32H750VBT6, AK4621EF codec, no SDRAM, relay
bypass, in a Hammond 125B on the Alchemist/Relic board and jack layout.

Status: **planning.** No schematic or PCB yet.

## Layout

| Path | Contents |
|------|----------|
| `docs/design-brief.md` | What the pedal is, engine, controls, bypass, cost target, decisions, open items |
| `docs/pcb-plan.md` | One-board plan and two-board fallback, face schedule, zoning, schematic sheets, pin budget, order of work |
| `hardware/kicad/the_harp/` | KiCad project (to be seeded from The Relic) |
| `hardware/gerbers/` | Fabrication output |
| `firmware/the_harp/` | STM32H750 firmware |
| `Documents/` | Controlled LaTeX documents, one folder each |
| `bom/` | Generated BOM (`scripts/export_bom.py`, to be adapted from The Relic) |
| `scripts/` | Project tooling |

## Conventions

Same as The Relic and The Alchemist: enclosure centre is the PCB drill/place
and grid origin at (148.5, 105); face X right, face Y up; jacks on the board
underside at the Alchemist's positions and heights; pots on the board;
momentary footswitches wired to headers; relay true bypass.
