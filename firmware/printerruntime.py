from gcodetranslator import gcodeparser
import printerdriver, multiprocessing, pathlib, subprocess, time
from printerdriver import xpos, ypos, zpos


def print_gcode_thread(filename):
    try:
        printerdriver.setup_motors()
    except Exception as e:
        print()
    print(f'Running {filename}')
    with open(filename, 'r') as f:
        content = f.read().splitlines()
        for i in range(len(content)):
            print(gcodeparser(content[i]))
            try:
                print(exec(gcodeparser(content[i])))
            except Exception as e:
                print(f'While trying to execute the command {gcodeparser(content[i])}, an error "{e}" happened')
    printerdriver.move_to((0, 0), 100)

def print_python_thread(filename):
    subprocess.run(["python", filename])

def print_gcode(filename):
    global print_thread
    if pathlib.Path(filename).suffix.lower() == '.py':
        print_thread = multiprocessing.Process(target=print_python_thread, args=(filename,))
    else:
        print_thread = multiprocessing.Process(target=print_gcode_thread, args=(filename,))
    print_thread.start()
    return

def stopprocesses():
    global print_thread
    print_thread.terminate()

def Move(x=0, y=0, z=0, f=0):
    printerdriver.move_to((x, y), 100)

def Wait(p=0, s=0):
    time.sleep(s+p/1000)

def Home(x=0, y=0, z=0):
    printerdriver.move_to((0, 0), 100)

def AbsolutePos():
    global absoluteposboolean
    absoluteposboolean = True

def RelativeLastPos():
    global xpos, ypos, zpos
    xpos, ypos, zpos = 0, 0, 0

def SetAbsolutePos(x=None, y=None, z=None, e=None):
    global xpos, ypos, zpos
    if x == None:
        pass
    else:
        xpos = x
    if y == None:
        pass
    else:
        ypos = y
    if z == None:
        pass
    else:
        zpos = z

def GetCurrentPosition():
    global xpos, ypos, zpos
    output = f'ok C: X:{float(xpos)} Y:{float(ypos)} Z:{float(zpos)}'
    print(output)
    return output

if __name__ == "__main__":
    print_gcode('gcode/testmove.gcode')
