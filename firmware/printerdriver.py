import machine, time # type: ignore

limit_switches = [machine.Pin(button_iter, machine.Pin.IN, machine.Pin.PULL_UP) for button_iter in (21, 22, 26, 27)]

def x_switch():
    global limit_switches
    if limit_switches[0].value():
        return False
    else: 
        return True

def y_switch():
    global limit_switches
    if limit_switches[1].value():
        return False
    else: 
        return True

def z_switch():
    global limit_switches
    if limit_switches[2].value():
        return False
    else: 
        return True

def e_switch():
    global limit_switches
    if limit_switches[3].value():
        return False
    else: 
        return True
