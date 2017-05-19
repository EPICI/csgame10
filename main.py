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
width = 1280
height = 720
resize(width,height)

class drift:
    """
    Gradually moves towards the target/true value
    Used for animation easing
    """
    def __init__(self,rate,target=0.0,value=None):
        self.rate = rate
        self.target = target
        self.value = target if value is None else value
    def step(self):
        """
        Go forward one step
        """
        self.value += self.rate*(self.target-self.value)
    def diff(self):
        """
        How far is the current value from the target?
        """
        return self.value-self.target
    def __float__(self):
        """
        Ensure float() gets the current value
        """
        return float(self.value)

class image_sequence:
    """
    A sequence of images
    Makes animation easier
    """
    def __init__(self,names,loop):
        self.loop = loop
        self.images = map(loadimage,names)
        self.frame = 0
    def step(self):
        """
        Try to go forward one frame
        """
        frames = len(self.images)
        self.frame += 1
        if self.frame>=frames: # Loop behaviour
            self.frame = 0 if self.loop else frames-1
    def draw(*args,**kwargs):
        """
        Draws the current frame
        """
        drawimage(self.images[self.frame],*args,**kwargs)

class particle_system:
    """
    A simple acceleration-based particle system
    """
    def __init__(self,source_xy,source_dxy,source_ddxy,bound,limit,spawn_rate):
        self.params = source_xy+source_dxy+source_ddxy
        self.limit = limit
        self.rate = spawn_rate
        self.bound = bound
        self.particles = []
    def step(self):
        """
        Go forward one time step
        """
        params = self.params
        limit = self.limit
        rate = self.rate
        bound = self.bound
        particles = self.particles
        for i in range(len(particles)-1,-1,-1):
            particle = particles[i]
            if hypot(particle[0],particle[1])>bound:
                particles.pop(i)
        while len(particles)<limit and rate>0:
            rate -= 1
            particles.append([uniform(param[0],param[1]) for param in params])
        for particle in particles:
            for i in range(4):
                particle[i] += particle[i+2]

class choice_button:
    """
    A button representing a choice
    """
    def __init__(self,text,index,action):
        global width,height
        text = str(text) # Force string type
        self.action = action
        self.index = index
        self.text = text
        image = render(text) # Dummy, use to get width
        self.width = iwidth = image.getWidth()
        self.x = drift(0.1,width-iwidth/2-40,width+iwidth/2+40)
        self.y = drift(0.1,height-index*50-30,height-index*50-30)
    def hit(self,xy):
        """
        Does the point xy lie on the button?
        If still transitioning, will return False unconditionally
        """
        iwidth = self.width
        ix = self.x
        iy = self.y
        if hypot(ix.diff(),iy.diff())>10:return False
        ix = float(ix)
        iy = float(iy)
        return ix-iwidth/2-20<=xy[0] and iy-20<=xy[1]<=iy+20
    def draw(self,hover):
        """
        Render the button
        Pass flag hover to indicate if the mouse is hovering
        """
        global width,height,button_glow,particle_systems
        img_glow = button_glow[hover]
        particles = particle_systems[self.index]
        iwidth = self.width
        ix = self.x
        iy = self.y
        ix.step()
        iy.step()
        ix = float(ix)
        iy = float(iy)
        left = ix-iwidth/2-20
        by = iy-20,iy+20
        setpolyclip([[width,by[0]],[width,by[1]],[left+10,by[1]],[left,iy],[left+10,by[0]]])
        setcolor(rgb=0.95)
        fill()
        particles.step()
        ox,oy = width,iy
        for particle in particles.particles:
            px,py = particle[0:2]
            drawimage(img_glow,(px+ox,py+oy))
        setcolor(rgb=0.02)
        drawimage(render(self.text),(ix,iy))
    def act(self):
        """
        Perform the action it was supposed to do
        """
        self.action()

def onclick(etype,exy,ebutton):
    global buttons
    if etype=='click' and ebutton==1:
        rbutton = None
        for button in buttons:
            if button.hit(exy):
                rbutton = button
        if rbutton is not None:
            rbutton.act()
bindmouse('mouse event',onclick)

def fw_clear_buttons(func):
    """
    Returns a function that pushes away all current buttons and executes the given function
    """
    def ifw_clear_buttons():
        global buttons
        for button in buttons:
            button.x.target+=uniform(-40,40)
            button.y.target=height+uniform(40,80)
        func()
    return ifw_clear_buttons

def fw_branch_to(*others):
    """
    Returns a function which pushes away all current buttons and adds the given buttons
    """
    def ifw_branch_to():
        global buttons
        fw_clear_buttons(lambda:None)()
        for index,params in enumerate(others):
            text = params[0]
            func = params[1]
            if type(func)==str:func = globals()[func]
            buttons.append(choice_button(text,index,func))
    return ifw_branch_to

# Initialize globals
setfont(None,-1,24)
buttons = []
button_glow = [loadimage('glow1.png'),loadimage('glow2.png')]
particle_systems = [particle_system([[80,200],[-80,80]],[[-4,-1],[-2,2]],[[-0.02,0.02],[-0.02,0.02]],width,400,1) for _ in range(8)]
for particles in particle_systems:
    for _ in range(100):
        particles.step()

# Test menu items
p_menu_1 = fw_branch_to(['1 -> 2','p_menu_2'],['1 -> 3','p_menu_3'],['1 -> 1','p_menu_1'])
p_menu_2 = fw_branch_to(['2 -> 3','p_menu_3'],['2 -> 1','p_menu_1'],['2 -> 2','p_menu_2'])
p_menu_3 = fw_branch_to(['3 -> 1','p_menu_1'],['3 -> 2','p_menu_2'],['3 -> 3','p_menu_3'],['3 -> 4','p_menu_4'])
p_menu_4 = fw_branch_to(['4 -> 1','p_menu_1'],['4 -> 2','p_menu_2'])
fw_branch_to(['1 >>',p_menu_1],['2 >>',p_menu_2],['3 >>',p_menu_3],['4 >>',p_menu_4])()

# Drivers and rendering
for _ in mainloop():
    mouse_x,mouse_y = mouse_xy = mousepos()
    setcolor(rgb=1.0)
    fill()
    for i in range(len(buttons)-1,-1,-1):
        button = buttons[i]
        button.draw(button.hit(mouse_xy))
        if float(button.y)>height+20:
            buttons.pop(i)
