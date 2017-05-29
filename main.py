"""
Contingency by Rudy Li and Faith Lum
For ICS2O1 (Mr.Cope) summative 2017
"""

# The header sets this dummy variable, so we treat its existence as a flag
if '_jython' not in globals():
    import os
    os.system('engine.jar')
    exit()

# ======================================================================================================================================================
#
# Initialization that needs to happen before the other initialization
#
# ======================================================================================================================================================

# Imports
from math import *
from random import *
from time import *
from core.engine import *

# Set reasonable FPS limit
# Note on FPS: game can go slower, but can never go faster, so it is okay to set this high
fps = 30
framerate(fps)
# Set base resolution
width = 1280
height = 720
resize(width,height)

# Override image loading and bundle with unload
oloadimage = loadimage
images = {}
def loadimage(name):
    """
    Load an image from file
    Memoizes
    """
    if name not in images:images[name]=oloadimage(name)
    return images[name]
def unloadimage(name):
    """
    Dereferences an image
    """
    images.pop(name,None)

# ======================================================================================================================================================
#
# Classes
#
# ======================================================================================================================================================

class weighted_choice:
    """
    A weighted choice
    """
    def __init__(self,objs):
        if not objs:raise AssertionError('Need at least one choice')
        if type(objs)==dict:objs = objs.items()
        mul = 1/sum(map(lambda x:x[1],objs))
        self.opt = opt = []
        pfx = 0
        for v,w in objs:
            pfx += w*mul
            opt.append([v,pfx])
    def choose(self):
        opt = self.opt
        x = random()
        for v,w in opt:
            if w>x:return v
        return opt[-1] # Blame rounding errors

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
        self.names = names = tuple(names)
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
    def atend(self):
        """
        Is it at the end of the sequence?
        """
        return self.frame>=self.frames
    def reset(self):
        """
        Go back to the beginning
        """
        self.frame = 0
    def draw(ialpha,*args,**kwargs):
        """
        Draws the current frame
        """
        if not ialpha or ialpha>0.998:
            drawimage(self.images[self.frame],*args,**kwargs)
        elif ialpha>0.002:
            drawimage(alpha(self.images[self.frame],ialpha),*args,**kwargs)

class image_sequence_loader:
    """
    Loads image sequence from iterable
    Does not load images until they are needed by default
    Can unload
    """
    def __init__(self,*args):
        self.seq = None
        self.args = args
    def fetch(self):
        """
        Get the image sequence, will load if not loaded
        """
        if self.seq is None:
            self.load()
        return self.seq
    def loaded(self):
        """
        Is it loaded?
        """
        return self.seq is not None
    def load(self):
        """
        Force the image sequence to load
        """
        self.seq = image_sequence(*self.args)
    def unload(self,full=True):
        """
        Unload the image sequence to free memory
        """
        if full:
            for name in self.seq.names:
                unloadimage(name)
        self.seq = None

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
        global width,height,linelength
        # Split lines
        if len(texts)<linelength:
            texts = (texts,)
        elif len(texts)<2*linelength:
            parts = texts.split(' ')[::-1]
            tl = len(texts)//2
            al = -1
            a = []
            while al<tl:
                nx = parts.pop()
                al += len(nx)+1
                a.append(nx)
            texts = (' '.join(a),' '.join(parts[::-1]))
        else:
            parts = texts.split(' ')[::-1]
            tl = len(texts)//3
            al = -1
            a = []
            while al<tl:
                nx = parts.pop()
                al += len(nx)+1
                a.append(nx)
            tl = (sum(map(len,parts))+len(parts)-1)//2
            bl = -1
            b = []
            while bl<tl:
                nx = parts.pop()
                bl += len(nx)+1
                b.append(nx)
            texts = (' '.join(a),' '.join(b),' '.join(parts[::-1]))
        self.texts = texts
        self.x = drift(0.1,width/2)
        self.y = drift(0.1,150,100)
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
        self.y.target = 200
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
        global width,height,button_glow,button_particle_systems
        setcolor(rgb=0.02)
        img_glow = button_glow[4 if hover else 0]
        particles = button_particle_systems[self.index]
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
        self.action = action = funcify(self.action)
        action()

class character:
    """
    Animation set for a character
    """
    def __init__(self,animset,start=None):
        global width,height
        self.x = drift(0.1,width/2)
        self.y = drift(0.1,height/2)
        self.alpha = drift(0.1,0)
        if type(animset)==dict:animset = animset.items()
        self.anims = anims = {}
        for name,group in animset:
            filenames,redir = group
            anims[name] = [image_sequence_loader(filenames,False),weighted_choice(redir)]
        self.current = start if start else animset[0][0]
    def draw(self):
        """
        Render the current animation frame
        """
        ix = self.x
        iy = self.y
        ialpha = self.alpha
        ix.step()
        iy.step()
        ialpha.step()
        ix = float(ix)
        iy = float(iy)
        ialpha = float(ialpha)
        if ialpha<=0:return
        iseql,redir = self.anims[self.current]
        iseq = iseql.fetch()
        iseq.draw(ialpha,(ix,iy))
        iseq.step()
        if iseq.atend():
            self.jumpto(redir.choose())
    def jumpto(self,name):
        """
        Jump to a particular animation
        """
        self.current = name
        iseql = self.anims[name][0]
        if iseql.loaded():iseql.fetch().reset()

# ======================================================================================================================================================
#
# Rendering abstractions
#
# ======================================================================================================================================================

def draw_background():
    """
    Handles rendering of background
    """
    global background_image,background_x,background_y
    setpolyclip()
    if background_image is not None:
        if type(background_image)==str:background_image=loadimage(background_image)
        background_x.step()
        background_y.step()
        drawimage(background_image,(float(background_x),float(background_y)))
    else:
        setcolor(1.0)
        fill()

def draw_characters():
    """
    Handles drawing of characters
    """
    global characters
    setpolyclip()
    for ichar in characters.values():
        ichar.draw()

def draw_buttons():
    """
    Handles rendering of buttons
    """
    global buttons,mouse_xy
    setfont(None,-1,24)
    for i in range(len(buttons)-1,-1,-1):
        button = buttons[i]
        button.draw(button.hit(mouse_xy)&2)
        if float(button.y)>height+20:
            buttons.pop(i)

def draw_meter():
    """
    Handles rendering of love meter
    """
    global width,height,love_meter,love_meter_x,love_meter_particle_system,button_glow
    love_meter_x.step()
    love_meter.step()
    ix = float(love_meter_x)
    if ix<-160:return
    iy = 1-float(love_meter)
    if iy<0:iy=0
    if iy>1:iy=1
    ir = iy
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
    setfont(None,-1,int(30*(0.5+ir)))
    drawimage(render('Hate'),(ix+40,40),xalign=0)
    setfont(None,-1,int(30*(1.5-ir)))
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
            funcify(timer_func)()
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
    caption_y.target = 0 if anyd else -200
    caption_y.step()
    ox,oy = width/2,float(caption_y)
    if oy>-180:
        bx = 250,width-250
        by = 0,oy+180
        setcolor(rgb=0.7)
        setpolyclip([[bx[0]-40,by[0]],[bx[1]+40,by[0]],[bx[1],by[1]],[bx[0],by[1]]])
        fill()
        for capt in captions:
            capt.draw()

# ======================================================================================================================================================
#
# Event handling
#
# ======================================================================================================================================================

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

# ======================================================================================================================================================
#
# Functional utilities
#
# ======================================================================================================================================================

def funcify(func):
    """
    Returns the function version of the given
    """
    if func is None:return lambda:None
    tfunc = type(func)
    if tfunc==str:return funcify(globals()[func])
    if tfunc==list or tfunc==tuple:return fw_exec_all(*func)
    return func

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
            buttons.append(choice_button(text,index,func))
    return ifw_branch_to
redir = lambda x:fw_branch_to(('...',x))

def fw_exec_all(*funcs):
    """
    Return a function which executes all functions in order
    """
    def ifw_exec_all():
        for func in map(funcify,funcs):
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

def fw_background_set(**kwargs):
    """
    Return a function to change the background
    """
    img = None
    cxy = None
    txy = None
    for k,v in kwargs.items():
        if k in 'imageimg':
            if img is not None:raise ValueError('Duplicate keyword '+k)
            img = v
        elif k in 'targetxytargetposition':
            if txy is not None:raise ValueError('Duplicate keyword '+k)
            txy = v
        elif k in 'staticxystaticposition':
            if cxy is not None:raise ValueError('Duplicate keyword '+k)
            cxy = v
        else:
            raise ValueError('Unrecognized keyword '+k)
    def ifw_background_set():
        global background_image,background_x,background_y
        if img is not None:
            background_image = img
        if cxy is not None:
            x,y = cxy
            background_x.target = background_x.value = float(x)
            background_y.target = background_y.value = float(y)
        if txy is not None:
            x,y = txy
            background_x.target = float(x)
            background_y.target = float(y)
    return ifw_background_set

def fw_character_set(cname,**kwargs):
    """
    Return a function to set the target character to a certain animation
    """
    aname = None
    cxy = None
    txy = None
    ca = None
    ta = None
    for k,v in kwargs:
        if k in 'jumptoanimationnameaname':
            if aname is not None:raise ValueError('Duplicate keyword '+k)
            aname = v
        elif k in 'targetxytargetposition':
            if txy is not None:raise ValueError('Duplicate keyword '+k)
            txy = v
        elif k in 'staticxystaticposition':
            if cxy is not None:raise ValueError('Duplicate keyword '+k)
            cxy = v
        elif k in 'targetalpha':
            if ta is not None:raise ValueError('Duplicate keyword '+k)
            ta = v
        elif k in 'staticalpha':
            if ca is not None:raise ValueError('Duplicate keyword '+k)
            ca = v
        else:
            raise ValueError('Unrecognized keyword '+k)
    def ifw_character_jump():
        global characters
        ichar = characters[cname]
        if aname is not None:
            ichar.jumpto(aname)
        if cxy is not None:
            x,y = cxy
            ichar.x.target = ichar.x.value = float(x)
            ichar.y.target = ichar.y.value = float(y)
        if txy is not None:
            x,y = txy
            ichar.x.target = float(x)
            ichar.y.target = float(y)
        if ca is not None:
            ichar.alpha.target = ichar.alpha.value = float(ca)
        if ta is not None:
            ichar.alpha.target = float(ta)
    return ifw_character_jump

def drgb(istr):
    """
    Get RGB colour from hex string
    """
    r = int(istr[-6:],16)
    b = r&0xff
    r>>=8
    g = r&0xff
    r>>=8
    return r/255,g/255,b/255

# ======================================================================================================================================================
#
# Initialize globals
#
# ======================================================================================================================================================

# Constants and configurations
linelength = 50 # Number of characters to allow in one line for captions (soft limit)
# Comparators
epsilon = 1e-9
comparators = {
    '>':lambda x,y:x-y>epsilon,
    '>=':lambda x,y:x-y>-epsilon,
    '<':lambda x,y:y-x>epsilon,
    '<=':lambda x,y:y-x>-epsilon,
    '==':lambda x,y:abs(x-y)<epsilon,
    '!=':lambda x,y:abs(x-y)>epsilon
    }
# Particle systems, images, etc.
base_particles = 100
palette = lambda:None # Colour palette, dummy object
palette.narration = ('rgb',0.4)
palette.player = ('rgb',drgb('E50085'))
palette.lily = ('rgb',drgb('00BBCC'))
palette.yu = ('rgb',drgb('F2C500'))
palette.rustam = ('rgb',drgb('E54F2D'))
palette.lime = ('rgb',drgb('A2F218')) # Unused
palette.green = ('rgb',drgb('00E56B')) # Unused
palette.cyan = ('rgb',drgb('00CCC5')) # Unused
palette.blue = ('rgb',drgb('1442CC')) # Unused
palette.grey = ('rgb',drgb('C3D0D8')) # Unused
love_meter = drift(0.03,0.5) # 0 = hate, 1 = love
love_meter_x = drift(0.03,-200)
love_meter_particle_system = particle_system([[-200,-80],[-height/2,height/2]],[[0,2],[-1,1]],[[-0.01,0.01],[-0.01,0.01]],height/2+100,8*base_particles,2)
timer_time = None
timer_func = None
timer_size = drift(0.1,80)
timer_y = drift(0.1,height+300)
timer_particle_system = particle_system([[-80,80],[80,200]],[[-1,1],[-2,0]],[[-0.01,0.01],[-0.01,0.01]],300,1*base_particles,1)
captions = []
caption_y = drift(0.1,-200)
buttons = []
button_glow = [loadimage('glow'+str(i)+'.png') for i in range(1,6)]
button_particle_systems = [particle_system([[80,200],[-80,80]],[[-4,-1],[-2,2]],[[-0.02,0.02],[-0.02,0.02]],width,3*base_particles,1) for _ in range(8)]
for particles in button_particle_systems+[love_meter_particle_system,timer_particle_system]:
    for _ in range(200):
        particles.step()
background_image = None
background_x = drift(0.003,width/2)
background_y = drift(0.003,height/2)
characters = {} # TODO make characters and reference them here
mouse_x,mouse_y = mouse_xy = 0,0

# ======================================================================================================================================================
#
# Story is hardcoded
#
# ======================================================================================================================================================

# Test menu items (not deleted because it could be a useful reference)
##p_menu_1 = fw_exec_all(fw_branch_to(['...','p_menu_1a']),fw_caption_set('So basically'),)
##p_menu_1a = fw_exec_all(fw_branch_to(['...','p_menu_1b']),fw_caption_set('This is how dialogue will work'))
##p_menu_1b = fw_exec_all(fw_branch_to(['...','p_menu_1c']),fw_caption_set('We\'ll give each character\ntheir own colour\nor something like that',('hsv',(0.6,0.8,0.8))))
##p_menu_1c = fw_branch_to(['1 -> 2','p_menu_2'],['1 -> 3','p_menu_3'],['1 -> 1','p_menu_1'])
##p_menu_2 = fw_meter_condition('>',0.14,fw_exec_all(fw_branch_to(['2 -> 3','p_menu_3'],['2 -> 1','p_menu_1'],['2 -> 2','p_menu_2']),fw_meter_add(-0.13)),fw_branch_to(['uh oh','p_menu_2b']))
##p_menu_2b = fw_exec_all(fw_branch_to(['to 2','p_menu_2'],['to 4','p_menu_4']),fw_caption_set('Love metred'),fw_meter_add(0.5))
##p_menu_3 = fw_branch_to(['3 -> 1','p_menu_1'],['3 -> 2','p_menu_2'],['3 -> 3','p_menu_3'],['3 -> 4','p_menu_4'])
##p_menu_4 = fw_exec_all(fw_branch_to(['4 -> 1','p_menu_1'],['4 -> 2','p_menu_2']),fw_timer_set(10,'p_menu_5'))
##p_menu_5 = fw_branch_to(['5 -> 1','p_menu_1'],['5 -> 2','p_menu_2'],['5 -> 4','p_menu_4'])
##p_menu_6 = fw_branch_to(['1 >>',p_menu_1],['2 >>',p_menu_2],['3 >>',p_menu_3],['4 >>',p_menu_4])
##fw_branch_to(['Play',fw_exec_all(fw_meter_status(True),p_menu_6)])()
# Story, paths, etc.

# ------------------------------------------------------------------------------------------------------------------------------------------------------
# Opening sequence

p_intro_a = fw_branch_to(['Play','p_1_1aa'])
p_intro_ba = fw_background_set(img='artgallery.png',cxy=(width-1936,height/2)),redir('p_intro_bb'),fw_caption_set('Yu and Lily were lovers in highschool.',palette.narration)
p_intro_bb = redir('p_intro_bc'),fw_caption_set('You play as Marcel, their mutual friend.',palette.narration)
p_intro_bc = fw_background_set(txy=(1936,height/2)),redir('p_intro_bd'),fw_caption_set('Here you are at an art gallery',palette.narration)
p_intro_bd = redir('p_intro_be'),fw_caption_set('where you find Lily and her commissioned painter, Yu.',palette.narration)
p_intro_be = redir('p_intro_bf'),fw_caption_set('Lily is an art director at Axolotl Design Inc. and is already married to a hotshot lawyer.',palette.narration)
p_intro_bf = redir('p_intro_a'),fw_caption_set('Could this have gone differently?',palette.narration)
# Currently sets to the default, TODO read save file if present
p_intro = p_intro_ba

# ------------------------------------------------------------------------------------------------------------------------------------------------------
# Part 1, scene 1: before business class

p_1_1aa = fw_background_set(img='hallway.png',cxy=(width/2,height-600)),redir('p_1_1ab'),fw_caption_set('6 years earlier, in grade 12, just before\nthe start of a shared class, International Business.',palette.narration)
p_1_1ab = redir('p_1_1ac'),fw_caption_set('Lily is currently dating Rustam. Yu is a hobbyist painter.',palette.narration)
p_1_1ac = fw_meter_status(True),fw_background_set(txy=(width/2,600)),fw_branch_to(('Talk to Yu','p_1_2aa'),('Talk to Lily','p_1_3aa')),fw_timer_set(15,'p_1_4aa')

# ------------------------------------------------------------------------------------------------------------------------------------------------------
# Part 1, scene 2: talking with Yu before class

p_1_2aa = fw_branch_to(('Hi','p_1_2ba')),fw_timer_set(7,'p_1_2ca')

p_1_2ba = redir('p_1_2bb'),fw_caption_set('Hi Yu.',palette.player)
p_1_2bb = redir('p_1_2bc'),fw_caption_set('Oh. Hi Marcel.',palette.yu)
p_1_2bc = redir('p_1_2bd'),fw_caption_set('I\'m just drawing a thing for Painting.',palette.yu)
p_1_2bd = fw_branch_to(('Look','p_1_2da')),fw_timer_set(5,'p_2_ea')

p_1_2ca = redir('p_1_2cb'),fw_caption_set('Hi Marcel.',palette.yu)
p_1_2cb = redir('p_1_2cc'),fw_caption_set('Bored? I guess anyone would be.',palette.yu)
p_1_2cc = redir('p_1_4aa'),fw_caption_set('I\'ll get back to painting.',palette.yu)

p_1_2da = redir('p_1_2db'),fw_caption_set('Wow, you\'ve gotten a lot better with characters.',palette.player)
p_1_2db = redir('p_1_2dc'),fw_caption_set('Yeah, it\'s thanks to learning anatomy.',palette.yu)
p_1_2dc = redir('p_1_2dd'),fw_caption_set('It was a nice change from art history.',palette.yu)
p_1_2dd = redir('p_1_4aa'),fw_caption_set('Well, class is starting soon. Let\'s go?',palette.yu)

p_1_2ea = redir('p_1_4aa'),fw_caption_set('I\'ll leave you to it then.',palette.player)

# ------------------------------------------------------------------------------------------------------------------------------------------------------
# Part 1, scene 3: talking with Lily before class

p_1_3aa = redir('p_1_3ab'),fw_caption_set('Hey Marcel. Ready for trade?',palette.lily)
p_1_3ab = redir('p_1_3ac'),fw_caption_set('Huh? Oh, did you read the entire syllabus?',palette.player)
p_1_3ac = redir('p_1_3ad'),fw_caption_set('I like to be prepared.',palette.lily)
p_1_3ad = fw_branch_to(('Rustam','p_1_3ba'),('Clubs','p_1_3ca'))

p_1_3ba = redir('p_1_3bb'),fw_caption_set('Anything new with Rustam?',palette.player)
p_1_3bb = redir('p_1_3bc'),fw_caption_set('Well, now that you\'ve asked, I kind of have to tell you don\'t I?',palette.lily)
p_1_3bc = redir('p_1_3bd'),fw_caption_set('No. You\'re entitled to some amount of privacy.',palette.player)
p_1_3bd = redir('p_1_3be'),fw_caption_set('But it\'d be bad mannered not to share something so petty.',palette.lily)
p_1_3be = redir('p_1_3bf'),fw_caption_set('So the one time I\'m free for a date, Rustam is streaming League of Legends.',palette.lily)
p_1_3bf = redir('p_1_3bg'),fw_caption_set('It wouldn\'t have been so bad if he had seemed to care.',palette.lily)
p_1_3bg = redir('p_1_3bh'),fw_caption_set('Why are you still with him?',palette.player)
p_1_3bh = redir('p_1_3bi'),fw_caption_set('These things happen I guess.',palette.lily)
p_1_3bi = redir('p_1_3bj'),fw_caption_set('I\'d want another chance, so I chose to forgive him.',palette.lily)
p_1_3bj = redir('p_1_3bk'),fw_caption_set('You shouldn\'t stay with someone so apathetic.',palette.player)
p_1_3bk = redir('p_1_3bl'),fw_caption_set('Apathetic? Do you read dictionaries in your spare time or something?',palette.lily)
p_1_3bl = redir('p_1_3bm'),fw_caption_set('Whatever. You can\'t seriously call someone who favours gaming over you, your boyfriend.',palette.player)
p_1_3bm = redir('p_1_3bn'),fw_caption_set('Well, I favour DECA over him, I can understand how he could be so attracted to gaming.',palette.lily)
p_1_3bn = redir('p_1_3bo'),fw_caption_set('DECA accomplishes something. Casual League doesn\'t.',palette.player)
p_1_3bo = redir('p_1_3bp'),fw_caption_set('Really, don\'t try to defend him. Just tell him.',palette.player)
p_1_3bp = redir('p_1_4aa'),fw_caption_set('There are plenty of fish in the sea.',palette.player)

p_1_3ca = redir('p_1_3cb'),fw_caption_set('How\'s DECA going?',palette.player)
p_1_3cb = redir('p_1_3cc'),fw_caption_set('Our board is right around the corner. You could\'ve checked before asking me.',palette.lily)
p_1_3cc = redir('p_1_3cd'),fw_caption_set('Anyways, I\'m club president now.',palette.lily)
p_1_3cd = redir('p_1_3ce'),fw_caption_set('It won\'t be long before we get gold again.',palette.lily)
p_1_3ce = redir('p_1_3cf'),fw_caption_set('Do you even need school?',palette.player)
p_1_3cf = redir('p_1_4aa'),fw_caption_set('For the certification, yes.',palette.lily)

# ------------------------------------------------------------------------------------------------------------------------------------------------------
# Part 1, scene 4: business class

#

# ------------------------------------------------------------------------------------------------------------------------------------------------------
# Go!
funcify(p_intro)()

# ======================================================================================================================================================
#
# Rendering and updates
#
# ======================================================================================================================================================
for _ in mainloop():
    mouse_x,mouse_y = mouse_xy = mousepos()
    draw_background()
    draw_characters()
    draw_buttons()
    draw_meter()
    draw_timer()
    draw_captions()
