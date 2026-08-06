# Sanitized reference configurations

Nothing below this directory is a current deployable printer profile. These
trees preserve historical and factory context for comparison:

- `qidi-firmware-1.7.3-beacon` and `qidi-firmware-1.7.3-beacon-box` are the old
  QIDI 1.7.3 Beacon profiles;
- `qidi-firmware-1.8.2-factory` is the QIDI 1.8.2 factory extraction;
- `qidi-firmware-1.8.2-beacon-non-box-stale` is the superseded QIDI-fork
  non-Box profile; and
- `qidi-firmware-1.8.2-beacon-box-pre-klippee` is the superseded Box profile
  from before Klippee became the verified source of truth.

The reference files are intentionally sanitized. Real Beacon/Box by-id paths
are replaced with `CHANGE_ME_*` values, and generated `SAVE_CONFIG` tails are
removed. Use Git history if an exact old calibration is ever needed; do not
deploy a reference tree to either current printer.
