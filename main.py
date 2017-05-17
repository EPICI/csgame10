"""
Async by Rudy Li and Faith Lum
For ICS2O1 (Mr.Cope) summative

plz fix this senpai
"""

# The header sets this dummy variable, so we treat its existence as a flag
if '_jython' not in globals():
    import os
    os.system('engine.jar')
    exit()

# Imports
from math import *
from random import *
from time import *
from core.engine import *

# Set reasonable FPS
fps = 24
framerate(fps)
# Set base resolution
resize(800,450)

# Test code
istr = 'typed: '
cx = 400
cy = 225
def onkey(etype,ekey):
    global istr
    print('key',etype)
    if etype=='type' and 32<ekey<126:
        istr+=chr(ekey)
bindkey('key event name',onkey)
def onmouse(etype,exy,ebutton):
    global cx
    global cy
    print('mouse',etype,ebutton)
    if etype=='press' and ebutton==1:
        cx,cy = exy
bindmouse('mouse event name',onmouse)
i = fps*30
icon = loadimage('icon.png')
for _ in mainloop():
    i -= 1
    if not i:break
    img = render(istr) if len(istr)<10 else icon
    r = i*0.02
    setcolor(rgb=(1,1,1))
    fill()
    setpolyclip([[cx+200*cos(j*pi/30),cy+200*sin(j*pi/30)] for j in range(60)])
    setcolor(rgb=(0,0,0))
    for _ in range(6):
        r += 0.9
        for radius in range(0,300,60):
            drawimage(img,(cx+radius*cos(r),cy+radius*sin(r)))
        img = alpha(img,0.8)


