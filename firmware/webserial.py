from js import window  # type: ignore

from serialcom import localtime

message_cache = []


async def writeSerial(message: str):
    await window.writeSerial(str(message))


async def receiveSerial(message):
    global message_cache, last_message
    message_cache.append({"message": message, "time": localtime()})
    last_message = message


window.receiveFromSerial = receiveSerial


async def connectSerial():
    await window.connectSerial()
