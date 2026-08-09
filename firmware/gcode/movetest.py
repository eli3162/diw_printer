import printerdriver
printerdriver.setup_motors()
printerdriver.move_to((100, 100), 100)
printerdriver.move_to((0, 0), 100)