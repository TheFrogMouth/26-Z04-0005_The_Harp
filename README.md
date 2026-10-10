# 26-Z04-0005 — The Harp

Frogmouth digital sympathetic-string guitar pedal. Up to 24 modelled strings
that nobody plays ring when the guitar sounds their note, retuned continuously
to the chord being played. STM32H750VBT6, AK4621EF codec, no SDRAM, relay
bypass, in a Hammond 125B on the Alchemist/Relic board and jack layout.

Status: **first schematic draft, board placed and mostly routed, 29 connections open.** Seven sheets generated from the Timekeeper's circuits and The Relic's bypass (190 parts, net-traced, drawn to the Frogmouth schematic standard, not yet opened in KiCad); board outline and 28 face/jack/bypass footprints placed from The Relic. Stereo in (TRS) and a 0.91 in OLED display added 2026-10-08; the PCB was synced to the schematic and every part placed on both sides on 2026-10-08 (scripted; one-board fit confirmed, see `docs/pcb-plan.md` *Placement*). First routing pass by script on 2026-10-09: GND to In1 and rails on In2 from every pad, analog and digital kept apart. Opened in KiCad 2026-10-10 (now the source of truth): power section re-placed and re-routed, every track at the Alchemist widths and at 0/45/90°, 29 connections left for KiCad (*Routing*). See `docs/pcb-plan.md` and `kicad/README.md`.

## Layout

| Path | Contents |
|------|----------|
| `docs/design-brief.md` | What the pedal is, engine, controls, bypass, cost target, decisions, open items |
| `docs/pcb-plan.md` | One-board plan and two-board fallback, face schedule, zoning, schematic sheets, pin budget, order of work |
| `docs/firmware-requirements.md` | Firmware requirements (draft): audio path, engine, controls, display, bypass, persistence, budgets, verification |
| `kicad/the_harp/` | KiCad 10 project: seven-sheet schematic, Relic-outline board |
| `Gerbers/` | Fabrication output, when generated |
| `firmware/the_harp/` | STM32H750 firmware |
| `Documents/` | Controlled LaTeX documents, one folder each |
| `bom/` | Generated BOM (`scripts/export_bom.py`, to be adapted from The Relic) |
| `scripts/harp_schematic/` | Schematic generator and net checker (first draft only; see its README) |
| `scripts/pcb_placement/` | PCB sync to the schematic and scripted placement (2026-10-08; see its README) |
| `scripts/oled_drawings/` | Face cut-out and OLED-to-PCB drawings in `docs/images/` |

The layout is the Frogmouth product repository standard
(`docs/repo-structure.md` in 26-F01-0001_Frogmouth).

## Conventions

Same as The Relic and The Alchemist: enclosure centre is the PCB drill/place
and grid origin at (148.5, 105); face X right, face Y up; jacks on the board
underside at the Alchemist's positions and heights; pots on the board;
momentary footswitches wired to pads; relay true bypass.
