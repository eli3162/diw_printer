import gpiozero as GPIO # type: ignore[reportMissingImports]
import asyncio, math, time, multiprocessing # type: ignore[reportMissingImports]

xpos, ypos = 110, 110

def timenow():
    return time.perf_counter()

ControlMode = [
    'hardward',
    'softward',
]

class DRV8825():
    def __init__(self, dir_pin, step_pin, enable_pin, mode_pins):
        
        self.mode_pins = mode_pins
        self.dir_pin = dir_pin
        self.enable_pin = enable_pin
        self.step_pin = step_pin
        
        self.dir = GPIO.LED(self.dir_pin)
        self.step = GPIO.LED(self.step_pin)        
        self.enable = GPIO.LED(self.enable_pin)
        self.mode_1 = GPIO.LED(self.mode_pins[0])
        self.mode_2 = GPIO.LED(self.mode_pins[1])
        self.mode_3 = GPIO.LED(self.mode_pins[2])

        self.control_pin = {
          dir_pin: self.dir,
          enable_pin: self.enable,
          step_pin: self.step,
          mode_pins[0]: self.mode_1,
          mode_pins[1]: self.mode_2,
          mode_pins[2]: self.mode_3
        }
        
    def digital_write(self, pin, value):
        if value:
            self.control_pin[pin].on()
        else:
            self.control_pin[pin].off()
                  
    def stop(self):
            self.digital_write(self.enable_pin, 0)
        
    def configure_mode(self, microstep):
        j = 0
        for i in microstep:
          self.digital_write(self.mode_pins[j], i)
          j = j+1
    
    def setmicrostep(self, mode, stepformat):
        microstep = {'fullstep': (0, 0, 0),
                     'halfstep': (1, 0, 0),
                     '1/4step': (0, 1, 0),
                     '1/8step': (1, 1, 0),
                     '1/16step': (0, 0, 1),
                     '1/32step': (1, 0, 1)}

        if (mode == ControlMode[1]):
            self.configure_mode(microstep[stepformat])
    
    def turnstep(self, steps, stepdelay, activatationtime):
        if activatationtime - timenow() < 0:
            pass
        else:
            while activatationtime - timenow() > 0:
                pass
        j=0
        deltatime = timenow()
        for i in range(steps):
            j=j+1
            self.digital_write(self.step_pin, True)
            while deltatime + stepdelay*j > timenow():
                pass
            j=j+1
            self.digital_write(self.step_pin, False)
            while deltatime + stepdelay*j > timenow():
                pass
        self.stop()
        return
    
    async def asyncmove(self, mm, speed, acttime=0):
        if acttime==0:
            acttime = timenow()+0.01
        steps = math.floor(abs(mm*(1.8*360*10)/(16*3.14)))
        if speed == 0:
            stepdelay=0
        else:
            stepdelay = abs(1/((speed)*(1.8*360*10)/(16*3.14)))
        
        if mm>0:
            self.digital_write(self.enable_pin, 1)
            self.digital_write(self.dir_pin, 0)
        elif mm<0:
            self.digital_write(self.enable_pin, 1)
            self.digital_write(self.dir_pin, 1)
        else:
            self.digital_write(self.enable_pin, 0)
            return
        if steps == 0:
            return
        p = multiprocessing.Process(target=self.turnstep, args=(steps, stepdelay, acttime))
        p.start()
        return
        
    def move(self, mm, speed):
        return asyncio.run(self.asyncmove(mm, speed))
        
async def asyncmoveto(point, speed, delay=0.01):
    x = point[0]
    y = point[1]
    acttime = timenow()+delay
    distance = math.sqrt(x**2+y**2)
    deltatime = distance/speed
    try:
        xspeed = abs(x/deltatime)
        yspeed = abs(y/deltatime)
    except Exception as e:
        xspeed, yspeed = 0, 0
    asyncio.gather(
        ymotor.asyncmove(y, yspeed, acttime=acttime),
        xmotor.asyncmove(x, xspeed, acttime=acttime)
    )
    xmotor.stop()
    ymotor.stop()
    await asyncio.sleep(deltatime)
    return

def moveto(point, speed, offset=-0.022):
    x = point[0]
    y = point[1]
    distance = math.sqrt(x**2+y**2)
    timerun = distance/speed
    asyncio.run(asyncmoveto(point, speed))
    time.sleep(abs(timerun+offset*distance))
    return 

def move_to(point, speed):
    global xpos, ypos
    deltax = point[0]-xpos
    deltay = point[1]-ypos
    moveto((deltax, deltay), speed)
    xpos, ypos = xpos+(deltax), ypos+(deltay)
    return

def calibration():
    move_to((0, 0), 100)


xmotor = DRV8825(dir_pin=13, step_pin=19, enable_pin=12, mode_pins=(16, 17, 20))
ymotor = DRV8825(dir_pin=24, step_pin=18, enable_pin=4, mode_pins=(21, 22, 27))
xmotor.setmicrostep('softward', 'fullstep')
ymotor.setmicrostep('softward', 'fullstep')
calibration()