# QIDI firmware 1.8.2 reference notes

These notes document the original merge of QIDI firmware 1.8.2 with the Beacon
profiles. The old trees now live under `reference/` and are sanitized,
non-deployable comparison material. `printers/qidi1` is the current QIDI-fork
1.8.2 + Box profile. `printers/qidi2` has since migrated to mainline Klipper
and is not an in-place QIDI 1.8.2 configuration.

## Before installing

1. Back up the complete `~/printer_data/config` directory and the current
   `saved_variables.cfg` from each printer.
2. Render the `CHANGE_ME_QIDI1_BEACON_SERIAL` and
   `CHANGE_ME_QIDI1_BOX_SERIAL` placeholders for the intended QIDI1 target.
3. Never copy another printer's Beacon model, mesh, saved variables or USB
   identifiers.
4. Install/reinstall the Beacon Klipper module and the Plus4 `probe.py` patch
   referenced in the main README after the firmware update.
5. Do not copy `config.mksini` from the factory reference to another
   printer. It contains device/app state and is intentionally absent from the
   current profiles.

Generated `SAVE_CONFIG` tails have been removed from both current and reference
trees. QIDI1's stable measured input-shaper values were promoted into its
ordinary configuration; Beacon models and bed meshes remain target-local.
Re-run input shaping, Beacon calibration and bed meshing if the mechanics
change. The Klippee apply workflow must preserve existing target calibration.

## QIDI configuration changes in 1.8.2

Compared with the existing 1.7.3 Beacon + Box configuration, the fresh 1.8.2
factory extraction changes the following areas:

* The factory probing stack is now `[smart_effector]` plus `[qdprobe]`. Homing,
  Z-offset storage, nozzle cleaning and bed meshing were rewritten around that
  probe. Those stock-probe portions are intentionally replaced by the Beacon
  contact/proximity workflow in the deployable folders.
* X/Y microsteps changed from 16 to 32, rotation distance from 38.86 to 38.82,
  and the X minimum/endstop moved from -1.2 to -1.5.
* Z/Z1 microsteps changed from 16 to 128. QIDI also enabled interpolation and
  raised the Z stealthChop threshold. Beacon's required zero homing retract is
  retained instead of the factory 5 mm retract.
* Extruder microsteps changed from 64 to 16, interpolation was enabled,
  `smooth_time` became `0.000001`, pressure-advance smoothing changed from
  0.05 to 0.03, and instantaneous corner velocity changed from 5 to 10.
* Printer square-corner velocity changed from 5 to 8 and resonance-test
  `max_smoothing` changed from 0.1 to 0.5.
* Bed PID values changed to 63.418 / 1.342 / 749.125, and bed heater gain-check
  time changed from 360 to 60 seconds.
* QIDI redesigned the stock chamber heater and fan settings: a 40% heater
  limit, target-temperature bounds, bed-assisted heating, revised verification
  limits, full chamber-fan speed, and a controller-style board fan. The
  repository's custom chamber probe/heater and quieter CPU fan tuning are kept
  in the Beacon variants.
* Auxiliary and chamber fan shutdown behavior changed to stop rather than run
  at full speed. The deployable folders retain hardware-specific/custom values
  where they differ.
* Runout handling gained Box auto-reload support, and the factory macro file
  substantially changed print start, nozzle cleaning, homing, resume/tool
  change, Z-offset and mesh behavior. The deployable folders retain the
  Beacon-compatible macros and the working Box compatibility fixes, since the
  new probe-specific macros cannot be used with Beacon unchanged.
* QIDI added the custom `[print_stats_manager]` and
  `[multi_color_controller]` runtime sections. Both are present in the Box
  variant; the non-Box variant includes the print statistics manager only.
* The fresh extraction also contains `moonraker.conf` and `config.mksini`.
  Both are retained only as sanitized factory/reference context; neither is a
  managed file in the current printer profiles.

`plr.cfg` was byte-for-byte unchanged between the old configuration and the
1.8.2 extraction. The only original `box.cfg` difference was removal of the
reminder comment after its machine-specific MCU serial; that serial is now a
placeholder throughout this sanitized repository.
