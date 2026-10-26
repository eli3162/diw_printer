"""
# printerdriver.py
 ©2026 Ethan Li
Micropython firmware for driving stepper motors with the DRV8825 module.
Additional Classes for ease of 3d printer control.
"""

import asyncio
import math
import re

import machine


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
        return self.pin_obj.value() == 1


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
                if parsedline != {"command": "", "args": {}}:
                    output.append(parsedline)
            return output


class Extruder:
    """
    # Extruder
    Extruder Class object, takes input of extrusion ratio: `ratio` as `int | float` and extuder motor: `extuder_motor` as class `StepperMotor`
    """

    def __init__(self, extruder_motor: StepperMotor, ratio: float = 1):
        self.extruder_motor = extruder_motor
        self.extrude_ratio = ratio
        self.steps_per_turn = 360 / 1.8

    async def extrude(
        self, mm: float, time: float, direction: str | bool | int | None = None
    ):
        if mm:
            degrees = 360 * mm
            steps = math.floor(
                ((degrees / 360) * self.steps_per_turn) * self.extrude_ratio
            )
            await self.extruder_motor.step_turn(steps, steps / time, direction)
            return
        else:
            return


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
        main_extruder: Extruder = None,
        secondary_extruder: Extruder = None,
        auxilarry_extruder: Extruder = None,
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

        if main_extruder or secondary_extruder or auxilarry_extruder:
            self.extruder_set = {
                "main": main_extruder,
                "secondary": secondary_extruder,
                "auxilarry": auxilarry_extruder,
            }

        [self.main_extruder, self.secondary_extruder, self.auxillary_extruder] = (
            main_extruder,
            secondary_extruder,
            auxilarry_extruder,
        )

        self.pos = {"x": 0, "y": 0, "z": 0}
        self.matchlist = None
        self.gcodeparser = GCodeParser(matchlist=self.matchlist)
        self.last_feed_rate = 0

    def writeSerial(message):
        print(f"send:{message}")

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
        e: float = 0,
    ):
        """
        # Move to Relative
        Moves to position `x, y, z` relative to current control coordinates
        """
        horizontal_conversion_const = 360 / (16 * math.pi)
        vertical_conversion_const = 360 / 8
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
            self.main_extruder.extrude(e, runtime, direction=0),
        )

    def getpos(self):
        """
        # Get Software Position
        Get current printer position as tuple: `(x, y, z)`
        """
        return (self.pos["x"], self.pos["y"], self.pos["z"])

    async def asyncmovetopoint(
        self, point: list | tuple, time: float = None, speed: float = None
    ):
        [start_x, start_y, start_z] = self.getpos()
        [end_x, end_y, end_z, extrude] = point
        movement_vector = (end_x - start_x, end_y - start_y, end_z - start_z)
        [x, y, z] = movement_vector
        self.setpos(x=end_x, y=end_y, z=end_z)
        await self.movetorelative(time=time, speed=speed, x=x, y=y, z=z, e=extrude)

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
        point = (x, y, z, e)
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
            if "e" in arguments:
                arguments.pop("e")

            self.setpos(**arguments)

    def run_gcode(self, gcode: str | list):
        """
        Run Gcode
        Run specified Gcode
        """
        parsed_gcode = self.gcodeparser.parse(gcode)
        if isinstance(parsed_gcode, list):
            for line in parsed_gcode:
                self.runcodeline(line)
        else:
            self.runcodeline(parsed_gcode)

    def hone_axis(self):
        """
        Uses Limitswitches to hone axis to origin
        """
        # \\ TODO !


def initPrinter(setpins: dict | None = None):
    """
    # initPrinter
    initPrinter() initializes a default printer configaration, and returns a `Printer` control object. Can **optionally** specify PIN CONFIGARATION:
    Default Pin config:
    ```
        pins = {
            'x_motor': {'en': 0, 'step': 1, 'dir': 2},
            'y_motor': {'en': 3, 'step': 4, 'dir': 5},
            'z_motor': {'en': 6, 'step': 7, 'dir': 8},
            'extruder_main': {'en': 9, 'step': 10, 'dir': 11, 'ratio': 1},
            'extruder_secondary': {'en': 12, 'step': 13, 'dir': 14, 'ratio': 1},
            'extruder_auxilarry': {'en': 15, 'step': 16, 'dir': 17, 'ratio': 1},
            'x_limit': {'pin': 21},
            'y_limit': {'pin': 22},
            'z_limit': {'pin': 26},
            'aux': {'sda': 23, 'scl': 24, 'pwm': 25}
        }
    ```
    """
    if not setpins is None:
        pins = setpins
    else:
        pins = {
            "x_motor": {"en": 0, "step": 1, "dir": 2},
            "y_motor": {"en": 3, "step": 4, "dir": 5},
            "z_motor": {"en": 6, "step": 7, "dir": 8},
            "extruder_main": {"en": 9, "step": 10, "dir": 11, "ratio": 1},
            "extruder_secondary": {"en": 12, "step": 13, "dir": 14, "ratio": 1},
            "extruder_auxilarry": {"en": 15, "step": 16, "dir": 17, "ratio": 1},
            "x_limit": {"pin": 21},
            "y_limit": {"pin": 22},
            "z_limit": {"pin": 26},
            "aux": {"sda": 23, "scl": 24, "pwm": 25},
        }

    x_motor = StepperMotor(
        enable_pin=pins["x_motor"]["en"],
        step_pin=pins["x_motor"]["step"],
        dir_pin=pins["x_motor"]["dir"],
    )
    y_motor = StepperMotor(
        enable_pin=pins["y_motor"]["en"],
        step_pin=pins["y_motor"]["step"],
        dir_pin=pins["y_motor"]["dir"],
    )
    z_motor = StepperMotor(
        enable_pin=pins["z_motor"]["en"],
        step_pin=pins["z_motor"]["step"],
        dir_pin=pins["z_motor"]["dir"],
    )

    extruder_main_motor = StepperMotor(
        enable_pin=pins["extruder_main"]["en"],
        step_pin=pins["extruder_main"]["step"],
        dir_pin=pins["extruder_main"]["dir"],
    )
    extruder_secondary_motor = StepperMotor(
        enable_pin=pins["extruder_secondary"]["en"],
        step_pin=pins["extruder_secondary"]["step"],
        dir_pin=pins["extruder_secondary"]["dir"],
    )
    extruder_auxilarry_motor = StepperMotor(
        enable_pin=pins["extruder_auxilarry"]["en"],
        step_pin=pins["extruder_auxilarry"]["step"],
        dir_pin=pins["extruder_auxilarry"]["dir"],
    )

    extruder_main = Extruder(extruder_main_motor, ratio=pins["extruder_main"]["ratio"])
    extruder_secondary = Extruder(
        extruder_secondary_motor, ratio=pins["extruder_secondary"]["ratio"]
    )
    extruder_auxilarry = Extruder(
        extruder_auxilarry_motor, ratio=pins["extruder_auxilarry"]["ratio"]
    )

    x_button = EndButton(pin=pins["x_limit"]["pin"])
    y_button = EndButton(pin=pins["y_limit"]["pin"])
    z_button = EndButton(pin=pins["z_limit"]["pin"])

    printer = Printer(
        x_motor,
        y_motor,
        z_motor,
        x_button,
        y_button,
        z_button,
        extruder_main,
        extruder_secondary,
        extruder_auxilarry,
    )
    return printer


def syringenozzle(
    nozzle_diameter: float = 1.5, syringe_diameter: float = 10.5, screw_pitch: float = 2
):
    '''
    Syringe Nozzle:
    Calculates how much to turn the stepper motor as a ratio with optional inputs of `nozzle_diameter` in mm, 'syringe_diameter' in mm, and `screw pitch` in mm per turn.
    '''
    return screw_pitch * (nozzle_diameter**2 / syringe_diameter**2)
