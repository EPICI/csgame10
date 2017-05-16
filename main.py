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
fps = 30
framerate(fps)
# Set base resolution
resize(1280,720)

# Test code
istr = 'typed: '
cx = 640
cy = 360
def onkey(etype,ekey):
    print('key',etype)
    if etype=='type' and 32<ekey<126:
        istr+=ord(ekey)
bindkey('key event name',onkey)
def onmouse(etype,exy):
    global cx
    global cy
    print('mouse',etype)
    if etype=='press':
        cx,cy = exy
bindmouse('mouse event name',onmouse)
i = fps*30
for _ in mainloop():
    i -= 1
    if not i:break
    img = render(istr)
    r = i*0.02
    setcolor(rgb=(1,1,1))
    fill()
    setcolor(rgb=(0,0,0))
    for radius in range(0,1400,60):
        drawimage(img,(cx+radius*cos(r),cy+radius*sin(r)))


