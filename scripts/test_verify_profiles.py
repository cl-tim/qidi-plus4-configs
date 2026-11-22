"""Regression checks for the deployable Box profile, using temporary copies."""
from pathlib import Path
import tempfile
import unittest

import verify_profiles as profiles


class RunoutTests(unittest.TestCase):
    def test_both_profiles_use_300_for_tilt_and_mesh(self):
        for name in (profiles.QIDI_FIRMWARE_PROFILE, profiles.MAINLINE_PROFILE):
            errors = []
            profiles.validate_probe_speeds(profiles.PRINTERS_ROOT / name, errors)
            self.assertFalse(errors)

    def test_all_flags_without_dwell_and_other_waits_are_retained(self):
        source = profiles.PRINTERS_ROOT / profiles.QIDI_FIRMWARE_PROFILE
        errors = []
        profiles.validate_qidi_firmware_macro_safety(source, errors)
        self.assertEqual(errors, [])
        text = (source / 'gcode_macro.cfg').read_text()
        self.assertIn('G4 P5000', text)

    def test_guard_rejects_reintroduced_wait_or_missing_flag_saves(self):
        source = (profiles.PRINTERS_ROOT / profiles.QIDI_FIRMWARE_PROFILE / 'gcode_macro.cfg').read_text()
        for modified in (source.replace('VALUE=0\n        {% endfor %}', 'VALUE=0\n            G4 P100\n        {% endfor %}', 1),
                         source.replace('range(16)', 'range(8)', 1),
                         source.replace('SAVE_VARIABLE VARIABLE=runout_{i} VALUE=0', 'M400', 1)):
            with self.subTest(), tempfile.TemporaryDirectory() as name:
                root = Path(name)
                (root / 'gcode_macro.cfg').write_text(modified)
                errors = []
                profiles.validate_qidi_firmware_macro_safety(root, errors)
                self.assertTrue(any('all 16 runout flags' in error for error in errors), errors)


if __name__ == '__main__':
    unittest.main()
