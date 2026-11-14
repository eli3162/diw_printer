import re

gcode_spec_list = {
    'G0': 'linear_move',
    'G1': 'linear_move',
    'G2': 'clockwise_arc',
    'G3': 'counterclockwise_arc',
    'G4': 'dwell',
    'G10': 'retract_filament',
    'G11': 'unretract_filament',
    'G20': 'units_inch',
    'G21': 'units_mm',
    'G28': 'home',
    'G90': 'absolute_pos',
    'G91': 'relative_pos',
    'G92': 'set_pos',
    'M0': 'stop',
    'M1': 'sleep',
    'M2': 'prgm_end',
    'M3': 'clockwise_spindle_on',
    'M4': 'counterclockwise_spindle_on',
    'M5': 'spindle_off',
    'M18': 'disable_motors',
    'M20': 'list_sd',
    'M21': 'init_sd',
    'M22': 'deinit_sd',
    'M23': 'select_sd',
    'M24': 'start_sd_print',
    'M25': 'pause_sd_print',
    'M26': 'pos_sd',
    'M27': 'check_sd',
    'M28': 'start_sd_write',
    'M29': 'stop_sd_write',
    'M30': 'delete_sd_file',
    'M32': 'start_sd_file_print',
    'M42': 'set_pin',
    'M82': 'absolute_extruder',
    'M83': 'relative_extruder',
    'M84': 'disable_idle_hold',
    'M104': 'set_extruder_temp',
    'M105': 'get_extruder_temp',
    'M106': 'fan_on',
    'M107': 'fan_off',
    'M108': 'bed_heating_off',
    'M109': 'extruder_heat_wait',
    'M112': 'emergency_stop',
    'M114': 'get_pos',
    'M115': 'get_firmware',
    'M140': 'fast_bed_heating',
    'M150': 'led_color',
    'M190': 'wait_bed_heating',
    'M300': 'beep',
}

def parse(inputdata):
    if not isinstance(inputdata, tuple):
        if isinstance(inputdata, str):
            inputdata = tuple([inputdata])
        elif isinstance(inputdata, list):
            inputdata = tuple(inputdata)

    output = []
    for line in inputdata:
        if ";" in line:
            line = line.split(";", 1)[0]

        if "(" in line and ")" in line:
            line = re.sub(r"\(.*?\)", "", line)

        phrases = line.split(" ")
        while "" in phrases:
            phrases.remove("")

        if phrases:
            command = phrases.pop(0).upper()
            raw_arguments = phrases
            arguments = {}
            for argument in raw_arguments:
                if "'" in argument[1:] or '"' in argument[1:]:
                    arguments[argument[:1].lower()] = argument[1:]
                else:
                    arguments[argument[:1].lower()] = float(argument[1:])
            if command or arguments:
                if command in gcode_spec_list:
                    name = gcode_spec_list[command]
                else:
                    name = 'Not Implemented'

                output.append({"command": command, "name": name, "args": arguments})

    return output

if __name__ == '__main__':
    unknown = []
    used = []
    with open("gcode.gcode", "r", encoding="utf-8") as file:
        for line in file:
            parsed_line = parse(line)
            if parsed_line and parsed_line[0]['name'] == 'Not Implemented' and not parsed_line[0]['command'] in unknown:
                unknown.append(parsed_line[0]['command'])
            if parsed_line and not parsed_line[0]['name'] in used:
                used.append(parsed_line[0]['name'])

    print(unknown)
    print(used)
            