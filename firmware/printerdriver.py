"""
# printerdriver.py
 ©2026 Ethan Li
Micropython firmware for driving stepper motors with the DRV8825 module.
"""

import asyncio
import math
import re
import gc

import machine  # pyright: ignore[reportMissingImports]


class MachineError(Exception):
    """Base Class for Physical Machine based Errors"""


class StepperMotor:
    """
    # Stepper Motor
    Stepper Motor Class, configurable with three pins: the **EN** / Enable pin, the **STEP** / Step pin, and the **DIR** / Direction pin.
    Additional config to change the amount of steps needed for a <u>full rotation</u>: `steps_per_turn`
    """

    def __init__(
        self,
        enable_pin: int | str,
        step_pin: int | str,
        dir_pin: int | str,
        steps_per_turn: int = 200,
    ):
        self.enable_pin = enable_pin
        self.step_pin = step_pin
        self.dir_pin = dir_pin
        self.steps_per_turn = steps_per_turn
        self.control_pins = {
            self.enable_pin: machine.Pin(self.enable_pin, machine.Pin.OUT, value=1),
            self.step_pin: machine.Pin(self.step_pin, machine.Pin.OUT, value=0),
            self.dir_pin: machine.Pin(self.dir_pin, machine.Pin.OUT, value=0),
        }

    def digital_write(self, pin: int, value: int):
        self.control_pins[pin].value(value)

    def start(self):
        self.digital_write(self.enable_pin, 0)

    def stop(self):
        self.digital_write(self.enable_pin, 1)

    def set_direction(self, dir: int):
        self.digital_write(self.dir_pin, dir)

    def step(self, time):
        self.digital_write(self.step_pin, 1)
        self.digital_write(self.step_pin, 0)

    def stop_timer(self, time):
        self.freq_timer.deinit()
        self.deinit_timer.deinit()

    def stop_turn(self):
        self.stop()
        self.freq_timer.deinit()

    async def step_turn(
        self, steps: int, freq: float, direction: str | bool | int | None = None
    ):
        if direction in ["forward", "Forward", 1, True, "f"]:
            self.set_direction(1)
        elif direction in ["backward", "Backward", 0, False, "b"]:
            self.set_direction(0)
        elif direction == None:
            pass
        else:
            raise ValueError(f"Invalid Direction: {direction}")

        if direction is None or steps < 0:
            if steps > 0:
                self.set_direction(1)
            elif steps < 0:
                self.set_direction(0)
                steps = -1 * steps
            else:
                return
        try:
            self.start()
            self.freq_timer = machine.Timer(-1)
            self.deinit_timer = machine.Timer(-1)
            self.freq_timer.init(
                mode=machine.Timer.PERIODIC, freq=freq, callback=self.step
            )
            self.deinit_timer.init(
                mode=machine.Timer.ONE_SHOT,
                period=round(1000 * steps / freq),
                callback=self.stop_timer,
            )
            await asyncio.sleep(steps / freq)
            self.stop()
        except KeyboardInterrupt:
            self.stop_timer(0)
            self.stop()
            try:
                self.freq_timer.deinit()
                self.deinit_timer.deinit()
            except Exception:
                pass
        return

    def start_step_turn(
        self, steps: int, freq: float, direction: str | bool | int | None = None
    ):
        if direction in ["forward", "Forward", 1, True, "f"]:
            self.set_direction(1)
        elif direction in ["backward", "Backward", 0, False, "b"]:
            self.set_direction(0)
        elif direction == None:
            pass
        else:
            raise ValueError(f"Invalid Direction: {direction}")

        if direction is None or steps < 0:
            if steps > 0:
                self.set_direction(1)
            elif steps < 0:
                self.set_direction(0)
                steps = -1 * steps
            else:
                return
        self.start()
        self.freq_timer = machine.Timer(-1)
        self.freq_timer.init(mode=machine.Timer.PERIODIC, freq=freq, callback=self.step)
        return

    async def turn(
        self, degrees: float, time: float, direction: str | bool | int | None = None
    ):
        if degrees:
            steps = math.floor((degrees / 360) * self.steps_per_turn)
            await self.step_turn(steps, steps / time, direction)
            return
        else:
            return

    def start_turn(self, degrees: float, direction: str | bool | int | None = None):
        if degrees:
            time = 1
            steps = math.floor((degrees / 360) * self.steps_per_turn)
            self.start_step_turn(steps, steps / time, direction)
            return
        else:
            return

    def turn_step(self, degrees, time, direction):
        asyncio.run(self.turn(degrees, time, direction=direction))


class EndButton:
    """
    # End Button
    3d printer End Button, takes 1 pin location as input: `pin`
    """

    def __init__(self, pin):
        self.pin_obj = machine.Pin(pin, machine.Pin.IN, machine.Pin.PULL_UP)

    def state(self):
        """
        Gets Digital State of button or pin
        """
        if self.pin_obj.value() == 0:
            return False
        elif self.pin_obj.value() == 1:
            return True
        else:
            return False


class GCodeParser:
    def __init__(self, matchlist: dict | None = None):
        if matchlist:
            self.matchlist = matchlist
        else:
            self.matchlist = {}

    def parseline(self, line: str):
        if ";" in line:
            line = line.split(";", 1)[0]

        if "(" in line and ")" in line:
            line = re.sub(r"\(.*?\)", "", line)

        phrases = line.split(" ")
        while "" in phrases:
            phrases.remove("")

        try:
            if phrases:
                command = phrases.pop(0).upper()
                raw_arguments = phrases

                arguments = {}
                for argument in raw_arguments:
                    if "'" in argument[1:] or '"' in argument[1:]:
                        arguments[argument[:1].lower()] = argument[1:]
                    else:
                        arguments[argument[:1].lower()] = float(argument[1:])

                if command in self.matchlist:
                    command = self.matchlist[command]

                return {"command": command, "args": arguments}
        except Exception:
            pass
        return {"command": "", "args": {}}

    def parse(self, inputdata: str | list):
        if isinstance(inputdata, str):
            if inputdata.count("\n") > 1:
                inputdata = inputdata.splitlines()
            else:
                return self.parseline(inputdata)

        if isinstance(inputdata, list):
            output = []
            for line in inputdata:
                parsedline = self.parseline(line)
                if not parsedline == {"command": "", "args": {}}:
                    output.append(parsedline)
            return output


class Printer:
    """
    # Printer
    Printer Control System, takes 3 stepper motors as input: `x_motor`, `y_motor`, and `z_motor`, 3 optional end button inputs as `x_limit`, `y_limit`, and `z_limit`, and can be moved around to any coordinate on the print bed.
    """

    def __init__(
        self,
        x_motor: StepperMotor,
        y_motor: StepperMotor,
        z_motor: StepperMotor,
        x_limit: EndButton = None,
        y_limit: EndButton = None,
        z_limit: EndButton = None,
    ):
        self.x_motor = x_motor
        self.y_motor = y_motor
        self.z_motor = z_motor
        if x_limit:
            self.x_limit = x_limit

        if y_limit:
            self.y_limit = y_limit

        if z_limit:
            self.z_limit = z_limit

        self.pos = {"x": 0, "y": 0, "z": 0}

        self.matchlist = None

        self.gcodeparser = GCodeParser(matchlist=self.matchlist)

        self.last_feed_rate = 0

    def setpos(
        self, x: float | None = None, y: float | None = None, z: float | None = None
    ):
        """
        # Set Pos:
        Set Virtual control system position with optional `x`, `y`, and `z` values
        """
        if not x is None:
            self.pos["x"] = x
        if not y is None:
            self.pos["y"] = y
        if not z is None:
            self.pos["z"] = z

    def signed_direction(self, angle):
        if angle > 0:
            direction = 1
        if angle <= 0:
            direction = 0
        return [abs(angle), direction]

    async def movetorelative(
        self,
        time: float | None = None,
        speed: float | None = None,
        x: float = 0,
        y: float = 0,
        z: float = 0,
    ):
        """
        # Move to Relative
        Moves to position `x, y, z` relative to current control coordinates
        """
        horizontal_conversion_const = 360 / (16 * math.pi)
        vertical_conversion_const = 360 / 8
        x = -x
        y = -y
        x_degrees = x * horizontal_conversion_const
        y_degrees = y * horizontal_conversion_const
        z_degrees = z * vertical_conversion_const
        [x_degrees, x_direction] = self.signed_direction(x_degrees)
        [y_degrees, y_direction] = self.signed_direction(y_degrees)
        [z_degrees, z_direction] = self.signed_direction(z_degrees)

        if time and speed:
            raise MachineError("User may not choose both time and speed inputs")
        elif time:
            runtime = time
        elif speed:
            distance = math.sqrt(x**2 + y**2 + z**2)
            runtime = distance / speed
        else:
            raise MachineError("User speed or time not specified")

        await asyncio.gather(
            self.x_motor.turn(x_degrees, runtime, direction=x_direction),
            self.y_motor.turn(y_degrees, runtime, direction=y_direction),
            self.z_motor.turn(z_degrees, runtime, direction=z_direction),
        )

    def getpos(self):
        """
        # Get Pos
        Get current printer position as tuple: `(x, y, z)`
        """
        return (self.pos["x"], self.pos["y"], self.pos["z"])

    async def asyncmovetopoint(self, point, time=None, speed=None):
        [start_x, start_y, start_z] = self.getpos()
        [end_x, end_y, end_z] = point
        movement_vector = (end_x - start_x, end_y - start_y, end_z - start_z)
        [x, y, z] = movement_vector
        self.setpos(x=end_x, y=end_y, z=end_z)
        await self.movetorelative(time=time, speed=speed, x=x, y=y, z=z)

    def moveto(
        self,
        time: float | None = None,
        speed: float | None = None,
        x: float = 0,
        y: float = 0,
        z: float = 0,
        e: float = 0,
    ):
        """
        # Move To
        Move to a point on with the control system, use `time` or `speed` as a setting, and optional coordinates `x`, `y`, and `z`.
        """
        point = (x, y, z)
        if time or speed:
            asyncio.run(self.asyncmovetopoint(point, time=time, speed=speed))

    def software_home(self):
        """
        # Home
        Returns to (0, 0, 0) with the control system
        """
        self.moveto(speed=100, x=0, y=0, z=0)

    def runcodeline(self, pycode: str):
        command = pycode["command"]
        arguments = pycode["args"]
        if command in "G0":
            arguments["speed"] = 150
            self.moveto(**arguments)

        elif command in "G1":
            if "f" in arguments:
                arguments["speed"] = arguments["f"]
                self.last_feed_rate = arguments["f"]
                arguments.pop("f")

            elif self.last_feed_rate:
                arguments["speed"] = self.last_feed_rate

            else:
                arguments["speed"] = 150

            self.moveto(**arguments)

        elif command in "G28":
            self.hone_axis()

        elif command in "G92":
            if 'e' in arguments:
                arguments.pop('e')

            self.setpos(**arguments)

    def run_gcode(self, gcode: str | list):
        """
        Run specified Gcode
        """
        parsed_gcode = self.gcodeparser.parse(gcode)
        if isinstance(parsed_gcode, list):
            for line in parsed_gcode:
                self.runcodeline(line)
                gc.collect()
        else:
            self.runcodeline(parsed_gcode)

    def hone_axis(self):
        """
        Uses Limitswitches to hone axis to origin
        """
        printer = self
        printer.z_motor.turn_step(720 * 2, 4, "forward")
        printer.x_motor.start_turn(260, "forward")
        printer.y_motor.start_turn(260, "forward")
        printer.z_motor.start_turn(260, "backward")

        x_calib, y_calib, z_calib = False, False, False

        while not x_calib or not y_calib or not z_calib:
            if printer.x_limit.state():
                x_calib = True
                printer.x_motor.stop_turn()

            if printer.y_limit.state():
                y_calib = True
                printer.y_motor.stop_turn()

            if printer.z_limit.state():
                z_calib = True
                printer.z_motor.stop_turn()

        asyncio.run(printer.movetorelative(time=2, z=20))
        asyncio.run(printer.movetorelative(time=2, x=50, y=50))
        asyncio.run(printer.movetorelative(time=5, z=-20))
        printer.setpos(x=0, y=0, z=0)


class Extruder:
    """
    # Printer
    Printer Control System, takes 3 stepper motors as input: `x_motor`, `y_motor`, and `z_motor`, 3 optional end button inputs as `x_limit`, `y_limit`, and `z_limit`, and can be moved around to any coordinate on the print bed.
    """

    def __init__(self, extruder_motor: StepperMotor):
        self.extruder_motor = extruder_motor

    async def extrude(
        self, mm: float, time: float, direction: str | bool | int | None = None
    ):
        if mm:
            degrees = None
            steps = math.floor((degrees / 360) * self.steps_per_turn)
            await self.step_turn(steps, steps / time, direction)
            return
        else:
            return


if __name__ == "__main__":
    x_motor = StepperMotor(enable_pin=0, step_pin=1, dir_pin=2)
    y_motor = StepperMotor(enable_pin=3, step_pin=4, dir_pin=5)
    z_motor = StepperMotor(enable_pin=6, step_pin=7, dir_pin=8)
    extruder_main = StepperMotor(enable_pin=9, step_pin=10, dir_pin=11)
    extruder_secondary = StepperMotor(enable_pin=12, step_pin=13, dir_pin=14)
    extruder_auxilary = StepperMotor(enable_pin=15, step_pin=16, dir_pin=17)
    x_button = EndButton(pin=21)
    y_button = EndButton(pin=22)
    z_button = EndButton(pin=26)
    printer = Printer(x_motor, y_motor, z_motor, x_button, y_button, z_button)
    gcode = """
G90                      ; set absolute positioning mode
M83                      ; set relative positioning for extruder
G28                      ; home axes
G92 X0 Y0 Z0 E0          ; reset all axes positions
G1 X0 Y0 Z0.25 F180      ; move xy to 0,0 and z 0.25mm over bed
G92 E0                   ; zero the extruder
G1 F225                  ; set feed speed
G1 E-1.5000 F2400 ; e-retract 1.5
;; --- layer 0 (0.250 @ 0.255) ---
G1 Z0.2550 F4800
; feature brim
G1 X27.4812 Y28.3722
G1 E1.5000 F2400 ; e-engage 1.5
G4 P20
G1 X29.1292 Y26.7242 E0.0951 F1800
G1 Y0.5703 E1.0675
G1 X27.4812 Y-1.0777 E0.0951
G1 X1.3273 E1.0675
G1 X-0.3208 Y0.5703 E0.0951
G1 Y26.7242 E1.0675
G1 X1.3273 Y28.3722 E0.0951
G1 X27.4812 E1.0675
G1 X27.3155 Y27.9723 F4800
G1 X28.7292 Y26.5585 E0.0816 F1800
G1 Y0.7360 E1.0540
G1 X27.3155 Y-0.6778 E0.0816
G1 X1.4930 E1.0540
G1 X0.0793 Y0.7360 E0.0816
G1 Y26.5585 E1.0540
G1 X1.4930 Y27.9723 E0.0816
G1 X27.3155 E1.0540
G1 E-1.5000 F2400 ; e-retract 1.5
G1 Z0.4550 F4800 ; z-hop start
; start object id: 101
; feature shells
M106 S0
G1 X14.4042 Y23.8301
G1 Z0.2550 ; z-hop end
G1 E1.5000 F2400 ; e-engage 1.5
G4 P20
G1 X24.5861 Y13.6472 E0.5878 F1800
G1 X14.4042 Y3.4654 E0.5877
G1 X4.2224 Y13.6472 E0.5877
G1 X14.4042 Y23.8301 E0.5878
G1 Y24.3958 F4800
G1 X25.1517 Y13.6472 E0.6204 F1800
G1 X14.4042 Y2.8997 E0.6204
G1 X3.6567 Y13.6472 E0.6204
G1 X14.4042 Y24.3958 E0.6204
G1 X14.2150 Y24.7722 F4800
G1 X3.2792 Y13.8354 E0.6313 F1800
G1 Y24.7722 E0.4464
G1 X14.2150 E0.4464
G1 X2.8792 Y25.1722 F4800
G1 X25.9292 E0.9408 F1800
G1 Y2.1223 E0.9408
G1 X2.8792 E0.9408
G1 Y25.1722 E0.9408
G1 X2.4792 Y25.5644 F4800
G1 X2.4871 Y25.5723 E0.0005 F1800
G1 X26.3214 E0.9728
G1 X26.3292 Y25.5644 E0.0005
G1 Y1.7301 E0.9728
G1 X26.3214 Y1.7222 E0.0005
G1 X2.4871 E0.9728
G1 X2.4792 Y1.7301 E0.0005
G1 Y25.5644 E0.9728
G1 X14.5935 Y24.7722 F4800
G1 X25.5292 E0.4464 F1800
G1 Y13.8354 E0.4464
G1 X14.5935 Y24.7722 E0.6313
G1 X3.2792 Y13.4590 F4800
G1 X14.2160 Y2.5222 E0.6313 F1800
G1 X3.2792 E0.4464
G1 Y13.4590 E0.4464
G1 X14.5925 Y2.5222 F4800
G1 X25.5292 Y13.4590 E0.6313 F1800
G1 Y2.5222 E0.4464
G1 X14.5925 E0.4464
; feature solid fill
G1 X15.6526 Y2.7823 F4800
G1 X25.2692 Y12.3989 E0.6939 F2100
"""
    printer.run_gcode(gcode)
