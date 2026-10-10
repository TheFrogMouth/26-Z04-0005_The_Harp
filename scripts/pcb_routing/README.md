# PCB routing scripts

Used on 2026-10-09 to route `kicad/the_harp/The Harp.kicad_pcb` without
KiCad: the board goes to Freerouting as a Specctra DSN, one net class at a
time, and the session comes back into the board file as tracks and vias.
Once the board has been edited in KiCad, KiCad is the source of truth:
rerun these only for a deliberate restart (they replace every track and via).

| File | What it does |
|---|---|
| `route.py` | Runs the phases in order (below) and writes `build/routes.json`. With phase names, reruns those on top of the rest. |
| `fanout.py` | Gives every SMD pad of a net set its own via and a straight stub (GND and the rails). |
| `regions.py` | The audio and digital regions per layer, from where the pads are; used as keepouts. |
| `dsn.py` | Writes the DSN (each footprint its own image, pads pre-rotated, earlier phases protected) and reads the SES. |
| `nets.py` | Net classes: what each net is, its width and clearance, the via. |
| `write_tracks.py` | Replaces the board's tracks and vias with `build/routes.json`. |
| `check.py` | Stand-in for DRC: connectivity (GND through the plane), clearances per class, copper to edge, hole to hole. |
| `pours.py` | Replaces the rails' In2 tracks with pours (+9V, +5V, +3V3): the old tracks are the backbone, the rest of In2 goes to the nearest one, zones are written, the fill is imitated and any cut-off group is joined by a jumper on F.Cu or B.Cu. Needs the In2 tracks to be present in the board file. |
| `render.py` | Draws F.Cu, B.Cu and In2.Cu with tracks coloured by class. |
| `netclasses.py` | Writes the same classes into `The Harp.kicad_pro` (one pattern per net) for KiCad's DRC and router. |
| `kpcb.py` | Board-file reader: footprints, pads in board coordinates, outline. |

Phases (`route.py`):

1. **gnd**: every SMD GND pad gets its own via to the In1.Cu plane (Relic
   rule). ICs put the via under the package, two-pin parts off the free end.
2. **rails**: every SMD pad on +3V3, +5V, +9V gets its own via; Freerouting
   joins the vias on In2.Cu, the only layer the rails may use. `pours.py`
   then turns those tracks into pours.
3. **power**: local power nets (buck, LDO, DC input, VDDA, relay coil, LED
   current), wide, F/B.
4. **core**: digital round the MCU (codec interface, QSPI, crystal, SWD,
   OLED, reset), kept out of the audio region.
5. **audio**: kept out of the digital region; before the long digital lines
   so the bypass paths get the corridors under the MCU to the relay.
6. **drive**: the LED and relay drive lines to the bottom-side drivers, kept
   out of the audio region.
7. **ctrl**: pots, toggles, footswitches, expression (DC), kept out of the
   audio region.
8. **repair**: anything still open, without the region keepouts and with the
   signal tracks unlocked so the router can move them; GND, rail and power
   copper stays fixed.

Signals never use In2.Cu; vias cost more than Freerouting's default (80
against 50), so a track changes side rarely; much higher and it takes long
one-sided detours instead. No via within 0.6 mm of the SWD needle pads.

Needs Java 25 and Freerouting 2.4.1 (`app.freerouting:freerouting`,
`freerouting-2.4.1-executable.jar` from Maven Central), plus Python with
shapely, numpy, scipy and matplotlib:

```bash
cd scripts/pcb_routing
FREEROUTING=/path/freerouting-2.4.1-executable.jar JAVA=/path/java25 python3 route.py
python3 write_tracks.py && python3 check.py && python3 render.py
```

Freerouting quirks found on the way: any `autoroute_settings` block in the
DSN makes it see nothing to route (so per-layer costs are not used; In2 is
reserved by net class instead), and with an In1 plane declared it counts GND
as done and will not fan it out (so `fanout.py` does that). A full run takes
about an hour and a half on four cores. The 2026-10-09 run left 32
connections open (`docs/pcb-plan.md`, *Routing*).
