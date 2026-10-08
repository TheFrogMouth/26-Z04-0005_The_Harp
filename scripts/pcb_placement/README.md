# PCB sync and placement scripts

Used on 2026-10-08 to do, without KiCad, what *Update PCB from Schematic*
and a first placement pass would do. They edit
`kicad/the_harp/The Harp.kicad_pcb` in place. Once the board has been
edited in KiCad, KiCad is the source of truth: rerun these only for a
deliberate restart.

| File | What it does |
|---|---|
| `sync_pcb.py` | Brings the board in line with `harp_spec.py`: removes footprints no longer in the schematic, adds new ones (cloned from footprints already on this board or the Timekeeper's), sets values and pad nets, links each footprint to its schematic symbol. New parts are parked off the board. |
| `run_place.py` | Places every part: fixed face parts stay, U201 goes at (0, −21.5), each group gets a home position and each passive the nearest free spot to the pads it connects to (decoupling first). Avoids courtyards, underside jack pins, the board edge and, for tall parts, the OLED module. Writes `build/pos.json`. |
| `write_pos.py` | Writes `build/pos.json` into the board file (position and rotation). |
| `verify.py` | Re-reads the board file: courtyard overlaps, parts outside the outline, top parts over underside through-hole pins, tall parts under the OLED. |
| `score.py` | Total and analogue net length (half-perimeter) of a `pos.json`, to compare runs. |
| `render_place.py` | Draws the placement: `CHROME=/path/to/chrome python3 render_place.py ../../docs/images/pcb-placement`. |
| `place.py`, `geom.py`, `pcbread.py` | Shared helpers: footprint geometry, the placer, board-file and spec readers. |

```bash
cd scripts/pcb_placement
python3 run_place.py && python3 write_pos.py && python3 verify.py
```

The placement is greedy and deterministic. Its result and its weak spots
are written up in `docs/pcb-plan.md`, *Placement*.
