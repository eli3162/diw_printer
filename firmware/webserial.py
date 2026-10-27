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
