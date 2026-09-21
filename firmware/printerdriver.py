"""
# printerdriver.py
 ©2026 Ethan Li
Micropython firmware for driving stepper motors with the DRV8825 module.
"""

import asyncio
import math

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
        self.start()
        self.freq_timer = machine.Timer(-1)
        self.deinit_timer = machine.Timer(-1)
        self.freq_timer.init(mode=machine.Timer.PERIODIC, freq=freq, callback=self.step)
        self.deinit_timer.init(
            mode=machine.Timer.ONE_SHOT,
            period=round(1000 * steps / freq),
            callback=self.stop_timer,
        )
        await asyncio.sleep(steps / freq)
        self.stop()
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


class EndButton:
    """
    # End Button
    3d printer End Button, takes 1 pin location as input: `pin`
    """

    def __init__(self, pin):
        self.pin_obj = machine.Pin(pin, machine.Pin.IN, machine.Pin.PULL_UP)

    def state(self):
        if self.pin_obj.value():
            return False
        elif self.pin_obj.value() == 1:
            return True
        else:
            raise MachineError("Button Indeterminate state")


class ThreeAxisControlSystem:
    """
    # Three Axis Control System
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

    def setpos(self, x=None, y=None, z=None):
        if x:
            self.pos["x"] = x
        if y:
            self.pos["y"] = y
        if z:
            self.pos["z"] = z

    def signed_direction(self, angle):
        if angle > 0:
            direction = 1
        if angle <= 0:
            direction = 0
        return [abs(angle), direction]

    async def movetorelative(
        self, time: float, x: float = 0, y: float = 0, z: float = 0
    ):
        horizontal_conversion_const = 360 / (16 * math.pi)
        vertical_conversion_const = 360 / 8
        x_degrees = -x * horizontal_conversion_const
        y_degrees = -y * horizontal_conversion_const
        z_degrees = z * vertical_conversion_const
        [x_degrees, x_direction] = self.signed_direction(x_degrees)
        [y_degrees, y_direction] = self.signed_direction(y_degrees)
        [z_degrees, z_direction] = self.signed_direction(z_degrees)

        await asyncio.gather(
            self.x_motor.turn(x_degrees, time, direction=x_direction),
            self.y_motor.turn(y_degrees, time, direction=y_direction),
            self.z_motor.turn(z_degrees, time, direction=z_direction),
        )

    def getpos(self):
        return (self.pos["x"], self.pos["y"], self.pos["z"])

    async def asyncmovetopoint(self, point, time):
        [start_x, start_y, start_z] = self.getpos()
        [end_x, end_y, end_z] = point
        movement_vector = (end_x - start_x, end_y - start_y, end_z - start_z)
        [x, y, z] = movement_vector
        self.setpos(x=end_x, y=end_y, z=end_z)
        await self.movetorelative(time, x=x, y=y, z=z)

    def moveto(self, time: float = 0, x: float = 0, y: float = 0, z: float = 0):
        point = (x, y, z)
        if time:
            asyncio.run(self.asyncmovetopoint(point, time))


if __name__ == "__main__":
    x_motor = StepperMotor(enable_pin=0, step_pin=1, dir_pin=2)
    y_motor = StepperMotor(enable_pin=3, step_pin=4, dir_pin=5)
    z_motor = StepperMotor(enable_pin=6, step_pin=7, dir_pin=8)
    x_button = EndButton(pin=21)
    y_button = EndButton(pin=22)
    z_button = EndButton(pin=26)

    control_system = ThreeAxisControlSystem(
        x_motor, y_motor, z_motor, x_limit=x_button, y_limit=y_button, z_limit=z_button
    )

    control_system.moveto(x=0, y=75, z=0, time=1)
    control_system.moveto(x=75, y=75, z=0, time=1)
    control_system.moveto(x=75, y=0, z=0, time=1)
    control_system.moveto(x=0, y=75, z=0, time=1)
