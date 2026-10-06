# Schematic generator

Writes the first draft of the Harp's KiCad 10 schematic from a plain Python
description of the circuit.

| File | What it is |
|---|---|
| `harp_spec.py` | The circuit: every part, its value, footprint, manufacturer part number and the net on each pin, sheet by sheet |
| `schgen.py` | Writes `.kicad_sch` files: each pin gets a 2.54 mm stub and a power symbol, a global label (net on more than one sheet) or a local label; unused pins get a no-connect flag |
| `kisch.py` | Minimal schematic reader and net tracer, used to check the output |
| `build.py` | Runs the generator into `kicad/the_harp/`, then re-reads every sheet, traces the nets and compares them with the spec |
| `symbols.sexpr` | The 34 symbol definitions used, copied from the Timekeeper, Relic and Alchemist schematics and KiCad's `STM32H750VBTx` |
| `libcollect.py`, `h750vb.kicad_sym` | Only needed to rebuild `symbols.sexpr` (delete it and run `build.py` with the sibling repos checked out next to this one) |

```bash
python3 scripts/harp_schematic/build.py
# sheets 7 parts 192 global nets 49 problems 0
```

Sheet and symbol UUIDs are derived from the sheet name and reference, so a
rebuild keeps the links to the PCB.

**The generator owns the schematic only until someone edits it in KiCad.**
After that, the KiCad files are the source of truth and running `build.py`
would overwrite those edits. Use it again only for a deliberate full
regeneration, with the spec updated to match.
