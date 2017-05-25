"""
Contingency by Rudy Li and Faith Lum
For ICS2O1 (Mr.Cope) summative 2017
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
        self.target = float(target)
        self.value = float(target if value is None else value)
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
        return self.value

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

class caption:
    """
    Some text and other data, collectively representing a caption
    """
    def __init__(self,texts,colors=None):
        global width,height
        self.texts = texts.split('\n') if type(texts)==str else list(map(str,texts)) # Force string type
        self.x = drift(0.1,width/2)
        self.y = drift(0.1,200,120)
        self.alpha = drift(0.1,1,0) # Alpha
        self.color = {'rgb':0} if colors is None else {colors[0]:colors[1]}
        self.live = 2
    def alive(self):
        """
        Is it live?
        Uses bitmask to signal
        """
        return self.live|(float(self.alpha)>=0)
    def kill(self):
        """
        Time to die
        """
        self.y.target = 240
        self.alpha.target = -0.1
        self.live = 0
    def draw(self):
        """
        Render the caption
        """
        global width,height
        setfont(None,-1,30)
        setcolor(**self.color)
        setpolyclip()
        x = self.x
        y = self.y
        x.step()
        y.step()
        x = float(x)
        y = float(y)
        ialpha = self.alpha
        ialpha.step()
        ialpha = float(ialpha)
        if ialpha<=0:return
        for text in self.texts:
            image = alpha(render(text),ialpha)
            drawimage(image,(x,y))
            y -= 40

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
        self.x = drift(0.1,width-40,width+iwidth)
        self.y = drift(0.1,height-index*50-70)
    def hit(self,xy):
        """
        Does the point xy lie on the button?
        Also, is it still transitioning?
        Uses bitmask indicator
        """
        iwidth = self.width
        ix = self.x
        iy = self.y
        ready = hypot(ix.diff(),iy.diff())<20
        ix = float(ix)
        iy = float(iy)
        return ((ix-iwidth-40<=xy[0] and iy-20<=xy[1]<=iy+20)<<1)|ready
    def draw(self,hover):
        """
        Render the button
        Pass flag hover to indicate if the mouse is hovering
        """
        global width,height,button_glow,particle_systems
        setcolor(rgb=0.02)
        img_glow = button_glow[4 if hover else 0]
        particles = particle_systems[self.index]
        image = render(self.text)
        self.width = iwidth = image.getWidth()
        ix = self.x
        iy = self.y
        ix.step()
        iy.step()
        ix = float(ix)
        iy = float(iy)
        left = ix-iwidth-40
        by = iy-20,iy+20
        setcolor(rgb=0.95)
        setpolyclip([[width,by[0]],[width,by[1]],[left+10,by[1]],[left,iy],[left+10,by[0]]])
        fill()
        particles.step()
        ox,oy = width,iy
        for particle in particles.particles:
            px,py = particle[0:2]
            drawimage(img_glow,(px+ox,py+oy))
        drawimage(image,(ix,iy),xalign=1)
    def act(self):
        """
        Perform the action it was supposed to do
        """
        self.action()

def draw_meter():
    """
    Handles rendering of love meter
    """
    global width,height,love_meter,love_meter_x,love_meter_particle_system,button_glow
    love_meter_x.step()
    love_meter.step()
    ix = float(love_meter_x)
    if ix<-160:return
    iy = float(love_meter)
    if iy<0:iy=0
    if iy>1:iy=1
    iy = 40+(height-80)*iy
    love_meter_particle_system.step()
    particles = love_meter_particle_system.particles
    # Lower half
    setcolor(rgb=0.95)
    img_glow = button_glow[0]
    setpolyclip([[ix-30,40],[ix,30],[ix+30,40],[ix+30,iy],[ix-30,iy]])
    fill()
    for particle in particles:
        px,py = particle[0:2]
        drawimage(img_glow,(px,py+height/2))
    # Upper half
    setcolor(rgb=0.95)
    img_glow = button_glow[3]
    setpolyclip([[ix-30,height-40],[ix,height-30],[ix+30,height-40],[ix+30,iy],[ix-30,iy]])
    fill()
    for particle in particles:
        px,py = particle[0:2]
        drawimage(img_glow,(px,py+height/2))
    # Text
    setcolor(rgb=0.02)
    setpolyclip()
    drawimage(render('Hate'),(ix+40,40),xalign=0)
    drawimage(render('Love'),(ix+40,height-40),xalign=0)

def draw_timer():
    """
    Handles drawing of timer
    Also does updating
    """
    global width,height,timer_time,timer_func,timer_y,timer_particle_system,timer_size,button_glow
    timer_y.step()
    ox,oy = width/2,float(timer_y)
    timer_str = '0.0'
    if timer_time:
        timer_y.target = height
        timer_remaining = timer_time-time()
        if timer_remaining>0:
            timer_size.target = 400/(timer_remaining+5)
            timer_str = str(timer_remaining)[:4]
        else:
            timer_time = None
            timer_func()
    else:
        timer_y.target = height+300
        timer_size.target = 40
    timer_size.step()
    itimer_size = float(timer_size)
    timer_radius = itimer_size*1.8
    if oy<height+timer_radius:
        setcolor(rgb=0.95)
        setpolyclip([[ox+timer_radius*cos(i*pi/32),oy+timer_radius*sin(i*pi/32)] for i in range(64)])
        fill()
        img_glow = button_glow[2]
        timer_particle_system.step()
        for particle in timer_particle_system.particles:
            px,py = particle[0:2]
            drawimage(img_glow,(px+ox,py+oy))
    setcolor(rgb=0.02)
    setfont(None,-1,int(itimer_size))
    setpolyclip()
    timer_img = render(timer_str)
    drawimage(timer_img,(ox,oy),yalign=1.2)

def draw_captions():
    """
    Handles drawing of captions
    """
    global width,height,captions,caption_y,caption_particle_system,button_glow
    for i in range(len(captions)-1,-1,-1):
        capt = captions[i]
        if not capt.alive()&1:
            captions.pop(i)
    anyd = False
    for capt in captions:
        anyd |= capt.alive()&2
    caption_y.target = 0 if anyd else -250
    caption_y.step()
    ox,oy = width/2,float(caption_y)
    if oy>-230:
        bx = 240,width-240
        by = 0,oy+230
        setcolor(rgb=0.95)
        setpolyclip([[bx[0]-40,by[0]],[bx[1]+40,by[0]],[bx[1],by[1]],[bx[0],by[1]]])
        fill()
        img_glow = button_glow[1]
        caption_particle_system.step()
        for particle in caption_particle_system.particles:
            px,py = particle[0:2]
            drawimage(img_glow,(px+ox,py+oy))
        for capt in captions:
            capt.draw()

def onclick(etype,exy,ebutton):
    """
    Handles mouse events
    """
    global buttons
    if etype=='click' and ebutton==1:
        rbutton = None
        ready = []
        for button in buttons:
            bhit = button.hit(exy)
            if bhit&1:
                ready.append(button)
            if bhit==3:
                rbutton = button
        if rbutton is not None:
            rbutton.act()
        elif len(ready)==1:
            ready[0].act()
bindmouse('mouse event',onclick)

def clear_buttons():
    """
    Gets rid of the current buttons
    """
    global buttons
    for button in buttons:
        button.x.target+=uniform(-40,40)
        button.y.target=height+uniform(40,80)

def clear_captions():
    """
    Gets rid of the current captions
    """
    global captions
    for capt in captions:
        capt.kill()

def fw_branch_to(*others):
    """
    Returns a function which pushes away all current buttons and adds the given buttons
    """
    def ifw_branch_to():
        global buttons
        clear_buttons()
        clear_captions()
        timer_set(None)
        for index,params in enumerate(others):
            text = params[0]
            func = params[1]
            if type(func)==str:func = globals()[func]
            buttons.append(choice_button(text,index,func))
    return ifw_branch_to

def fw_exec_all(*funcs):
    """
    Return a function which executes all functions in order
    """
    def ifw_exec_all():
        for func in funcs:
            if type(func)==str:func = globals()[func]
            func()
    return ifw_exec_all

def fw_meter_add(increment):
    """
    Return a function which adds increment to the love meter
    """
    def ifw_meter_add():
        global love_meter
        love_meter.target += increment
    return ifw_meter_add

def meter_status(enabled):
    """
    Set meter to either show or not be shown
    """
    global love_meter_x
    love_meter_x.target = 60 if enabled else -200

def fw_meter_status(enabled):
    """
    Return a function which sets the love meter status to enabled
    """
    def ifw_meter_status():
        meter_status(enabled)
    return ifw_meter_status

def fw_meter_condition(oper,value,if_true,if_false):
    """
    Return a function which branches based on the criteria
    """
    global comparators,love_meter
    comp = comparators[oper]
    if not if_true:if_true = lambda:None
    if not if_false:if_false = lambda:None
    def ifw_meter_condition():
        if comp(love_meter.target,value):
            if_true()
        else:
            if_false()
    return ifw_meter_condition

def timer_set(seconds,func=None):
    """
    Set the timer to last a certain number of seconds, then call func
    Call with None, 0, False, etc. to disable the timer
    """
    global timer_time,timer_func
    if seconds:
        if type(func)==str:func=globals()[func]
        timer_time = time()+seconds
        timer_func = func
    else:
        timer_time = None

def fw_timer_set(seconds,func=None):
    """
    Return a function to set the timer later
    """
    def ifw_timer_set():
        timer_set(seconds,func)
    return ifw_timer_set

def fw_caption_set(*args):
    """
    Return a function to clear all captions and set it to the given
    """
    def ifw_caption_set():
        global captions
        clear_captions()
        captions.append(caption(*args))
    return ifw_caption_set

# Comparators
epsilon = 1e-9
comparators = {
    '>':(lambda x,y:x-y>epsilon),
    '>=':(lambda x,y:x-y>-epsilon),
    '<':(lambda x,y:y-x>epsilon),
    '<=':(lambda x,y:y-x>-epsilon),
    '==':(lambda x,y:abs(x-y)<epsilon),
    '!=':(lambda x,y:abs(x-y)>epsilon)
    }

# Initialize globals
base_particles = 100
setfont(None,-1,24)
love_meter = drift(0.03,0.5) # 0 = hate, 1 = love
love_meter_x = drift(0.03,-200)
love_meter_particle_system = particle_system([[-200,-80],[-height/2,height/2]],[[0,2],[-1,1]],[[-0.01,0.01],[-0.01,0.01]],height/2+100,5*base_particles,1)
timer_time = None
timer_func = None
timer_size = drift(0.1,80)
timer_y = drift(0.1,height+300)
timer_particle_system = particle_system([[-80,80],[80,200]],[[-1,1],[-2,0]],[[-0.01,0.01],[-0.01,0.01]],300,2*base_particles,1)
captions = []
caption_y = drift(0.1,-250)
caption_particle_system = particle_system([[-width/2,width/2],[-200,-80]],[[-1,1],[0,2]],[[-0.01,0.01],[-0.01,0.01]],width,10*base_particles,2)
buttons = []
button_glow = [loadimage('glow'+str(i)+'.png') for i in range(1,6)]
particle_systems = [particle_system([[80,200],[-80,80]],[[-4,-1],[-2,2]],[[-0.02,0.02],[-0.02,0.02]],width,5*base_particles,1) for _ in range(8)]
for particles in particle_systems+[love_meter_particle_system,timer_particle_system,caption_particle_system]:
    for _ in range(200):
        particles.step()

# Test menu items
p_menu_1 = fw_exec_all(fw_branch_to(['...','p_menu_1a']),fw_caption_set('So basically'),)
p_menu_1a = fw_exec_all(fw_branch_to(['...','p_menu_1b']),fw_caption_set('This is how dialogue will work'))
p_menu_1b = fw_exec_all(fw_branch_to(['...','p_menu_1c']),fw_caption_set('We\'ll give each character\ntheir own colour\nor something like that',('hsv',(0.6,0.8,0.8))))
p_menu_1c = fw_branch_to(['1 -> 2','p_menu_2'],['1 -> 3','p_menu_3'],['1 -> 1','p_menu_1'])
p_menu_2 = fw_meter_condition('>',0.2,fw_exec_all(fw_branch_to(['2 -> 3','p_menu_3'],['2 -> 1','p_menu_1'],['2 -> 2','p_menu_2']),fw_meter_add(-0.15)),fw_branch_to(['uh oh','p_menu_2b']))
p_menu_2b = fw_exec_all(fw_branch_to(['to 2','p_menu_2'],['to 4','p_menu_4']),fw_caption_set('Love metred'),fw_meter_add(0.5))
p_menu_3 = fw_branch_to(['3 -> 1','p_menu_1'],['3 -> 2','p_menu_2'],['3 -> 3','p_menu_3'],['3 -> 4','p_menu_4'])
p_menu_4 = fw_exec_all(fw_branch_to(['4 -> 1','p_menu_1'],['4 -> 2','p_menu_2']),fw_timer_set(10,'p_menu_5'))
p_menu_5 = fw_branch_to(['5 -> 1','p_menu_1'],['5 -> 2','p_menu_2'],['5 -> 4','p_menu_4'])
p_menu_6 = fw_branch_to(['1 >>',p_menu_1],['2 >>',p_menu_2],['3 >>',p_menu_3],['4 >>',p_menu_4])
fw_branch_to(['Play',fw_exec_all(fw_meter_status(True),p_menu_6)])()

# Drivers and rendering
for _ in mainloop():
    mouse_x,mouse_y = mouse_xy = mousepos()
    setcolor(rgb=1.0)
    fill()
    setfont(None,-1,24)
    for i in range(len(buttons)-1,-1,-1):
        button = buttons[i]
        button.draw(button.hit(mouse_xy)&2)
        if float(button.y)>height+20:
            buttons.pop(i)
    draw_meter()
    draw_timer()
    draw_captions()
