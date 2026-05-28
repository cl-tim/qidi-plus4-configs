; Recommended OrcaSlicer Machine Start G-code for the live
; QIDI-XPlus4-With-Beacon-And-Box Klipper config.
;
; Keep this minimal: PRINT_START already handles Box startup, Beacon-sensitive
; probing, heating, chamber behavior, nozzle cleaning/wiping, and sensor setup.

PRINT_START BED=[bed_temperature_initial_layer_single] HOTEND=[first_layer_temperature] CHAMBER=[overall_chamber_temperature] EXTRUDER=[initial_no_support_extruder]
SET_PRINT_STATS_INFO TOTAL_LAYER=[total_layer_count]
M83
