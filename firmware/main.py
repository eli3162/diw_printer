from js import window
from pyscript import document
import asyncio

def display(message):
    output = document.querySelector("#output")
    output.textContent += str(message) + "\n"

async def send_to_pico(message):
    message = str(message)
    display("CLIENT:" + message)
    await window.writeSerial(message)

def receive_from_pico(message):
    message = str(message)
    display("SERVER:" + message)

window.receiveFromPico = receive_from_pico

async def connect(event=None):
    await window.connectPico()
    display("CONNECTED")

async def send_button(event=None):
    message = document.querySelector("#message").value
    await send_to_pico(message)

async def send_command(command):
    return await send_to_pico('serverexecutable:'+command)

document.querySelector("#connect").onclick = connect
document.querySelector("#send").onclick = send_button
