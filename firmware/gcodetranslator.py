replacmentdic = {
    "X": "x=",
    "Y": "y=",
    "Z": "z=",
    "E": "e=",
    "F": "f=",
    "I": "i=",
    "J": "j=",
    "K": "k=",
    "R": "r=",
    "P": "p=",
    "S": "s=",
    "G0 ": "Move(",
    "G1 ": "Move(",
    "G2 ": "ClockwiseArc(",
    "G3 ": "CounterClockwiseArc(",
    "G4 ": "Wait(",
    "G00 ": "Move(",
    "G01 ": "Move(",
    "G02 ": "ClockwiseArc(",
    "G03 ": "CounterClockwiseArc(",
    "G04 ": "Wait(",
    "G28 ": "Home(",
    "G90 ": "AbsolutePos(",
    "G91 ": "RelativeLastPos(",
    "G92 ": "SetAbsolutePos(",
    "M1 ": "Sleep(",
    "M01 ": "Sleep(",
    "M17 ": "EnableStepperMotors(",
    "M18 ": "DisableStepperMotors(",
    "M114 ": "GetCurrentPosition(",
    " ": ",",
    ".,": ".0,",
    ".)": ".0)",
    ". ": ".0 "
}
sentax = {
    " ": ",",
    ".,": ".0,",
    ".)": ".0)",
    ". ": ".0 "
}
def gcodeparser(gcodeline):
    global replacmentdic
    gcodeline=gcodeline.split(';', 1)[0]
    for i in range(len(replacmentdic.keys())):
        dictionarykeys = list(replacmentdic.keys())
        gcodeline = gcodeline.replace(dictionarykeys[i], replacmentdic.get(dictionarykeys[i]))
    if '(' in gcodeline:
        gcodeline = gcodeline + ")"
    else:
        pass
    for j in range(len(sentax.keys())):
        dictionarykeys = list(sentax.keys())
        gcodeline = gcodeline.replace(dictionarykeys[j], sentax.get(dictionarykeys[j]))
    gcodeline=gcodeline.split('G', 1)[0]
    return gcodeline
