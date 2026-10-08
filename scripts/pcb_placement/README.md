# PCB sync and placement scripts

Used on 2026-10-08 to do, without KiCad, what *Update PCB from Schematic*
and a first placement pass would do. They edit
`kicad/the_harp/The Harp.kicad_pcb` in place. Once the board has been
edited in KiCad, KiCad is the source of truth: rerun these only for a
deliberate restart.

| File | What it does |
|---|---|
| `sync_pcb.py` | Brings the board in line with `harp_spec.py`: removes footprints no longer in the schematic, adds new ones (cloned from footprints already on this board or the Timekeeper's), sets values and pad nets, links each footprint to its schematic symbol. New parts are parked off the board. |
| `run_place.py` | Places every part on its group's side: fixed face parts stay, U201 goes at (0, −21.5), each group gets a home position and each passive the nearest free spot to the pads it connects to (decoupling first, bias nets ignored, anti-alias caps at the codec pins). Avoids courtyards on its side, through-holes from the other side, the board edge and, for tall parts, the OLED module. Writes `build/pos.json`. |
| `write_pos.py` | Writes `build/pos.json` into the board file: position, rotation and side (flips a footprint as KiCad does). |
| `verify.py` | Re-reads the board file: courtyard overlaps per side, parts on through-holes from the other side, parts outside the outline, tall parts under the OLED, and that every pad sits where the placer put it. |
| `metrics.py` | Key net lengths and the total, for comparing runs. |
| `render_place.py` | Draws the placement: `CHROME=/path/to/chrome python3 render_place.py ../../docs/images/pcb-placement`. |
| `place.py`, `geom.py`, `pcbread.py` | Shared helpers: footprint geometry, the placer, board-file and spec readers. |

```bash
cd scripts/pcb_placement
python3 run_place.py && python3 write_pos.py && python3 verify.py
```

The placement is greedy and deterministic. Its result and its weak spots
are written up in `docs/pcb-plan.md`, *Placement*.
