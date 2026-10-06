# The Harp — firmware requirements

Draft A, 2026-10-04. Companion to `design-brief.md` (what the pedal is) and
`pcb-plan.md` (pin budget, sheets). This document says what the firmware in
`firmware/the_harp/` must do; it does not say how. Where the brief leaves a
value open, the number here is a **proposal** marked *(TBC)* and is settled
on the Timekeeper prototype (section 14).

Sources: the design brief and PCB plan in this repo, and the Timekeeper
firmware it reuses
(`25-Z01-0001_DSP_Development_Board/firmware/dsp_development_board/`):
`audio_fx.h` (chain and ISR hand-off), `controls.c` (ADC1 scan),
`fx_spectral.c` (STFT), `fx_humfilter.c`, `fx_noisegate.c`, `preset.c`
(QSPI slots), `AK4621EF.c`, the IWDG and crash record in `main.c`, and the
host test suite in `tests/run_tests.sh`.

## 1. Conventions

- **Shall** is a requirement, **should** a goal, **may** a permission.
- Each requirement has an ID (`AUD-3`, `STR-5`, …) so tests, commits and
  issues can cite it. IDs are never reused; a dropped requirement is struck
  through, not deleted.
- **Verification** column: **T** host unit test (runs in `tests/`), **B**
  bench measurement on hardware, **L** listening test, **I** inspection of
  code or build output, **A** analysis.
- **Priority**: **1** needed for the first Harp hardware build, **2** needed
  for release, **3** wanted.
- Face positions and designators are those of `pcb-plan.md`.

## 2. Scope

In scope: everything that runs on the Harp's STM32H750VBT6, i.e. the audio
engine, controls, note display, relay bypass, persistence, start-up, fault
handling and the production test mode, plus a build of the same engine on
the Timekeeper board for prototyping.

Out of scope for the first release: MIDI (the spare UART is reserved for
it), the codec's second ADC channel as an aux input, a USB or other
field-update path, and an OLED display (open item in the brief).

## 3. Platform

| ID | Requirement | Ver. | Pri. |
|---|---|---|---|
| PLT-1 | Target is the STM32H750VBT6 (LQFP-100) at 480 MHz with the FPU and I/D caches on, no external SDRAM. | I | 1 |
| PLT-2 | Every audio buffer, delay line and FFT work area shall live in internal RAM (DTCM 128 KB, AXI SRAM 512 KB, D2 288 KB, D3 64 KB). DMA buffers shall not be placed in DTCM, which no DMA reaches. | I | 1 |
| PLT-3 | The image shall fit the H750's 128 KB internal flash, with at least 16 KB free at the first Harp build. If it does not, the fallback (execute from QSPI in memory-mapped mode, or a loader in internal flash) is a decision to raise, not to take silently. | I | 1 |
| PLT-4 | One source tree shall build for two boards: `BOARD_HARP` and `BOARD_TIMEKEEPER`. Pin maps, the relay polarity, the LED driver and the codec wiring are selected by a board header; the engine and control logic are identical on both. | I | 1 |
| PLT-5 | Every DSP and control-logic module shall build and run on a desktop compiler with no HAL, no CMSIS and no heap, as the Timekeeper's modules do, so the engine is testable without hardware. | T | 1 |
| PLT-6 | No dynamic allocation after start-up. All buffers sized for the maximum (24 strings) at compile time. | I | 1 |
| PLT-7 | Toolchain: STM32CubeIDE / arm-none-eabi-gcc as the Timekeeper; host tests with gcc `-Wall -Wextra -Werror`. | I | 1 |

## 4. Audio path

| ID | Requirement | Ver. | Pri. |
|---|---|---|---|
| AUD-1 | AK4621EF over SAI1, 44.1 kHz, 24-bit, codec configured over I2C1, using the Timekeeper's driver. | B | 1 |
| AUD-2 | Input is codec ADC L (mono). ADC R is ignored and its data discarded; the DAC drives OUT L and OUT R. | B | 1 |
| AUD-3 | Processing runs in the SAI DMA half/complete callbacks on blocks of the Timekeeper's size (64 frames, `AUDIO_BUFFER_SIZE` 256 half-words). | I | 1 |
| AUD-4 | Dry path: the dry signal shall pass the DSP at unity gain (±0.1 dB) with no processing other than the mix, the bypass fades and the output limiter. The front end (hum filter, gate) applies to the string feed only, not to the dry. | T, B | 1 |
| AUD-5 | Input-to-output latency of the dry path shall be ≤ 3 ms, measured jack to jack *(TBC on the bench; 64-frame blocks with double buffering plus the codec filters should give about 2.5 ms)*. | B | 1 |
| AUD-6 | The output shall never clip digitally. A wet-bus limiter (ceiling −1 dBFS *(TBC)*) shall act before the DAC, and the wet level shall be normalised for the number of active strings so that the Strings knob changes density, not loudness, by more than ±3 dB. | T, L | 1 |
| AUD-7 | Denormals flushed (FPU FZ set); any string whose state goes non-finite is reset to silence within one block and counted in a diagnostic. | T | 1 |
| AUD-8 | Output noise floor with Mix fully wet and no input shall be no worse than the Timekeeper's measured floor plus 3 dB. | B | 2 |
| AUD-9 | No audible click or zipper noise from any knob, toggle, footswitch, retune or mode change. | L | 1 |

Note: the brief gives the latency as "one block, about 6 ms at 44.1 kHz /
256 samples". The Timekeeper's `AUDIO_BUFFER_SIZE` is 256 half-words of
interleaved stereo, i.e. 64 frames per DMA half, about 1.5 ms. AUD-5 uses
the smaller figure; the brief should be corrected once it is measured.

## 5. Engine

### 5.1 Front end

| ID | Requirement | Ver. | Pri. |
|---|---|---|---|
| FE-1 | Hum filter and noise gate from the Timekeeper, in that order, on the signal that feeds the strings and the chord tracker. | T | 1 |
| FE-2 | The gate shall close the string feed only; strings already ringing decay naturally. | T | 1 |

### 5.2 String bank

| ID | Requirement | Ver. | Pri. |
|---|---|---|---|
| STR-1 | Up to 24 strings, each a waveguide / Karplus-Strong loop: fractional delay line, one-pole loss filter, tuning allpass. | T | 1 |
| STR-2 | Pitch range of the bank C2 (65.4 Hz) to C6 (1047 Hz) *(TBC)*. Delay memory sized for the lowest pitch plus the Jawari tap and interpolation margin; about 24 × 700 samples × 4 bytes ≈ 70 KB, inside the brief's 100 KB. | A, I | 1 |
| STR-3 | Tuning accuracy ±2 cents across the range, at every Brightness setting (the loss filter's phase delay is compensated). | T | 1 |
| STR-4 | Excitation: the front-end signal reaches each string through a resonant band-pass at the string's pitch. A string shall respond to a played note whose fundamental or a low partial (up to the 4th *(TBC)*) coincides with its pitch, and stay at least 20 dB *(TBC)* quieter for a note a semitone away. No envelope or onset trigger. | T, L | 1 |
| STR-5 | Sustain sets the string decay, T60 from 0.5 s to 20 s *(TBC)*, log taper. Infinite sustain (Hold) shall be stable: string energy bounded, no runaway, indefinitely. | T | 1 |
| STR-6 | Brightness (SW103) selects one of three loss-filter voicings, **Dark / Warm / Glassy**, roughly 1.2 kHz / 4 kHz / 10 kHz cutoff *(TBC by ear)*, without changing pitch (STR-3) or, by more than 3 dB, level. A change cross-fades over 50 ms *(TBC)* with no click (AUD-9). | T, L | 1 |
| STR-7 | Strings sets 6 to 24 active strings in steps of 1. Strings removed fade out over ≥ 50 ms; strings added start silent. Which strings drop is set by the tuning manager (TUN-6). | T | 1 |
| STR-8 | Inactive strings cost no CPU beyond a branch. | I | 2 |

### 5.3 Jawari

| ID | Requirement | Ver. | Pri. |
|---|---|---|---|
| JAW-1 | Nonlinear bridge in each string loop: soft clip plus a short extra delay tap, depth on the Jawari knob. Zero is linear (harp), full is the buzzing sitar bridge. | T, L | 1 |
| JAW-2 | At every Jawari setting the loop stays stable and the pitch stays within STR-3. | T | 1 |
| JAW-3 | Jawari should be level-dependent (louder notes buzz more), as a real bridge is. | L | 2 |

### 5.4 Chord tracker

| ID | Requirement | Ver. | Pri. |
|---|---|---|---|
| CHD-1 | Analyse the front-end signal into a 12-bin chroma vector and match it to a chord set with hysteresis. Reuse the Timekeeper STFT where it fits. | T | 1 |
| CHD-2 | Chord set for the first release: major, minor, power chord (root + fifth), dominant 7th, minor 7th, sus2, sus4 *(TBC)*; plus "single note". Output is a pitch-class set and a root. | T | 1 |
| CHD-3 | A new chord shall be adopted only after it has been stable for the commit time, 400 ms by default *(TBC, may become a secondary setting)*. Silence (gate closed) never changes the chord. | T | 1 |
| CHD-4 | Accuracy target on a reference set of clean DI recordings of open and barre chords in standard tuning: ≥ 90 % of chords correct within 600 ms. On distorted input: best effort, measured and recorded, not a release gate (the brief's open item). | T | 2 |
| CHD-5 | Low-note resolution. A 1024-point frame at 44.1 kHz has 43 Hz bins, wider than a semitone below about C4. The tracker shall resolve pitch classes down to E2, by a longer frame (4096 points), harmonic weighting or another method; whichever is chosen is justified by CHD-4. | T | 1 |
| CHD-6 | The tracker runs outside the audio ISR or spread over hops so that it never pushes a block over the CPU budget (PRF-1). | B | 1 |
| CHD-7 | The tracker is not needed in Key or Drone mode and shall not run there, to save CPU. | I | 2 |

### 5.5 Tuning manager

| ID | Requirement | Ver. | Pri. |
|---|---|---|---|
| TUN-1 | Three modes on the Tuning toggle (SW101): **Follow** (up: strings take the tracked chord), **Key** (centre: the diatonic scale of a set key), **Drone** (down: a fixed open tuning chosen from a set, TUN-3). | T | 1 |
| TUN-2 | Key mode: 12 roots × major / natural minor *(TBC: modes beyond these)*. | T | 1 |
| TUN-3 | Drone sets, first release: sitar tarab (Sa–Re–Ga–Ma–Pa scale on a set root), open D (D A D F♯ A D), open G, DADGAD, root + fifth, stacked fifths on a set root *(TBC: list to be settled by ear)*. | T | 1 |
| TUN-4 | Allocation is deterministic: the same pitch-class set and string count always give the same tuning. Low strings take the root and fifth first; pitches are spread over the bank range (STR-2). | T | 1 |
| TUN-5 | Minimum movement: on a change of set, a string whose pitch is still in the new set keeps it. | T | 1 |
| TUN-6 | When Strings is reduced, strings are dropped from the top of the range first, keeping the root and fifth. | T | 2 |
| TUN-7 | **Snap** (SW102 up): only strings below a silence threshold (−60 dB re. full scale *(TBC)*) retune; sounding strings keep their pitch until they decay below it. | T | 1 |
| TUN-8 | **Glide** (SW102 centre): sounding strings slide to the new pitch over the glide time, 150 ms default *(TBC)*, without clicks (AUD-9) and with the loop gain held constant during the slide. | T, L | 1 |
| TUN-9 | Hold (FSW-3) freezes the tuning: no retune of any kind while Hold is active. | T | 1 |
| TUN-10 | A tuning change in Key or Drone (a new key or set chosen by the user) follows Snap / Glide like a chord change. | T | 1 |
| TUN-11 | **Lock** (SW102 down): no retune of any kind, as TUN-9, while the sustain stays on the Sustain knob. Leaving Lock retunes to the current set through Glide. | T | 1 |

### 5.6 Stereo, mix and output

| ID | Requirement | Ver. | Pri. |
|---|---|---|---|
| OUT-1 | Strings panned by pitch, low to the left and high to the right, constant power. Spread width is a secondary setting, 0 (mono) to 100 %, default 70 % *(TBC)*. | T | 1 |
| OUT-2 | A player with only OUT L connected shall hear every string. Spread at 0 % puts the full mix on both outputs; whether the default needs to be narrower than 70 % for this is decided by ear on the prototype. | L | 1 |
| OUT-3 | The dry signal is centred (equal on both outputs). | T | 1 |
| OUT-4 | Mix law: dry at unity from fully counter-clockwise to noon while the wet rises from silent to full; from noon to fully clockwise the dry falls to silent with the wet at full *(TBC by ear)*. | T, L | 1 |
| OUT-5 | Output level with Mix fully counter-clockwise matches true bypass within ±0.5 dB at 1 kHz. | B | 1 |

## 6. Controls

### 6.1 Pots

Four pots, B10K on ADC1 PA0, PA1, PA2, PA4, read with the Timekeeper's DMA
scan (`controls.c`). PA3 and PA5 are free.

| ID | Requirement | Ver. | Pri. |
|---|---|---|---|
| POT-1 | Pot map: PA0 Mix (RV101), PA1 Sustain (RV102), PA2 Strings (RV103), PA4 Jawari (RV105). | I | 1 |
| POT-2 | Scan at ≥ 1 kHz per channel, smoothed so that a still pot causes no audible change and no change in a stepped value. Dead bands of 2 % at each end so every pot reaches 0 and 1. | T, B | 1 |
| POT-3 | Continuous parameters are slewed in the audio path (one-pole, 20 ms *(TBC)*) so knob moves are click-free. | T | 1 |
| POT-4 | Stepped parameters (string count, secondary-layer selections) use hysteresis of at least half a step, so a pot on a boundary never toggles. | T | 1 |

### 6.2 Toggles

| ID | Requirement | Ver. | Pri. |
|---|---|---|---|
| TGL-1 | Three Taiway 100-DP6 ON-ON-ON toggles: SW101 Tuning Follow / Key / Drone (PE11 A, PE12 B), SW102 Retune Snap / Glide / Lock (PE13, PE14), SW103 Brightness Dark / Warm / Glassy (PE15, PB10). Commons to GND, internal pull-ups. Decode: A low, B high = up; both low = centre; A high, B low = down; both high (between positions) keeps the last state. Read at start-up and on change, debounced 20 ms. | T, B | 1 |
| TGL-2 | A toggle change acts like a knob move: Tuning through TUN-10, Retune at once, Brightness through its cross-fade (STR-6), never with a click (AUD-9). | T, B | 1 |
| TGL-3 | Changing the bypass-mode secondary setting while the effect is off follows the bypass sequence (BYP-3), so the relay never switches with signal on the DSP outputs. | T, B | 1 |

### 6.3 Footswitches

Two momentary SPST-NO switches: Bypass (J105, face −20, −49) and Hold
(J106, +20, −49).

| ID | Requirement | Ver. | Pri. |
|---|---|---|---|
| FSW-1 | Debounce 10 ms *(TBC against the RC on the board)*; an action fires on the press edge, not on release, except where a hold gesture is defined. | T, B | 1 |
| FSW-2 | Bypass: a tap toggles the effect on and off. | T | 1 |
| FSW-3 | Hold: momentary by default (active while pressed); latching (tap on, tap off) as a secondary setting. While active: tuning frozen (TUN-9) and sustain infinite (STR-5). On release the strings return to the Sustain knob's decay over 200 ms *(TBC)*. | T | 1 |
| FSW-4 | Hold works with the effect on, and in Trails bypass while the strings ring out. In True bypass it does nothing. | T | 2 |
| FSW-5 | Both footswitches pressed together for 2 s enters the secondary layer (section 6.5) *(TBC: see open item 4)*. | T | 1 |

### 6.4 Expression

| ID | Requirement | Ver. | Pri. |
|---|---|---|---|
| EXP-1 | Expression on the buffered TRS input to the ADC (PB1), smoothed as POT-2. | B | 1 |
| EXP-2 | **Bend** (expression target, secondary setting): heel = no bend, toe = all strings up a whole tone *(TBC: range and direction as a secondary setting)*, pitch kept within STR-3 at both ends. | T, L | 1 |
| EXP-3 | **Swell** (expression target, secondary setting): heel = wet silent, toe = wet at the Mix setting. Dry unaffected. | T | 1 |
| EXP-4 | Heel and toe calibration as a secondary setting, stored (PER-1), so any 10–50 kΩ pedal reaches both ends. | T, B | 2 |
| EXP-5 | With no pedal plugged in the expression shall have no effect. Whether the input reads a detectable rail when empty depends on the buffer circuit; if it does not, the firmware ignores expression until a value change larger than 10 % is seen *(TBC with the schematic)*. | B | 1 |

### 6.5 Secondary layer

There is no screen. Secondary settings are reached by a footswitch gesture
and set with the knobs, with the note LEDs as the display.

| ID | Requirement | Ver. | Pri. |
|---|---|---|---|
| SEC-1 | In the secondary layer the knobs set: Mix → key / drone set (the meaning follows the Tuning toggle), Sustain → spread width, Strings → bypass mode (counter-clockwise half True, clockwise half Trails), Jawari → expression target and range (counter-clockwise half Swell, clockwise half Bend with the range growing to the end) *(all TBC; Hold latching, Brightness trim, chord commit time and output trim need a second page or a default, see open item 3)*. The toggles keep their primary job in the layer. | T | 1 |
| SEC-2 | Entering and leaving the layer never changes a primary parameter: on return each pot is ignored until it is moved past the stored value (pick-up), and the effect LED shows a pot that has not been picked up. | T | 1 |
| SEC-3 | The layer is left by the same gesture or after 10 s with no knob moved. Values are saved on leaving (PER-1). | T | 1 |
| SEC-4 | The note LEDs show the value of the knob last moved (DSP-3). | T | 1 |
| SEC-5 | Audio keeps running while in the layer. | T | 1 |

## 7. Note display

Twelve note LEDs D101–D112, C to B left to right, on direct GPIO through
1 kΩ; the effect LED D113 on a PWM pin.

| ID | Requirement | Ver. | Pri. |
|---|---|---|---|
| DSP-1 | Normal running: a note LED is lit for every pitch class the active strings are tuned to. The root is brighter than the others (two levels by software PWM ≥ 1 kHz, or blink, if a dim level shows flicker through the light pipe). | T, B | 1 |
| DSP-2 | A chord change shows on the LEDs at the moment it is committed (CHD-3); in Snap mode, LEDs show the target tuning, not the strings still waiting to retune. | T | 1 |
| DSP-3 | Secondary layer: a stepped value shows as one lit LED (key root, set index 1–12), a continuous value as a bar of LEDs from C. | T | 1 |
| DSP-4 | Effect LED: on when the effect is engaged; breathing slowly while Hold is active; off in bypass. In Trails bypass it fades out with the strings *(TBC)*. | T | 1 |
| DSP-5 | LED switching shall not be audible at the outputs. LED edges are not synchronised to anything in the audio band; any software PWM runs above 20 kHz or below 2 Hz *(TBC: to be checked on the bench, since the LEDs sit over the jack bodies)*. | B | 1 |
| DSP-6 | Faults and test mode use LED patterns listed in the firmware README, distinct from any normal display. | I | 2 |

## 8. Bypass and relay

One Omron G6K-2F-Y relay (5 V coil), driven by a 2N7002 from the MCU, pull-down off
through boot (brief, Bypass). De-energised: OUT L = IN, input buffer
grounded, OUT R silent. Energised: signal goes through the DSP.

| ID | Requirement | Ver. | Pri. |
|---|---|---|---|
| BYP-1 | **True bypass** (bypass mode = True, the default): effect off = relay de-energised. | B | 1 |
| BYP-2 | **Trails bypass** (bypass mode = Trails, secondary setting): the relay stays energised; effect off feeds dry to both outputs, stops feeding the strings and lets them ring out at their current decay (or hold, FSW-4). | T, B | 1 |
| BYP-3 | Every relay change follows: fade the DSP outputs to silence (10 ms *(TBC)*), switch, wait for the contacts to settle (operate time plus bounce from the G6K datasheet, 5 ms *(TBC)*), fade back in. No mute transistor. | T, B | 1 |
| BYP-4 | A footswitch tap reaches the relay within 20 ms. | B | 1 |
| BYP-5 | Bypass in True mode produces no click at OUT L louder than −60 dBu *(TBC)* with the input shorted. | B | 2 |
| BYP-6 | The relay drive pin stays low (relay off, true bypass) from reset until the codec is running and the outputs are at silence. | B | 1 |
| BYP-7 | Power-up state is effect on *(TBC: or last state, see open item 6)*, entered through BYP-3 once the codec is running. | B | 1 |

## 9. Persistence

| ID | Requirement | Ver. | Pri. |
|---|---|---|---|
| PER-1 | Secondary settings, expression calibration and (if BYP-7 says so) the last bypass state are kept in the W25Q128 QSPI flash, with a version number and CRC as the Timekeeper's `preset.c`. | T | 1 |
| PER-2 | Writes only after 2 s with no change and never more often than once per 10 s; settings alternate between at least two sectors so a power loss during a write leaves the previous copy valid. | T | 1 |
| PER-3 | A missing, corrupt or older-version record loads defaults (or migrates, if the layout allows) and never blocks start-up. | T | 1 |
| PER-4 | A flash write never stalls the audio callback (the image runs from internal flash and RAM, not from QSPI, while writing; see PLT-3). | B | 1 |
| PER-5 | User presets are not in the first release (no control to recall them); the layout leaves room for them. | I | 3 |

## 10. Start-up, faults and safety

| ID | Requirement | Ver. | Pri. |
|---|---|---|---|
| SYS-1 | Power to audio within 500 ms *(TBC)*: clocks, codec reset and init, settings load, audio start, fade-in. Outputs silent until the codec is running. | B | 1 |
| SYS-2 | Independent watchdog as the Timekeeper's (IWDG1 from the LSI, crash record kept across reset). A watchdog reset drops the relay (true bypass, signal still on OUT L) and restarts. | B | 1 |
| SYS-3 | Codec, I2C or SAI failure at start-up: relay stays off (OUT L passes the guitar), fault pattern on the note LEDs, retry once. | B | 1 |
| SYS-4 | Audio-callback overrun (block not finished in time) is counted, never crashes, and is visible over SWD/SWO. | I, B | 1 |
| SYS-5 | Brown-out reset enabled at a level that keeps the QSPI write valid. | I | 1 |
| SYS-6 | Firmware version (major.minor.patch and git hash) in the image, readable over SWD and shown on the note LEDs by a gesture *(TBC)*. | I | 2 |

## 11. Performance budgets

| ID | Requirement | Ver. | Pri. |
|---|---|---|---|
| PRF-1 | Worst-case audio callback, 24 strings, full Jawari, Glide active, tracker running: ≤ 60 % of the block period at 480 MHz, measured with the DWT cycle counter (`dbg_audio_max_cycles`) over a 10-minute playing test. | B | 1 |
| PRF-2 | Same figure measured on the Timekeeper board before the Harp schematic is frozen; this is the brief's "not yet measured" CPU number. | B | 1 |
| PRF-3 | RAM: all engine state and buffers ≤ 75 % of internal RAM, reported from the map file at each release. | I | 1 |
| PRF-4 | Flash: see PLT-3. | I | 1 |
| PRF-5 | Hot loops (string bank) may be placed in ITCM with `AUDIO_ITCM`, as the Timekeeper does. | I | 3 |

## 12. Structure and reuse

| ID | Requirement | Ver. | Pri. |
|---|---|---|---|
| ARC-1 | Engine modules are new files under `firmware/the_harp/Core/`: string bank, Jawari, chord tracker, tuning manager, stereo/mix/output. Each is pure C over its own header (PLT-5). | I | 1 |
| ARC-2 | Reused from the Timekeeper: the `audio_fx_t` chain and ISR parameter hand-off, `controls.c`, the hum filter, the noise gate, the STFT from `fx_spectral.c`, the QSPI preset storage, the AK4621EF driver, the IWDG and crash record, the DWT budget timing. How they are shared (copy with a recorded source commit, or a shared library) is open item 7. | I | 1 |
| ARC-3 | Not carried over: SDRAM, FMC, TFT and LVGL, USB, MIDI, encoders, the knob board link, the mod matrix and the other effects. | I | 1 |
| ARC-4 | Parameter changes from the main loop reach the ISR by the Timekeeper's staging pattern (stage, adopt at block boundary); no locks in the audio path. | I | 1 |
| ARC-5 | `BOARD_TIMEKEEPER` build: the note LEDs are drawn on the Timekeeper's TFT, the four pots on four of its control channels and the three toggles in the UI simulator *(TBC)*, Hold and Bypass on its existing switches. | B | 1 |

## 13. Verification

| ID | Requirement | Ver. | Pri. |
|---|---|---|---|
| VER-1 | `firmware/the_harp/tests/run_tests.sh` builds and runs every host test with warnings as errors, as the Timekeeper's suite does. | T | 1 |
| VER-2 | Host tests cover at least: string pitch accuracy across the range and Brightness (STR-3), stability under Hold and full Jawari (STR-5, JAW-2), excitation selectivity (STR-4), tuning allocation and minimum movement (TUN-4, TUN-5), Snap / Glide behaviour (TUN-7, TUN-8), chord tracker on synthetic chords and on the reference recordings (CHD-4), mix law and limiter (OUT-4, AUD-6), pot pick-up and hysteresis (SEC-2, POT-4), settings CRC and migration (PER-3). | T | 1 |
| VER-3 | An offline render tool runs the engine over a WAV file and writes a stereo WAV, for listening tests and for tracker evaluation on recorded playing. | T | 1 |
| VER-4 | Reference recordings for CHD-4 (clean DI and distorted, chords and single notes) are kept in the repo or referenced from it, with expected labels. | I | 2 |
| VER-5 | Production test mode, entered by holding both footswitches at power-up: walks the LEDs, toggles the relay with a pause, shows each pot and toggle on the LEDs, outputs a 1 kHz tone at −10 dBFS on both outputs, and exits on power cycle. | B | 2 |

## 14. Order of work

1. **On the Timekeeper board** (`BOARD_TIMEKEEPER`): string bank with a
   fixed tuning, then Jawari, then the tuning manager in Key / Drone
   (neither needs the tracker). Measure PRF-2. Listen; settle
   the *(TBC)* ranges in sections 5 and 6.
2. Chord tracker and Follow mode, offline first against the reference
   recordings (VER-3, VER-4), then on the board.
3. Controls, secondary layer and the TFT stand-in for the note LEDs.
4. Port to `BOARD_HARP` when the schematic pin map exists: LEDs on GPIO,
   relay sequence, toggles, settings in QSPI, start-up and fault handling.
5. Production test mode and the bench measurements (sections 4, 8, 11).

## 15. Open items

1. **Brief latency figure.** The brief's 6 ms / 256-sample block does not
   match the Timekeeper's 64-frame block; correct the brief after AUD-5 is
   measured.
2. **Internal flash.** Whether the Harp image fits 128 KB (PLT-3). Build
   the Timekeeper image without TFT, LVGL, USB and SDRAM code to get a
   first number.
3. **Secondary layer size.** With Tuning, Brightness and Retune on
   toggles, bypass mode and expression target join the secondary layer,
   which now has more settings than knobs (SEC-1). Choose a second page or
   defaults on the prototype.
4. **Secondary-layer gesture.** Both footswitches together (FSW-5) keeps
   each switch's single job simple; the alternative, holding Bypass,
   delays every bypass action until release. Decide on the prototype.
5. **Mono use.** With no switch on the output jacks the firmware cannot
   tell that OUT R is unused (OUT-2). Either a default spread a mono player
   can live with, or a jack-detect line on the schematic now while the
   pin budget has room.
6. **Power-up state.** Effect on, or last state (BYP-7, PER-1).
7. **Sharing code with the Timekeeper.** Copy the reused modules into this
   repo with the source commit recorded, or pull them from a shared
   library (submodule). Copying is simpler for a first build; a library
   avoids two copies of the same fixes.
8. **Expression detection without a switch** (EXP-5) depends on the
   Timekeeper buffer circuit carried into sheet 6.
9. **Display.** Whether 12 LEDs are enough (brief open item) is judged
   after step 3 of section 14, using the TFT stand-in.

## 16. Trace to the brief

| Brief item | Requirements |
|---|---|
| Signal path, mono in / stereo out, dry through the codec | AUD-1 – AUD-5, OUT-1 – OUT-5 |
| String bank, 24 strings, no envelope trigger | STR-1 – STR-8 |
| Jawari | JAW-1 – JAW-3 |
| Chord tracker, ~400 ms commit, hysteresis | CHD-1 – CHD-7 |
| Tuning manager, Follow / Key / Drone, Snap / Glide / Lock | TUN-1 – TUN-11 |
| Stereo spread | OUT-1, OUT-2 |
| Front end | FE-1, FE-2 |
| Framework: chain, presets in QSPI, smoothing, expression, UI simulator | ARC-2, ARC-4, PER-1 – PER-5, POT-3, EXP-1 – EXP-5, ARC-5 |
| Controls and face | POT-1 – POT-4, TGL-1 – TGL-3, FSW-1 – FSW-5 |
| Secondary settings by footswitch + knob | SEC-1 – SEC-5 |
| 12 note LEDs, effect LED | DSP-1 – DSP-6 |
| Relay true bypass, Trails, fades, no mute transistor | BYP-1 – BYP-7 |
| No SDRAM, H750VBT6 | PLT-1 – PLT-3, STR-2 |
| CPU "not yet measured" | PRF-1, PRF-2 |
| Firmware first on the Timekeeper board | PLT-4, ARC-5, section 14 |
