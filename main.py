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
        setcolor(rgb=0.1)
        img = self.img = render(text)
        iwidth = img.getWidth()
        self.x = 760-iwidth/2
        y = self.y = 420-y*40
        bx,by = self.bounds = [[740-iwidth,800],[y-15,y+15]]
        self.particles = [[
            uniform(*bx),
            uniform(*by),
            uniform(-4,4),
            uniform(-4,4),
            uniform(-0.1,0.1),
            uniform(-0.1,0.1),
            img_glow_random()] for _ in range(20)]
    def hit(self,x,y):
        bx,by = self.bounds
        return bx[0]<=x<=bx[1] and by[0]<=y<=by[1]
    def draw(self):
        global img_glow
        bx,by = self.bounds
        particles = self.particles
        for i in range(len(particles)-1,-1,-1):
            pc = particles[i]
            pcx = pc[0]
            if pcx>900 or pcx<-100:
                particles.pop(i)
        r = 3 # Spawning rate
        while len(particles)<200 and r>0:
            r -= 1
            particles.append([
                bx[0]-uniform(80,120),
                uniform(by[0]-80,by[1]+80),
                uniform(2,6),
                uniform(-4,4),
                uniform(-0.05,0.05),
                uniform(-0.05,0.05),
                img_glow_random()])
        setpolyclip([[bx[1],by[1]],[bx[1],by[0]],[bx[0]+10,by[0]],[bx[0],(by[0]+by[1])/2],[bx[0]+10,by[1]]])
        setcolor(rgb=0.97)
        fill()
        for pc in particles:
            for i in range(4):
                pc[i]+=pc[i+2]
            drawimage(pc[6],pc[0:2])
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
            buttons.append(textbutton(str(i+j)+' (+'+str(j**3)+')',j-1,incall(j**3)))
    return act

buttons = []
i = 0
img_glow = [loadimage('glow1.png'),loadimage('glow2.png')]
def img_glow_random():
    global img_glow
    return img_glow[random()>0.8]

for _ in mainloop():
    if i==0:incall(1)()
    setcolor(rgb=1.0)
    fill()
    for button in buttons:
        button.draw()
