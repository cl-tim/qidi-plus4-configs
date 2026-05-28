; Recommended OrcaSlicer Machine Start G-code for the
; QIDI-XPlus4-With-Beacon config without QIDI Box.
;
; Keep this minimal: PRINT_START already handles Beacon-sensitive probing,
; heating, chamber behavior, nozzle cleaning/wiping, and sensor setup.

PRINT_START BED=[bed_temperature_initial_layer_single] HOTEND=[first_layer_temperature] CHAMBER=[overall_chamber_temperature]
SET_PRINT_STATS_INFO TOTAL_LAYER=[total_layer_count]
M83
