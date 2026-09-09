from js import window, console # type: ignore
from serialcom import localtime

message_cache = []

async def writeSerial(message: str):
    await window.writeSerial(str(message))

async def receiveSerial(message):
    global message_cache
    message_cache.append({'message': message, 'time': localtime()})

window.receiveFromSerial = receiveSerial

async def connectSerial():
    await window.connectSerial()

