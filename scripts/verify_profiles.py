#!/usr/bin/env python3
"""Validate the sanitized, Klippee-backed printer profiles."""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PRINTERS_ROOT = REPO_ROOT / "printers"
INCLUDE_RE = re.compile(r"^\s*\[include\s+(.+?)\]\s*(?:#.*)?$")
SAVE_CONFIG_RE = re.compile(r"^#\*#\s+<.*SAVE_CONFIG", re.MULTILINE)
BY_ID_RE = re.compile(r"/dev/serial/by-id/")
TOKEN_RE = re.compile("klp_" + r"[A-Za-z0-9_-]{20,}")
WINDOWS_USER_PATH_RE = re.compile(r"[A-Za-z]:\\Users\\", re.IGNORECASE)
CFG_SECTION_RE = re.compile(r"^\s*\[([^]]+)]\s*(?:#.*)?$")
EXPECTED_MANAGED_COUNTS = {"qidi1": 16, "qidi2": 10}
EXPECTED_DEVICE_PLACEHOLDERS = {
    "qidi1": {"CHANGE_ME_QIDI1_BEACON_SERIAL", "CHANGE_ME_QIDI1_BOX_SERIAL"},
    # The firmware repository's render-config command consumes this exact token.
    "qidi2": {"CHANGE_ME_BEACON_SERIAL"},
}


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def load_metadata(profile_dir: Path, errors: list[str]) -> dict[str, object]:
    path = profile_dir / "profile.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(errors, f"{path.relative_to(REPO_ROOT)}: invalid metadata: {exc}")
        return {}

    required = {
        "schemaVersion",
        "id",
        "printerName",
        "firmwareMode",
        "klippeeAppliedVersion",
        "verifiedAt",
        "managedFiles",
        "devicePlaceholders",
        "volatilePrivateExclusions",
    }
    missing = sorted(required - data.keys())
    if missing:
        fail(errors, f"{path.relative_to(REPO_ROOT)}: missing keys {missing}")
    if data.get("id") != profile_dir.name:
        fail(errors, f"{path.relative_to(REPO_ROOT)}: id must equal {profile_dir.name!r}")
    if not isinstance(data.get("klippeeAppliedVersion"), int):
        fail(errors, f"{path.relative_to(REPO_ROOT)}: klippeeAppliedVersion must be an integer")
    try:
        datetime.fromisoformat(str(data.get("verifiedAt")))
    except ValueError:
        fail(errors, f"{path.relative_to(REPO_ROOT)}: verifiedAt must be ISO-8601")
    return data


def validate_includes(profile_dir: Path, cfg_files: set[str], errors: list[str]) -> None:
    for relative in sorted(cfg_files):
        source = profile_dir / relative
        for line_number, line in enumerate(source.read_text(encoding="utf-8").splitlines(), 1):
            match = INCLUDE_RE.match(line)
            if not match:
                continue
            include = match.group(1).strip().replace("\\", "/")
            matches = list(source.parent.glob(include))
            if not matches:
                fail(
                    errors,
                    f"{source.relative_to(REPO_ROOT)}:{line_number}: missing include {include!r}",
                )


def load_cfg_sections(path: Path) -> dict[str, str]:
    sections: dict[str, list[str]] = {}
    current: str | None = None
    for line in path.read_text(encoding="utf-8").splitlines():
        match = CFG_SECTION_RE.match(line)
        if match:
            current = match.group(1).strip().lower()
            sections[current] = []
        elif current is not None:
            sections[current].append(line)
    return {name: "\n".join(lines) for name, lines in sections.items()}


def macro_lines(body: str) -> list[str]:
    return [
        line.split("#", 1)[0].strip()
        for line in body.splitlines()
        if line.split("#", 1)[0].strip()
    ]


def validate_qidi1_macro_safety(profile_dir: Path, errors: list[str]) -> None:
    path = profile_dir / "gcode_macro.cfg"
    sections = load_cfg_sections(path)
    required = {
        "gcode_macro _move_to_chute",
        "gcode_macro _move_to_chute_homed",
        "gcode_macro clear_nozzle_plr",
        "gcode_macro resume_print",
        "gcode_macro m107",
    }
    missing = sorted(required - sections.keys())
    if missing:
        fail(errors, f"qidi1: missing safety macros {missing}")
        return

    chute = sections["gcode_macro _move_to_chute"]
    chute_lines = macro_lines(chute)
    try:
        home_index = chute_lines.index("_CG28")
        move_index = chute_lines.index("_MOVE_TO_CHUTE_HOMED")
    except ValueError:
        fail(errors, "qidi1: _MOVE_TO_CHUTE must home, then call _MOVE_TO_CHUTE_HOMED")
    else:
        if move_index <= home_index:
            fail(errors, "qidi1: _MOVE_TO_CHUTE_HOMED must run after _CG28")
    if "printer.gcode_move.position" in chute:
        fail(errors, "qidi1: _MOVE_TO_CHUTE must not evaluate position before homing")

    homed_chute = sections["gcode_macro _move_to_chute_homed"]
    if "printer.gcode_move.position.x" not in homed_chute or "printer.gcode_move.position.y" not in homed_chute:
        fail(errors, "qidi1: _MOVE_TO_CHUTE_HOMED must evaluate the post-home X/Y position")

    plr_lines = macro_lines(sections["gcode_macro clear_nozzle_plr"])
    if not plr_lines or plr_lines[-1].upper() != "M400":
        fail(errors, "qidi1: CLEAR_NOZZLE_PLR must end with M400")

    resume = sections["gcode_macro resume_print"]
    if "_MOVE_TO_CHUTE" not in macro_lines(resume):
        fail(errors, "qidi1: RESUME_PRINT must use the guarded _MOVE_TO_CHUTE route")
    if re.search(r"(?im)^\s*G[01]\s+X95\b[^\n]*\n\s*G[01]\s+Y324\b", resume):
        fail(errors, "qidi1: RESUME_PRINT contains an unsafe direct purge-chute approach")

    m107 = sections["gcode_macro m107"]
    if not re.search(r"params\.P\|default\(0\)\|int", m107):
        fail(errors, "qidi1: M107 must default to QIDI fan port P0")
    if "M106 P{p} S0" not in macro_lines(m107):
        fail(errors, "qidi1: M107 must route P0/P2/P3 shutdown through M106")


def validate_qidi1_plr_contract(profile_dir: Path, errors: list[str]) -> None:
    path = profile_dir / "plr.cfg"
    sections = load_cfg_sections(path)
    power_section = "gcode_shell_command power_loss_resume"
    resume_section = "gcode_macro resume_interrupted"

    if power_section not in sections:
        fail(errors, "qidi1: POWER_LOSS_RESUME shell command is missing")
    else:
        power_options = [
            line
            for line in macro_lines(sections[power_section])
            if line.lower().startswith(("command:", "timeout:"))
        ]
        expected_options = [
            "command: bash /home/mks/scripts/plr/plr.sh",
            "timeout: 120",
        ]
        if power_options != expected_options:
            fail(
                errors,
                "qidi1: POWER_LOSS_RESUME must run /home/mks/scripts/plr/plr.sh "
                "with timeout 120",
            )

    if "gcode_shell_command update_gcode_lines" in sections:
        fail(errors, "qidi1: obsolete UPDATE_GCODE_LINES shell command is still configured")

    active_lines = macro_lines(path.read_text(encoding="utf-8"))
    if any("update_gcode_lines" in line.lower() for line in active_lines):
        fail(errors, "qidi1: obsolete UPDATE_GCODE_LINES reference is still active")

    if resume_section not in sections:
        fail(errors, "qidi1: RESUME_INTERRUPTED macro is missing")
    else:
        resume_lines = macro_lines(sections[resume_section])
        if resume_lines.count("RUN_SHELL_COMMAND CMD=POWER_LOSS_RESUME") != 1:
            fail(errors, "qidi1: RESUME_INTERRUPTED must invoke POWER_LOSS_RESUME exactly once")


def validate_qidi1_box_safety(profile_dir: Path, errors: list[str]) -> None:
    box_path = profile_dir / "box.cfg"
    box_sections = load_cfg_sections(box_path)
    motion_section = "filament_motion_sensor box_motion_sensor"
    if motion_section not in box_sections:
        fail(errors, "qidi1: Box motion sensor section is missing")
    else:
        motion_lines = macro_lines(box_sections[motion_section])
        if not any(re.fullmatch(r"use_irq\s*:\s*false", line, re.IGNORECASE) for line in motion_lines):
            fail(errors, "qidi1: Box motion sensor must use the bounded polled path")
        if any(re.match(r"debounce_us\s*:", line, re.IGNORECASE) for line in motion_lines):
            fail(errors, "qidi1: IRQ-only Box debounce_us must not remain configured")

    override_path = profile_dir / "box_overrides.cfg"
    override_sections = load_cfg_sections(override_path)
    required = {
        "box_output_clock_guard",
        "gcode_macro reload_all",
        "gcode_macro qidi_box_auto_insert_enable",
        "gcode_macro qidi_box_auto_insert_disable",
    }
    missing = sorted(required - override_sections.keys())
    if missing:
        fail(errors, f"qidi1: missing Box stability sections {missing}")
        return

    reload_all = override_sections["gcode_macro reload_all"]
    reload_lines = macro_lines(reload_all)
    required_fragments = (
        "rename_existing: _QIDI_RELOAD_ALL",
        "params.RFID|default(0)|int",
        "qidi_box_auto_insert|default(0)|int",
        "_QIDI_RELOAD_ALL {rawparams}",
    )
    for fragment in required_fragments:
        if fragment not in reload_all:
            fail(errors, f"qidi1: RELOAD_ALL safety wrapper is missing {fragment!r}")
    if not any("automatic and not enabled" in line for line in reload_lines):
        fail(errors, "qidi1: RELOAD_ALL must default automatic insertion to quarantined")

    enable = override_sections["gcode_macro qidi_box_auto_insert_enable"]
    disable = override_sections["gcode_macro qidi_box_auto_insert_disable"]
    if "SAVE_VARIABLE VARIABLE=qidi_box_auto_insert VALUE=1" not in macro_lines(enable):
        fail(errors, "qidi1: automatic Box insertion enable macro must persist its opt-in")
    if "SAVE_VARIABLE VARIABLE=qidi_box_auto_insert VALUE=0" not in macro_lines(disable):
        fail(errors, "qidi1: automatic Box insertion disable macro must persist its opt-out")


def validate_profile(profile_dir: Path, errors: list[str]) -> None:
    metadata = load_metadata(profile_dir, errors)
    if not metadata:
        return

    listed = metadata.get("managedFiles")
    if not isinstance(listed, list) or not all(isinstance(item, str) for item in listed):
        fail(errors, f"{profile_dir.name}: managedFiles must be a string list")
        return
    managed = set(listed)
    if len(managed) != len(listed):
        fail(errors, f"{profile_dir.name}: managedFiles contains duplicates")
    expected_count = EXPECTED_MANAGED_COUNTS[profile_dir.name]
    if len(managed) != expected_count:
        fail(errors, f"{profile_dir.name}: expected {expected_count} managed files, found {len(managed)}")

    actual = {
        path.relative_to(profile_dir).as_posix()
        for path in profile_dir.rglob("*.cfg")
        if path.is_file()
    }
    if managed != actual:
        fail(
            errors,
            f"{profile_dir.name}: managed file mismatch; missing={sorted(managed - actual)}, "
            f"unlisted={sorted(actual - managed)}",
        )

    if profile_dir.name == "qidi2" and any("/" in relative for relative in managed):
        fail(errors, "qidi2: runtime .cfg files must remain flat for --profile-dir rendering")

    combined = "\n".join(
        (profile_dir / relative).read_text(encoding="utf-8") for relative in sorted(actual)
    )
    if SAVE_CONFIG_RE.search(combined):
        fail(errors, f"{profile_dir.name}: generated SAVE_CONFIG marker found")
    if BY_ID_RE.search(combined):
        fail(errors, f"{profile_dir.name}: real /dev/serial/by-id path found")
    if TOKEN_RE.search(combined):
        fail(errors, f"{profile_dir.name}: Klippee-style token found")
    if WINDOWS_USER_PATH_RE.search(combined):
        fail(errors, f"{profile_dir.name}: personal Windows user path found")

    placeholders = metadata.get("devicePlaceholders")
    if not isinstance(placeholders, list) or not all(isinstance(item, str) for item in placeholders):
        fail(errors, f"{profile_dir.name}: devicePlaceholders must be a string list")
    else:
        expected_placeholders = EXPECTED_DEVICE_PLACEHOLDERS[profile_dir.name]
        if set(placeholders) != expected_placeholders:
            fail(
                errors,
                f"{profile_dir.name}: devicePlaceholders must be {sorted(expected_placeholders)}",
            )
        for placeholder in placeholders:
            count = combined.count(placeholder)
            if count != 1:
                fail(errors, f"{profile_dir.name}: placeholder {placeholder!r} appears {count} times")

    generated = profile_dir / "klippee-macros.cfg"
    if generated.exists() and "Managed by klippee install-moonraker" not in generated.read_text(
        encoding="utf-8"
    ):
        fail(errors, f"{profile_dir.name}: klippee-macros.cfg lost its generated-file marker")

    validate_includes(profile_dir, actual, errors)
    if profile_dir.name == "qidi1":
        validate_qidi1_macro_safety(profile_dir, errors)
        validate_qidi1_plr_contract(profile_dir, errors)
        validate_qidi1_box_safety(profile_dir, errors)


def validate_repository_state(errors: list[str]) -> None:
    for path in REPO_ROOT.rglob("*"):
        if ".git" in path.parts:
            continue
        if ".klippee" in path.parts:
            fail(errors, f"private Klippee state present: {path.relative_to(REPO_ROOT)}")
        if path.name in {"last-sync", "last-sync-files", "saved_variables.cfg"}:
            fail(errors, f"private runtime state present: {path.relative_to(REPO_ROOT)}")

    for cfg in [*PRINTERS_ROOT.rglob("*.cfg"), *(REPO_ROOT / "reference").rglob("*.cfg")]:
        text = cfg.read_text(encoding="utf-8")
        if SAVE_CONFIG_RE.search(text):
            fail(errors, f"generated SAVE_CONFIG marker found: {cfg.relative_to(REPO_ROOT)}")
        if BY_ID_RE.search(text):
            fail(errors, f"real /dev/serial/by-id path found: {cfg.relative_to(REPO_ROOT)}")


def main() -> int:
    errors: list[str] = []
    if not PRINTERS_ROOT.is_dir():
        print("printers/ is missing", file=sys.stderr)
        return 1

    profiles = sorted(path for path in PRINTERS_ROOT.iterdir() if path.is_dir())
    if {path.name for path in profiles} != {"qidi1", "qidi2"}:
        fail(errors, f"expected only qidi1 and qidi2 profiles, found {[path.name for path in profiles]}")
    for profile in profiles:
        validate_profile(profile, errors)
    validate_repository_state(errors)

    if errors:
        print("Profile verification failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    counts = ", ".join(
        f"{profile.name}={len(json.loads((profile / 'profile.json').read_text())['managedFiles'])} files"
        for profile in profiles
    )
    print(f"Profile verification passed ({counts}).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
