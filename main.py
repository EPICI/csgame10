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

# Buttons
class textbutton:
    def __init__(self,text,y,func):
        self.func = func
        img = self.img = render(text)
        y *= 40
        iwidth = img.getWidth()
        self.x = 760-iwidth/2
        self.y = y+20
        self.bounds = [[740-iwidth,780],[y,y+40]]
    def hit(self,x,y):
        bx,by = self.bounds
        return bx[0]<=x<=bx[1] and by[0]<=y<=by[1]
    def draw(self):
        drawimage(self.img,(self.x,self.y))
    def act(self):
        self.func()

def onclick(etype,exy,ebutton):
    global buttons
    if etype=='click' and ebutton==1:
        rbutton = None
        for button in buttons:
            if button.hit(*exy):
                rbutton = button
                break
        if rbutton is not None:
            rbutton.act()
bindmouse('mouse event',onclick)

def incall(n):
    global i,buttons
    def act():
        global i,buttons
        print('incremented by '+str(n))
        i += n
        buttons = []
        for j in range(1,11):
            buttons.append(textbutton(str(i+j)+' (+'+str(j)+')',j,incall(j)))
    return act

buttons = []
i = 0

for _ in mainloop():
    if i==0:incall(1)()
    setcolor(rgb=(1,1,1))
    fill()
    setcolor(rgb=(0,0,0))
    for button in buttons:
        button.draw()
