import printerdriver,turtle, math, time
x, y = 0, 0
speed = 100
def move_to(point, speed):
    global x, y
    deltax = point[0]-x
    deltay = point[1]-y
    
    printerdriver.moveto((deltax, deltay), speed)
    x, y = x+(deltax), y+(deltay)
    return
while True:
    print(printerdriver.timenow())
'''
move_to((50, 100), speed)
move_to((100, 0), speed)
move_to((0, 0), speed)
'''

'''
for i in range(1):
    printerdriver.moveto((-256, 0), speed)
    printerdriver.moveto((0, -256), speed)
    printerdriver.moveto((256, 0), speed)
    printerdriver.moveto((0, 256), speed)
'''