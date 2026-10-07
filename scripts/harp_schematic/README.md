# Schematic generator

Writes the Harp's KiCad 10 schematic from a plain Python description of the
circuit (`harp_spec.py`) and a hand layout per sheet (`layouts/`), in the
style of `docs/schematic-standard.md` in 26-F01-0001_Frogmouth: every
connection inside a sheet is a wire, global labels only for nets that leave
the sheet, a power symbol at each rail and ground point, Oswald on every
font, power symbols numbered uniquely across the project, and a coloured
block diagram on the top sheet.

| File | What it is |
|---|---|
| `harp_spec.py` | The circuit: every part, its value, footprint, manufacturer part number and the net on each pin, sheet by sheet |
| `schgen.py` | Writes `.kicad_sch` files: each pin gets a 2.54 mm stub and a power symbol, a global label (net on more than one sheet) or a local label; unused pins get a no-connect flag |
| `kisch.py` | Minimal schematic reader and net tracer, used to check the output |
| `build_layout.py` | **The build.** Runs the sheet layouts into `kicad/the_harp/`, numbers the power symbols, writes the top sheet, then re-reads every sheet, traces the nets and compares them pin by pin with the spec, and runs the layout checks |
| `layout.py` | The layout engine: places parts on the grid, draws wires, power symbols, labels and no-connects, splits wires at the pins they meet, adds junctions, and checks for dangling wires, wires through bodies, overlapping wires, crossings and overlapping text |
| `layouts/<sheet>.py` | One hand layout per sheet (`power.py`, `mcu.py`, ...); `layouts/common.py` has the shared helpers |
| `top_sheet.py` | The top sheet: sheet blocks coloured by domain, domain frames, connection lines, legend, and the embedded title block and Oswald fonts (copied from The Relic's top sheet) |
| `render_png.py` | Preview renderer (Pillow, no KiCad needed): `python3 render_png.py SHEET.kicad_sch out.png [px_per_mm]`. Set `FONT_DIR` to a folder with `Oswald-Regular.ttf` / `Oswald-Bold.ttf` for the real face |
| `build.py` | The first-draft generator (every pin on a labelled stub); superseded by `build_layout.py`, kept for reference |
| `symbols.sexpr` | The 34 symbol definitions used, copied from the Timekeeper, Relic and Alchemist schematics and KiCad's `STM32H750VBTx` |
| `libcollect.py`, `h750vb.kicad_sym` | Only needed to rebuild `symbols.sexpr` (delete it and run `build.py` with the sibling repos checked out next to this one) |

```bash
python3 scripts/harp_schematic/build_layout.py          # every sheet and the top sheet
python3 scripts/harp_schematic/build_layout.py Power    # one sheet (no power renumbering, no top sheet)
# Power   parts 24 wires 65 junctions 20 crossings 0 netlist OK layout OK
```

`netlist OK` means every pin is on the net the spec gives it, every rail
and global net carries its name, no node holds two nets, and no local
label is used except the ones a layout declares in `allow_local` (the MCU
sheet: `QSPI_CLK` and `QSPI_NCS`, whose ends sit on opposite sides of the
MCU). Each crossing is listed; a sheet should have none or very few.

Sheet and symbol UUIDs are derived from the sheet name and reference, so a
rebuild keeps the links to the PCB.

**The generator owns the schematic only until someone edits it in KiCad.**
After that, the KiCad files are the source of truth and running `build_layout.py`
would overwrite those edits. Use it again only for a deliberate full
regeneration, with the spec and the layouts updated to match.
