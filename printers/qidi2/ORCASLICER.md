# OrcaSlicer recommendations

These starting points come from the 2026-07-15 Shake&Tune vibration profile,
measured at 3000 mm/s^2 through 200 mm/s. They do not replace temperature,
flow-ratio, pressure-advance or maximum-volumetric-flow calibration for each
filament.

## Acceleration

| Feature | Acceleration |
| --- | ---: |
| First layer | 1000 mm/s^2 |
| External walls and top surfaces | 1500-2000 mm/s^2 |
| Internal walls | 3000 mm/s^2 |
| Infill and travel | 3500 mm/s^2 |

The current Klipper and Orca machine profiles expose a 20,000 mm/s^2 hardware
ceiling. That ceiling prevents stale runtime limits from constraining intended
machine moves; it is not a recommended feature acceleration. The conservative
starting points above remain below the Y shaper's approximately 4090 mm/s^2
smoothing recommendation. Reported shaper acceleration is not a skipped-step
limit.

## Speed

| Feature | Speed |
| --- | ---: |
| External walls | 50-55 mm/s |
| Top surfaces | 50-55 mm/s |
| Internal walls | 100-120 mm/s |
| Solid infill | 100-120 mm/s |
| Sparse infill and support | 150-170 mm/s |
| Travel | 200 mm/s |

The measured low-vibration bands were approximately 2-61, 74-80, 98-125,
132-135, 151-175 and 181-200 mm/s. Prominent vibration peaks appeared around
65, 89, 128, 142 and 179 mm/s. These are targeting guidelines: short moves,
acceleration and volumetric-flow limits mean the commanded speed is not always
reached.

The profile did not measure above 200 mm/s, so it does not validate 300 mm/s
travel. Rerun `CREATE_VIBRATIONS_PROFILE` with a larger range before raising
that limit.

## Printer G-code

Use the standard Klipper/Moonraker connection and the following start G-code:

```gcode
PRINT_START BED=[bed_temperature_initial_layer_single] HOTEND={first_layer_temperature[initial_extruder]} CHAMBER=[overall_chamber_temperature] MESH=adaptive
SET_PRINT_STATS_INFO TOTAL_LAYER=[total_layer_count]
M83
```

Use only this end G-code:

```gcode
PRINT_END
```

Enable **Label objects** in the OrcaSlicer printer profile. Moonraker uses those
object definitions for Klipper's adaptive mesh, Smart Park and the adaptive
Voron purge. If no object definitions are present, Smart Park and Voron Purge
fall back to a fixed safe location; the Beacon mesh still scans continuously.

`MESH=adaptive` performs a fresh continuous Beacon scan for each print. Use
`MESH=default` only when you intentionally want to load a previously saved
`default` mesh, or `MESH=none` for diagnostics.

The current profile defaults to `SOAK=0` and a 5 mm adaptive-mesh margin.
Override them only when a material or print warrants it, for example:

```gcode
PRINT_START BED=110 HOTEND=260 CHAMBER=55 MESH=adaptive SOAK=120 MESH_MARGIN=8
```

Firmware retraction is enabled in the current QIDI2 Orca printer profile and
uses the commissioned 0.8 mm at 30 mm/s retract/unretract settings.
