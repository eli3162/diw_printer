py_header = '''
# Machine Generated using gcodeparser.py
import printerdriver
printer = printerdriver.initPrinter()
printer.main_extruder.extrude_ratio = printerdriver.syringenozzle(nozzle_diameter=0.75)
'''

def generate_py(gcode: str, speed: float):
    [latestx, latesty, lateste] = (0, 0, 0)
    payload = py_header.splitlines()
    for line in gcode:
        [x, y, e] = (line[0], line[1], line[2])
        payloadline = 'printer.moveto('
        if not latestx is x:
            payloadline = payloadline + f'x={x:.2f},'
        if not latesty is y:
            payloadline = payloadline + f'y={y:.2f},'
        if not lateste is e:
            payloadline = payloadline + f'e={y:.2f},'
        payloadline = payloadline + f'speed={speed})'
        payload.append(payloadline)
        [latestx, latesty, lateste] = (x, y, e)
    with open("rungcode.py", "w", encoding="utf-8") as file:
        file.write('\n'.join(payload).lstrip())
    print('\n'.join(payload).lstrip())
    return ('\n'.join(payload).lstrip())


def generate_gcode(gcode: str, speed: float):
    [latestx, latesty, lateste, payload, addspeed] = (0, 0, 0, list(), True)
    for line in gcode:
        [x, y, e] = (line[0], line[1], line[2])
        payloadline = 'G1 '
        if not latestx is x:
            payloadline = payloadline + f'X{x:.2f} '
        if not latesty is y:
            payloadline = payloadline + f'Y{y:.2f} '
        if not lateste is e:
            payloadline = payloadline + f'E{y:.2f} '
        if addspeed:
            payloadline = payloadline + f'F{speed} '
            addspeed = False
        payload.append(payloadline)
        [latestx, latesty, lateste] = (x, y, e)
    with open("rungcode.gcode", "w", encoding="utf-8") as file:
        file.write('\n'.join(payload))
    print('\n'.join(payload))
    return ('\n'.join(payload).lstrip())
