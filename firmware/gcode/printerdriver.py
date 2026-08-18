import os, pathlib
exec(open(os.path.join(pathlib.Path(str(os.getcwd())).parent, 'firmware/printerdriver.py'), 'r').read())
