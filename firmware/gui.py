from js import window, console # type: ignore
from pyscript import document, web # type: ignore
import asyncio, time

connected_status = web.page['connect']
printer_connected = False
lastmessage = ''
runspeedtest = True

def display(message, clear=False):
    output = document.querySelector("#output")
    if not clear:
        output.textContent += str(message) + "\n"
    else:
        output.textContent = str(message)

async def send_to_printer(message):
    message = str(message)
    global printer_connected, connected_status
    if printer_connected:
        console.log('CLIENT:'+str(message))
    try:
        await window.writeSerial(message)
    except Exception as e:
        connected_status.textContent = 'Connect Printer - Not Connected'
        if printer_connected:
            display('DISCONNECTED')
        printer_connected = False

async def receive_from_printer(message):
    console.log(str(message))
    global lastmessage
    message = str(message)
    if not message.startswith('ECHO:') and not message == 'CMDOUT:None' and not message.startswith('clientexecutable:'):
        display(message)
    if message.startswith('clientexecutable:'):
        command = message[17:]
        try:
            output = await exec(command)
        except Exception as e:
            output = e
        await send_to_printer('CMDOUT:'+str(output))
    lastmessage = message

window.receiveFromPico = receive_from_printer

async def connect(event=None):
    global printer_connected, lastmessage, runspeedtest
    await window.connectPico()
    await check_if_disconnected()
    if printer_connected:
        display('', clear=True)
        await send_command('import os, sys')
        await send_command('device_info = os.uname()')
        await send_command('print(sys.version, device_info.machine)')
        if runspeedtest:
            await speed_test()

async def check_if_disconnected():
    global printer_connected, lastmessage, connected_status
    try:
        await send_to_printer('ECHO:Heartbeat')
    except Exception as e:
        connected_status.textContent = 'Connect Printer - Not Connected'
        if printer_connected:
            display("DISCONNECTED")
        printer_connected = False
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
    await send_to_printer('ECHO:Refresh')

async def check():
    while True:
        await check_if_disconnected()
        await asyncio.sleep(5)

async def send_button(event=None):
    message = document.querySelector("#message").value
    await send_command(message)

async def send_command(command):
    return await send_to_printer('serverexecutable:'+command)

async def speed_test():
    global lastmessage
    times = []
    payload = ''
    payload_size = 2048
    iteration_count = 100
    console.log(f'Start Speed Test - Config: Payload size: {payload_size}, Iteration Count: {iteration_count}')
    for p in range(payload_size):
        payload = payload + '0'
    for i in range(iteration_count):
        deltatime = time.ticks_us()
        await send_to_printer('ECHO:'+payload+str(i))
        while not lastmessage == 'ECHO:'+payload+str(i):
            await asyncio.sleep(0.01)
        times.append(time.ticks_diff(time.ticks_us(), deltatime))
    count = 0
    for c in range(len(times)):
        count = count + times[c]/1000000
    count = count/len(times)
    console.log(f'Connection Speed: {round((2*payload_size/count)/1000, 2)} kB/s')
    display(f'Connection Speed: {round((2*payload_size/count)/1000, 2)} kB/s')


document.querySelector("#connect").onclick = connect
document.querySelector("#send").onclick = send_button

asyncio.create_task(check())
