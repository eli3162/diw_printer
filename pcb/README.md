# Control Board PCB Design
I want to be able to code the 3d printer firmware in Micropython with a Raspberry Pi Pico W, and be able to control the stepper motors without using 3rd party software. There were no controller boards that could control more than 2 stepper motors at a time, and we needed 6 motor control. So, I decided that the best course of action would be to create my own control board as a Raspberry Pi HAT. I used KiCad, and used JLBPCB to manufacture the pcb. If you want to recreate the circuit board, you can open the circuit board file in KiCad, and export as a Gerber file.

Render:
![KiCad Render](https://eli3162.github.io/diw_printer/pcb/pcb_render.png)

[List of Materials and interactive model](https://eli3162.github.io/diw_printer/pcb/ibom.html)
