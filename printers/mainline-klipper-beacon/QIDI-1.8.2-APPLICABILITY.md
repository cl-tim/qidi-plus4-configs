# QIDI 1.8.2 applicability to mainline Klipper

This profile was checked against the fresh QIDI 1.8.2 factory extraction, the
1.7.3 Beacon profile, the firmware-analysis repository, and upstream Klipper at
the commit used during commissioning,
`f604aeeea3398b70df0456851931f955d981cfc4`.
The firmware comparison shows that most non-AMS QIDI host patches were
unchanged between 1.7.3 and 1.8.2; the items below are primarily the new
factory configuration policy, plus the new 1.8.2 Box/status components.

## Applied directly

| QIDI 1.8.2 change | Mainline treatment |
| --- | --- |
| XY 32 microsteps, 38.82 rotation distance and X minimum/endstop -1.5 | Already present. |
| Z/Z1 128 microsteps, interpolation and high stealthChop threshold | Already present; Beacon's zero homing retract remains. |
| Extruder 16 microsteps, interpolation and 0.03 pressure-advance smoothing | Already present. |
| Extruder `smooth_time: 0.000001` | Applied. This matches the factory PID baseline and the referenced mainline profile. |
| Extruder instantaneous corner velocity 10 | Applied; supported by upstream Klipper. |
| Printer square-corner velocity 8 | Applied. The current profile exposes the commissioned 600 mm/s and 20,000 mm/s^2 machine ceilings; measured shaper guidance still governs slicer targets. |
| Bed heater gain-check time 60 seconds | Applied; this is also upstream Klipper's current bed default. |
| 1.8.2 extruder, bed and chamber PID values | Applied as starting values in `printer.cfg`, where `PID_CALIBRATE`/`SAVE_CONFIG` can replace them. |
| Chamber maximum power 0.4 and revised verification values | Applied using standard upstream heater options. |
| Auxiliary and chamber circulation fan shutdown speed 0 | Applied. Hotend and chamber-heater fans retain fail-safe cooling behavior. |

## Reproduced with upstream mechanisms

QIDI's heater fork accepts chamber-only target bounds, can couple the chamber
target to the bed, and shuts chamber heating off once a homed machine rises
above Z=270. Mainline does not accept those vendor configuration keys.

The profile enforces QIDI's `0` or `45-65 C` chamber target range in `M141` and
uses `_QIDI_CHAMBER_Z_GUARD` to disable chamber heating above Z=270. It does
not silently increase a slicer's requested bed temperature to chamber target
plus 25 C; hidden material-temperature changes are unsafe and unnecessary in
the explicit `PRINT_START` workflow.

## Deliberately retained from the commissioned mainline profile

| Setting | Reason |
| --- | --- |
| Beacon offsets, contact homing and continuous scan workflow | QIDI 1.8.2's `smart_effector`/`qdprobe` stack is for the stock load-cell probe. |
| `resonance_tester max_smoothing: 0.1` | The profile uses measured Shake&Tune shapers and retains the stricter quality-oriented calibration limit instead of QIDI's 0.5. |
| Z minimum -2 and zero homing retract | Required by the commissioned Beacon workflow; the stock probe uses different travel. |
| Extrusion-only distance 100 and cross-section 5 | Safer upstream limits; the 80 mm chute purge is divided into legal 50 mm and 30 mm moves. QIDI's 1000/500 limits unnecessarily disable safeguards. |
| Hotend maximum 370 C | Retains margin below QIDI's 380 C factory ceiling. |
| Adaptive host fan and separate controller fan layout | Matches the live mainline hardware validation rather than QIDI's vendor fan objects. |
| PB4 5015 nozzle-cooling mapping | Retains the marked toolhead modification: PB4 is the controllable fan, PB5 is the heatbreak fan, and the stock PA8/PA9 fan/tachometer path is absent. |

## Not compatible with unmodified upstream Klipper

Do not add `[smart_effector]`, `[qdprobe]`, `[print_stats_manager]`,
`[multi_color_controller]`, `[chamber_fan]`, `target_min_temp`,
`target_max_temp`, `heat_with_heater_bed`, `heat_with_heater_bed_tem_add`, or
`verify_heater position_z`. They depend on QIDI-only Python or compiled
extensions. Box auto-reload and the new multi-colour state manager are also
irrelevant to this non-Box profile; Happy Hare supplies the mainline AMS path.

The QIDI PID numbers are hardware-family starting values, not a substitute for
calibration. Run `PID_CALIBRATE HEATER=extruder`,
`PID_CALIBRATE HEATER=heater_bed`, and (when used)
`PID_CALIBRATE HEATER=chamber`, followed by `SAVE_CONFIG`, on each printer.
