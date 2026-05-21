; Recommended OrcaSlicer Machine End G-code for the
; QIDI-XPlus4-With-Beacon config without QIDI Box.
;
; PRINT_END already handles heater/fan shutdown, sensor disable, mesh cleanup,
; last-file cleanup, and steppers.

G1 E-3 F1800
G0 Z{min(max_print_height, max_layer_z + 3)} F600
G0 X15 Y290 F12000
G4 P2000
TIMELAPSE_TAKE_FRAME
G4 P2000
{if max_layer_z < max_print_height / 2}G1 Z{max_print_height / 2 + 10} F600{else}G1 Z{min(max_print_height, max_layer_z + 3)}{endif}
PRINT_END
