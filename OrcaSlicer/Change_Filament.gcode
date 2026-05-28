; OrcaSlicer Change Filament G-code for QIDI Box in-print tool changes.
;
; Keep this close to Orca/QIDI's default. This is where the slicer's flush
; volumes are applied during color changes, and it coordinates the Box cut,
; unload, load, purge, clear, and TOOL_CHANGE_END sequence.

{if max_layer_z < 12}
G1 Z15 F1200
{else}
G1 Z{max_layer_z + 3.0} F1200
{endif}
TOOL_CHANGE_START F=[previous_extruder] T=[next_extruder]
DISABLE_ALL_SENSOR
{if long_retractions_when_cut[previous_extruder]}
MOVE_TO_TRASH
G1 E-{retraction_distances_when_cut[previous_extruder]} F{old_filament_e_feedrate}
M400
{else}
G1 E-5 F{old_filament_e_feedrate}
{endif}
CUT_FILAMENT T=[previous_extruder]
MOVE_TO_TRASH
M400
{if nozzle_temperature_range_high[previous_extruder] >= nozzle_temperature_range_high[next_extruder]}
M104 S{nozzle_temperature_range_high[previous_extruder]}
{else}
M104 S{nozzle_temperature_range_high[next_extruder]}
{endif}
M106 S0
M106 P2 S0
UNLOAD_T[previous_extruder]
G92 E0
M83
G1 E2 F50
T[next_extruder]
{if nozzle_temperature_range_high[previous_extruder] >= nozzle_temperature_range_high[next_extruder]}
SET_HEATER_TEMPERATURE HEATER=extruder TARGET={nozzle_temperature_range_high[previous_extruder]} WAIT=1
{else}
SET_HEATER_TEMPERATURE HEATER=extruder TARGET={nozzle_temperature_range_high[next_extruder]} WAIT=1
{endif}
{if long_retractions_when_cut[previous_extruder]}
G1 E{retraction_distances_when_cut[previous_extruder]} F{old_filament_e_feedrate}
{endif}
M400
M106 S60
; FLUSH_START
G1 E1 F50
G1 E{65.5 * 0.58} F{old_filament_e_feedrate}
G1 E{65.5 * 0.02} F50
G1 E{65.5 * 0.18} F{old_filament_e_feedrate}
G1 E{65.5 * 0.02} F50
G1 E{65.5 * 0.18} F{old_filament_e_feedrate}
G1 E{65.5 * 0.02} F50
G1 E-[old_retract_length_toolchange] F1800
; FLUSH_END
{if flush_length_1 > 1}
M400
M106 S255
G91
G1 X-5 F60
G1 X5 F60
G90
CLEAR_FLUSH
M400
M106 S60
; FLUSH_START
G1 E[old_retract_length_toolchange] F300
G1 E{flush_length_1 * 0.58} F{new_filament_e_feedrate}
G1 E{flush_length_1 * 0.02} F50
G1 E{flush_length_1 * 0.18} F{new_filament_e_feedrate}
G1 E{flush_length_1 * 0.02} F50
G1 E{flush_length_1 * 0.18} F{new_filament_e_feedrate}
G1 E{flush_length_1 * 0.02} F50
G1 E-[old_retract_length_toolchange] F1800
; FLUSH_END
{endif}
{if flush_length_2 > 1}
M400
M106 S255
G91
G1 X-5 F60
G1 X5 F60
G90
CLEAR_FLUSH
M400
M106 S60
; FLUSH_START
G1 E[old_retract_length_toolchange] F300
G1 E{flush_length_2 * 0.58} F{new_filament_e_feedrate}
G1 E{flush_length_2 * 0.02} F50
G1 E{flush_length_2 * 0.18} F{new_filament_e_feedrate}
G1 E{flush_length_2 * 0.02} F50
G1 E{flush_length_2 * 0.18} F{new_filament_e_feedrate}
G1 E{flush_length_2 * 0.02} F50
G1 E-[new_retract_length_toolchange] F1800
; FLUSH_END
{endif}
{if flush_length_3 > 1}
M400
M106 S255
G91
G1 X-5 F60
G1 X5 F60
G90
CLEAR_FLUSH
M400
M106 S60
; FLUSH_START
G1 E[new_retract_length_toolchange] F300
G1 E{flush_length_3 * 0.58} F{new_filament_e_feedrate}
G1 E{flush_length_3 * 0.02} F50
G1 E{flush_length_3 * 0.18} F{new_filament_e_feedrate}
G1 E{flush_length_3 * 0.02} F50
G1 E{flush_length_3 * 0.18} F{new_filament_e_feedrate}
G1 E{flush_length_3 * 0.02} F50
G1 E-[new_retract_length_toolchange] F1800
; FLUSH_END
{endif}
{if flush_length_4 > 1}
M400
M106 S255
G91
G1 X-5 F60
G1 X5 F60
G90
CLEAR_FLUSH
M400
M106 S60
; FLUSH_START
G1 E[new_retract_length_toolchange] F300
G1 E{flush_length_4 * 0.58} F{new_filament_e_feedrate}
G1 E{flush_length_4 * 0.02} F50
G1 E{flush_length_4 * 0.18} F{new_filament_e_feedrate}
G1 E{flush_length_4 * 0.02} F50
G1 E{flush_length_4 * 0.18} F{new_filament_e_feedrate}
G1 E{flush_length_4 * 0.02} F50
G1 E-[new_retract_length_toolchange] F1800
; FLUSH_END
{endif}
M104 S[new_filament_temp]
M400
M106 S255
G91
G1 X-5 F60
G1 X5 F60
G90
M109 S[new_filament_temp]
G92 E0
M400
CLEAR_FLUSH
CLEAR_OOZE
M400
M106 S0
TOOL_CHANGE_END
G1 Y305 F9000
ENABLE_ALL_SENSOR
