# Valve Oil: candidates for the Plus4 stack

Source snapshot: [Valve Oil `c89dddc475b73e060027ff5a2489239df1b14406`](https://github.com/thelegendtubaguy/Valve-Oil/tree/c89dddc475b73e060027ff5a2489239df1b14406), reviewed 2026-11-23. The initial review used source inspection only. The follow-up below records the later implementation and synthetic compatibility checks; no Valve Oil installer or firmware image was run.

## Recommendation

The strongest additional candidate is **faster, safer saved-variable writes**. **Box heater refresh** and **Klipper link/main-loop diagnostics** also deserve targeted compatibility work. The upstream Klipper C fixes merit a separate backport audit. These are ideas to adapt through hlab's existing transactions, not a recommendation to install Valve Oil on a Plus4.

Valve Oil currently supports Max 4, Plus 5 and Smart 5. Its installer also flashes supported boards automatically. The Plus4's Python 3.7, older Klipper/QIDI extensions, installation paths and firmware images need their own compatibility checks. [Supported targets and installation behavior](https://github.com/thelegendtubaguy/Valve-Oil/blob/c89dddc475b73e060027ff5a2489239df1b14406/README.md#supported-printers), [Box firmware admission](https://github.com/thelegendtubaguy/Valve-Oil/blob/c89dddc475b73e060027ff5a2489239df1b14406/firmware/BOX_FIRMWARE.md#L24-L50).

## Prioritized candidates

| Candidate | Value for our stack | Adoption boundary |
|---|---|---|
| Skip unchanged `SAVE_VARIABLE` writes and avoid reloading the file just written | Removes work beyond the runout dwell removal already adopted. The published Plus4 code still rewrites the whole file and calls `loadVariables()` after every command. | Highest-priority small host-side improvement; preserve QIDI serialization, default attributes and command semantics. |
| Atomic saved-variable replacement | Avoids truncating the live file while constructing its replacement. | Use file and directory fsync if durability across power loss is required; upstream's implementation does not do either. |
| Shorter Box-heater refresh interval | Gives the host more scheduling margin before the Box output watchdog expires. | Inspect the actual Plus4 heater and MCU behavior; its published host timings differ from Valve Oil's documented newer printers. |
| Box link and main-loop context in diagnostics | Can distinguish accumulating host work, late commands and communication symptoms more precisely than USB events alone. | Extend hlab/Klippee selectively; do not add another unbounded logger or equate a disconnect with a power fault. |
| Upstream Klipper C-helper fixes | Potential memory-leak, descriptor-leak, queue-safety and homing-timeout benefits. | Audit the Plus4 source first and rebuild for its ABI; the bundled Valve Oil library is not a Plus4 replacement. |
| Spoolman per-slot tracking | Connects material usage to the spool actually loaded from a Box. | Useful if Spoolman is used; our hlab currently observes active Spoolman state rather than implementing this complete slot-accounting path. |
| Configurable staged heating / minimum chamber readiness | A practical print-start policy option. | Adapt to our Beacon, purge and chamber macros; do not replace the complete start sequence. |

### Saved-variable writes: the clearest new opportunity

Valve Oil's handler skips a command when the current value's representation already matches, creates the replacement state without re-reading it from disk, and refreshes QIDI's default-value attributes. It also tries to wrap the Box modules' direct save methods, which otherwise bypass the G-code handler. [Implementation](https://github.com/thelegendtubaguy/Valve-Oil/blob/c89dddc475b73e060027ff5a2489239df1b14406/installer/klipper/extras/save_variables_fast.py#L147-L259).

This addresses work our existing runout patch intentionally retained: all sixteen saves still execute. Official Plus4 source writes with `open(..., "w")`, closes it and then calls `loadVariables()`; a read-only comparison with the locally extracted 2.1.1 vendor source found the same sequence. This is source evidence, not a measurement of a running print. [Official Plus4 Klipper source](https://github.com/QIDITECH/klipper/blob/4bb7c6337936ef273e621d1f55bc0ef92114785d/klippy/extras/save_variables.py#L90-L112).

The upstream `_write()` closes a temporary file and uses `os.replace()`, preserving mode and attempting to preserve group. It does **not** fsync the temporary file or its directory. Atomic replacement and guaranteed power-loss durability are different properties; do not repeat the README's power-cut language as a guarantee. Our implementation should follow the stronger durability pattern already used by hlab's persistent USB writer. [Atomic writer](https://github.com/thelegendtubaguy/Valve-Oil/blob/c89dddc475b73e060027ff5a2489239df1b14406/installer/klipper/extras/save_variables_fast.py#L64-L88).

Do not copy the whole module unchanged: its migration of `tltg_` settings to `vo_` names is specific to Valve Oil, and replacing Cython-backed Box methods needs an explicit compatibility check. Preserve representations/types, ConfigParser interpolation behavior, case handling, permissions, error handling and any concurrent readers. [Project-specific migration and command registration](https://github.com/thelegendtubaguy/Valve-Oil/blob/c89dddc475b73e060027ff5a2489239df1b14406/installer/klipper/extras/save_variables_fast.py#L91-L145).

### Box heater refresh: plausible, but timings differ

Valve Oil shortens unchanged Box-heater output refreshes to one second while leaving other heaters and safety limits unchanged. It also stops a failed Box AHT20 poll after Klipper is already shut down, so the sensor error does not replace the original failure. [Mechanism](https://github.com/thelegendtubaguy/Valve-Oil/blob/c89dddc475b73e060027ff5a2489239df1b14406/installer/klipper/extras/box_heater_refresh.py#L95-L139).

Its documentation describes a 3.75-second refresh against a five-second watchdog. The published Plus4 heater source instead declares `MAX_HEAT_TIME = 10.0` and uses `0.75 * MAX_HEAT_TIME`, implying 7.5 seconds at that host layer. The locally extracted 2.1.1 source has those same values. This does not establish the actual Box firmware deadline or prove a fault on this machine; verify that pairing before adapting the refresh. [Valve Oil explanation](https://github.com/thelegendtubaguy/Valve-Oil/blob/c89dddc475b73e060027ff5a2489239df1b14406/installer/klipper/extras/box_heater_refresh.py#L1-L25), [Plus4 host constant](https://github.com/QIDITECH/klipper/blob/4bb7c6337936ef273e621d1f55bc0ef92114785d/klippy/extras/heaters.py#L14), [Plus4 refresh calculation](https://github.com/QIDITECH/klipper/blob/4bb7c6337936ef273e621d1f55bc0ef92114785d/klippy/extras/heaters.py#L69-L80).

### Diagnostics and host correctness

The link monitor records serial counters and heater context in a separate rotated file. Klipper-health code adds timer count, main-thread load, homing synchronization context and late-command attribution. These could improve Klippee's analysis and collection without changing motion. [Link monitor inputs](https://github.com/thelegendtubaguy/Valve-Oil/blob/c89dddc475b73e060027ff5a2489239df1b14406/installer/klipper/extras/box_link_monitor.py#L1-L57), [Klipper health](https://github.com/thelegendtubaguy/Valve-Oil/blob/c89dddc475b73e060027ff5a2489239df1b14406/installer/klipper/extras/klipper_health.py#L757-L888).

The associated timer-leak cleanup is narrower than a general reactor cleanup: it targets stopped, unreferenced `_read_wei_timer` and `_init_probe_data_advance` callbacks from the newer load-cell workflow. Those names were not found in the locally extracted Plus4 2.1.1 Box binary. That absence is a static observation, not proof about every build, and is insufficient reason to apply the timer cleanup. [Exact cleanup conditions](https://github.com/thelegendtubaguy/Valve-Oil/blob/c89dddc475b73e060027ff5a2489239df1b14406/installer/klipper/extras/klipper_health.py#L146-L182).

Likewise, the whole `klipper_fixes.py` module is not portable by assumption. It hashes functions from the newer QIDI fork and skips mismatches. A concrete difference: the Plus4's `invoke_async_shutdown(self, msg)` does not have the required `details` parameter that Valve Oil's compatibility wrapper supplies. The source-matching principle is valuable; that particular wrapper is not demonstrated as a missing Plus4 fix. [Source guards](https://github.com/thelegendtubaguy/Valve-Oil/blob/c89dddc475b73e060027ff5a2489239df1b14406/installer/klipper/extras/klipper_fixes.py#L154-L224), [Valve Oil wrapper](https://github.com/thelegendtubaguy/Valve-Oil/blob/c89dddc475b73e060027ff5a2489239df1b14406/installer/klipper/extras/klipper_fixes.py#L251-L258), [Plus4 signature](https://github.com/QIDITECH/klipper/blob/4bb7c6337936ef273e621d1f55bc0ef92114785d/klippy/klippy.py#L263-L265).

### C-helper backports: investigate source, do not copy binaries

The four patches free expired pressure-advance allocations, correct a homing-timeout comparison, repair an out-of-bounds step-queue write and close leaked serial-queue pipe descriptors. Valve Oil links each change to its upstream Klipper commit. These are credible correctness candidates rather than generic speed tuning. [Patch index and upstream provenance](https://github.com/thelegendtubaguy/Valve-Oil/blob/c89dddc475b73e060027ff5a2489239df1b14406/chelper/README.md#L3-L14).

However, Valve Oil rebuilds an August 2024 source snapshot for its supported arm64 Debian bullseye environment and admits one exact stock library hash. The Plus4 uses an older fork/runtime; this review did not establish whether each vulnerable source pattern exists in its helper. Audit that source and rebuild its exact target before considering installation. Do not copy `c_helper.so`, overwrite source timestamps to force loading, or infer compatibility from the shared Klipper version family. [Build environment and checks](https://github.com/thelegendtubaguy/Valve-Oil/blob/c89dddc475b73e060027ff5a2489239df1b14406/chelper/README.md#L16-L32), [Library path and hash admission](https://github.com/thelegendtubaguy/Valve-Oil/blob/c89dddc475b73e060027ff5a2489239df1b14406/installer/runtime/klipper_chelper.py#L23-L55).

## Other useful adaptations

- **Per-slot Spoolman accounting:** use the loaded Box slot to choose the active spool and record consumption. This is an integration feature, not another printer firmware patch. [Spoolman guide](https://github.com/thelegendtubaguy/Valve-Oil/blob/c89dddc475b73e060027ff5a2489239df1b14406/docs/spoolman.md), [implementation](https://github.com/thelegendtubaguy/Valve-Oil/blob/c89dddc475b73e060027ff5a2489239df1b14406/installer/klipper/extras/spoolman.py).
- **Print-start options:** minimum chamber readiness and staged heating can be borrowed independently of the model-specific homing/cutting/parking macros. [Start policy](https://github.com/thelegendtubaguy/Valve-Oil/blob/c89dddc475b73e060027ff5a2489239df1b14406/docs/print-start.md#L43-L82).
- **Prime handoff:** retaining the nozzle prime until the first real extrusion could improve ooze and first-line behavior, but requires adapting our KAMP purge and extrusion modes. [Implementation](https://github.com/thelegendtubaguy/Valve-Oil/blob/c89dddc475b73e060027ff5a2489239df1b14406/installer/klipper/extras/prime_handoff.py).
- **Bed-soak analysis:** a useful future way to determine thermal stabilization time; it actively heats and probes and is not a passive diagnostic to run during this review. [Tool behavior](https://github.com/thelegendtubaguy/Valve-Oil/blob/c89dddc475b73e060027ff5a2489239df1b14406/docs/tools.md#L137-L173).

The current Fluidd/Box interface is useful but was already identified through Grease. Stock load-cell probe fixes, Max 4 closed-loop step-loss monitoring, model-specific speed caps, third-party RFID support and board firmware are not direct Plus4 additions. The Box firmware manifest is based on a newer validated image and bootloader; the existence of a QIDI Box alone does not make its image interchangeable with a Plus4's. [Box image and shutdown fix](https://github.com/thelegendtubaguy/Valve-Oil/blob/c89dddc475b73e060027ff5a2489239df1b14406/firmware/BOX_FIRMWARE.md#L1-L30).

Source provenance should be preserved when implementing an adaptation. Valve Oil's repository-authored code is GPLv3; review the destination's license and third-party notices before copying code. [License](https://github.com/thelegendtubaguy/Valve-Oil/blob/c89dddc475b73e060027ff5a2489239df1b14406/LICENSE), [notices](https://github.com/thelegendtubaguy/Valve-Oil/blob/c89dddc475b73e060027ff5a2489239df1b14406/THIRD_PARTY_NOTICES.md).

## Implementation follow-up

The saved-variable improvement is now available through hlab's opt-in
`printer firmware fixes --fast-variable-saves` transaction for reviewed stock
Plus4 1.8.2/2.1.1 sources. It covers `SAVE_VARIABLE` and the stock Box direct-save
method, skips unchanged writes, flushes file and directory around atomic
replacement, and preserves QIDI's serialization/default semantics. Installation
and rollback do not restore or migrate runtime variable values. Tests compare
file bytes and status with QIDI's original handler and exercise write failures,
source admission, transaction binding, idempotence and rollback. See
[hlab's maintained extension](https://github.com/cl-tim/hlab/blob/main/internal/printerlab/migration/qidi-fixes/save_variables_fast.py).

The Box heater follow-up confirmed the Plus4 host's ten-second configured
output timeout. Synthetic calls to the stock host code produced unchanged-output
intervals of 7.6–7.7 seconds with the tested sensor schedules. A synthetic failure
in the compiled AHT20 callback also propagated after simulated shutdown. This
makes the shutdown guard a relevant candidate and the faster refresh plausible
additional margin, but does not establish a real heater-refresh fault or an
independent firmware watchdog deadline. No heater behaviour was changed. The
[focused review and adoption boundary](https://github.com/cl-tim/hlab/blob/main/docs/plus4-box-heater-refresh.md)
keeps refresh, shutdown handling, PWM tuning and firmware flashing distinct.
