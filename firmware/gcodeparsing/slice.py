from pylatexenc.latex2text import LatexNodes2Text
from gcodegen import generate_py, generate_gcode

def slice_latex(latex: str):
    plain_text = str(LatexNodes2Text().latex_to_text(latex))
    plain_text = eval(plain_text)
    print(plain_text)
    py = generate_py(speed=20, gcode=plain_text, nozzle_diameter=0.75, layers=3)
    return py

if __name__ == '__main__':
    with open("latex.lt", "r") as file:
        content = file.read()
        print(content)
    print(slice_latex(content))