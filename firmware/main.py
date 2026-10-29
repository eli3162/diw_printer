'''
        Copyright (C) 2026 Ethan Li

        This program is free software: you can redistribute it and/or modify
        it under the terms of the GNU General Public License as published by
        the Free Software Foundation, either version 3 of the License, or
        (at your option) any later version.

        This program is distributed in the hope that it will be useful,
        but WITHOUT ANY WARRANTY; without even the implied warranty of
        MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
        GNU General Public License for more details.

        You should have received a copy of the GNU General Public License
        along with this program.  If not, see <https://www.gnu.org/licenses/>.
'''
import time
from pyscript import when, window, document
from js import console # type: ignore

def timenow():
    return time.ticks_us()

log_to_terminal = False
message_cache = []
last_message = None
log_cache = []
last_log = None

starting_command = """
import os, asyncio, sys, time
writeSerial(os.uname().machine + '; ' + os.uname().version)
printer = printerdriver.initPrinter()
printer.main_extruder.extrude_ratio = printerdriver.syringenozzle(nozzle_diameter=0.75)
"""

async def writeSerial(message: str):
    await window.writeSerial(str(message))


async def receiveSerial(message):
    global message_cache, last_message, log_cache, last_log, log_to_terminal
    if message.startswith("send:"):
        message = message[5:]
        message_cache.append({"message": message, "time": timenow()})
        print(message)
        last_message = message

    elif not message is None:
        log_cache.append({"message": message, "time": timenow()})
        console.log(message)
        if log_to_terminal:
            print(f'Log: {message}')
        last_log = message

window.receiveFromSerial = receiveSerial

async def connectSerial():
    await window.connectSerial()

@when("click", "#connect")
async def connect_handler(event):
    global starting_command
    await connectSerial()
    await writeSerial(starting_command)

@when("click", "#disconnect")
async def disconnect_handler(event):
    window.location.reload()

@when("click", "#gcode-input")
async def gcode_handler(event):
    gcode = document.getElementById("gcode-upload").value
    payload = f'printer.run_gcode("""{gcode}""")'
    print(f'GCode payload: {payload}')
    await writeSerial(payload)

@when("click", "#py-input")
async def py_handler(event):
    python = (document.getElementById("py-upload").value).strip() + '\n'
    await writeSerial(python)

@when("mousedown", "#w")
async def w_on_press(event):
    payload = 'printer.y_motor.start_turn(360, 0)'
    print(payload)
    await writeSerial(payload)

@when("mouseup", "#w")
async def w_on_release(event):
    payload = 'printer.y_motor.stop_turn()'
    print(payload)
    await writeSerial(payload)


@when("mousedown", "#a")
async def w_on_press(event):
    payload = 'printer.x_motor.start_turn(360, 1)'
    print(payload)
    await writeSerial(payload)

@when("mouseup", "#a")
async def w_on_release(event):
    payload = 'printer.x_motor.stop_turn()'
    print(payload)
    await writeSerial(payload)


@when("mousedown", "#d")
async def w_on_press(event):
    payload = 'printer.x_motor.start_turn(360, 0)'
    print(payload)
    await writeSerial(payload)

@when("mouseup", "#d")
async def w_on_release(event):
    payload = 'printer.x_motor.stop_turn()'
    print(payload)
    await writeSerial(payload)

@when("mousedown", "#s")
async def w_on_press(event):
    payload = 'printer.y_motor.start_turn(360, 1)'
    print(payload)
    await writeSerial(payload)

@when("mouseup", "#s")
async def w_on_release(event):
    payload = 'printer.y_motor.stop_turn()'
    print(payload)
    await writeSerial(payload)

