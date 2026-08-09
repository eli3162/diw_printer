from gcodetranslator import gcodeparser
import printerdriver, multiprocessing, pathlib, subprocess

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




def Move(x=0, y=0, z=0, f=0):
    printerdriver.move_to((x, y), 100)



if __name__ == "__main__":
    print_gcode('gcode/testmove.gcode')
