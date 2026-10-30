import sys
import select
import printerdriver

poll_object = select.poll()
poll_object.register(sys.stdin, select.POLLIN)

def receiveSerial(timeout: int = 10):
    events = poll_object.poll(timeout)
    if events:
        message = sys.stdin.splitlines()
        if isinstance(message, (list, tuple)):
            message = "\n".join(message)
            return message
        else:
            message = message.strip()
            return message
    

def writeSerial(message):
    print(f'send:{message}')
    
def listenSerialExec(timeout: int = 100):
    while True:
        message = receiveSerial(timeout = timeout)
        if not message is None:
            print(message)
            try:
                stout = exec(message)
                if not stout is None:
                    writeSerial(stout)
            except Exception as e:
                stout = e
                writeSerial(stout)
                
listenSerialExec()