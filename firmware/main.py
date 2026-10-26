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
