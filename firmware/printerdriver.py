'''
# printerdriver.py
 ©2026 Ethan Li
Micropython firmware for driving stepper motors with the DRV8825 module.
'''

import asyncio
import math

import machine  # type: ignore


class StepperMotor:
    '''
    # Stepper Motor
    Stepper Motor Class, configurable with three pins: the **EN** / Enable pin, the **STEP** / Step pin, and the **DIRECTION** / Dir pin.
    Additional config to change the amount of steps needed for a full rotation: `steps_per_turn`
    '''
    def __init__(self, enable_pin: int | str, step_pin: int | str, dir_pin: int | str, steps_per_turn: int = 200):
        self.enable_pin = int(enable_pin)
        self.step_pin = int(step_pin)
        self.dir_pin = int(dir_pin)
        self.steps_per_turn = steps_per_turn
        self.control_pins = {
            self.enable_pin: machine.Pin(self.enable_pin, machine.Pin.OUT, value=1),
            self.step_pin: machine.Pin(self.step_pin, machine.Pin.OUT, value=0),
            self.dir_pin: machine.Pin(self.dir_pin, machine.Pin.OUT, value=0)
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

    async def step_turn(self, steps: int, freq: float, direction: str | bool | int | None = None):
        if direction in ['forward', 'Forward', 1, True, 'f']:
            self.set_direction(1)
        elif direction in ['backward', 'Backward', 0, False, 'b']:
            self.set_direction(0)
        elif direction == None:
            pass
        else:
            raise ValueError(f'Invalid Direction: {direction}')
        
        if direction == None or steps < 0:
            if steps > 0:
                self.set_direction(1)
            elif steps < 0:
                self.set_direction(0)
                steps = -1 * steps
            else:
                return
            
        self.freq_timer = machine.Timer(-1)
        self.deinit_timer = machine.Timer(-1)
        self.freq_timer.init(mode=machine.Timer.PERIODIC, freq=freq, callback=self.step)
        self.deinit_timer.init(mode=machine.Timer.ONE_SHOT, period=round(1000*steps/freq), callback=self.stop_timer)
        await asyncio.sleep(steps/freq)
        return

    async def turn(self, degrees: float, time: float, direction: str | bool | int | None = None):
        if degrees:
            steps = math.floor((degrees / 360)*self.steps_per_turn)
            await self.step_turn(steps, steps/time, direction)
            return
        else:
            return

class XYZsystem:
    '''
    # XYZ System
    Printer Control System, takes 3 stepper motors as input: `x_motor`, `y_motor`, and `z_motor`, and can be moved arount to any coordinate on the print bed.
    '''
    def __init__(self, x_motor: StepperMotor, y_motor: StepperMotor, z_motor: StepperMotor):
        self.x_motor = x_motor
        self.y_motor = y_motor
        self.z_motor = z_motor
    
    async def movetorelative(self, time: float, x: float = 0, y: float = 0, z: float = 0):
        horizontal_conversion_const = 360/(16 * math.pi)
        vertical_conversion_const = 360/8
        x_degrees = x * horizontal_conversion_const
        y_degrees = y * horizontal_conversion_const
        z_degrees = z * vertical_conversion_const
        print([x_degrees, y_degrees, z_degrees, time])
        await asyncio.gather(
            self.x_motor.turn(x_degrees, time, 'forward'), 
            self.y_motor.turn(y_degrees, time, 'forward'),
            self.z_motor.turn(z_degrees, time, 'forward')
        )

x_motor = StepperMotor(enable_pin=0, step_pin=1, dir_pin=2)
y_motor = StepperMotor(enable_pin=3, step_pin=4, dir_pin=5)
z_motor = StepperMotor(enable_pin=6, step_pin=7, dir_pin=8)

