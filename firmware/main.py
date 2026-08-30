from js import window
from pyscript import document, web
import asyncio

connected_status = web.page['connect']
printer_connected = False
lastmessage = ''

def display(message):
    output = document.querySelector("#output")
    output.textContent += str(message) + "\n"

async def send_to_pico(message):
    message = str(message)
    global printer_connected, connected_status
    if printer_connected:
        if not message == 'Heartbeat':
            display("CLIENT:" + message)
    try:
        await window.writeSerial(message)
    except Exception as e:
        connected_status.textContent = 'Connect Printer - Not Connected'
        if printer_connected:
            display('DISCONNECTED')
        printer_connected = False

def receive_from_pico(message):
    global lastmessage
    message = str(message)
    if not message.startswith('ECHO:'):
        display("SERVER:" + message)
    lastmessage = message

window.receiveFromPico = receive_from_pico

async def connect(event=None):
    global printer_connected, lastmessage
    await window.connectPico()
    await check_if_disconnected()

async def check_if_disconnected():
    global printer_connected, lastmessage, connected_status
    try:
        await send_to_pico('Heartbeat')
    except Exception as e:
        pass
    await asyncio.sleep(0.1)
    if lastmessage == 'ECHO:Heartbeat':
        connected_status.textContent = 'Printer Connected!'
        if not printer_connected:
            display("CONNECTED") 
        printer_connected = True
    else:
        connected_status.textContent = 'Connect Printer - Not Connected'
        if printer_connected:
            display("DISCONNECTED")
        printer_connected = False

async def check():
    while True:
        await check_if_disconnected()
        await asyncio.sleep(5)

async def send_button(event=None):
    message = document.querySelector("#message").value
    await send_command(message)

async def send_command(command):
    return await send_to_pico('serverexecutable:'+command)

document.querySelector("#connect").onclick = connect
document.querySelector("#send").onclick = send_button

asyncio.create_task(check())