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
# Set font
try:
    setfont('Verdana',-1,-1)
except:
    print('Unable to change font')

# Override image loading and bundle with unload
oloadimage = loadimage
images = {}
def loadimage(name):
    """
    Load an image from file
    Memoizes
    """
    if type(name)==list:name=tuple(name)
    if name not in images:
        images[name]=oloadimage(name) if type(name)==str else image_sequence_loader(*name)
    return images[name]
def unloadimage(name):
    """
    Dereferences an image
    """
    images.pop(name,None)

# Override image drawing
odrawimage = drawimage
def drawimage(image,*args,**kwargs):
    """
    Redirect to draw method if available
    Can have side effects if arguments not matching drawimage
    """
    if hasattr(image,'draw'):
        image.draw(*args,**kwargs)
    else:
        odrawimage(image,*args,**kwargs)

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
        return self.frame>=self.frames-1
    def reset(self):
        """
        Go back to the beginning
        """
        self.frame = 0
    def draw(ixy,ialpha=1.0,**kwargs):
        """
        Draws the current frame
        """
        if ialpha>0.998:
            drawimage(self.images[self.frame],ixy,**kwargs)
        elif ialpha>0.002:
            drawimage(alpha(self.images[self.frame],ialpha),ixy,**kwargs)

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
    def draw(self,*args,**kwargs):
        """
        Convenience draw method
        """
        iseq = self.fetch()
        iseq.draw(*args,**kwargs)
        iseq.step()
    def atend(self):
        """
        Convenience is-at-the-end-of-the-animation method
        """
        return self.fetch().atend()

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
    def __init__(self,texts,colors=None,style=0,**kwargs):
        global width,height,linelength
        if 'prefix' in kwargs:texts=globals()[kwargs['prefix']]+'\n'+texts
        self.size = size = 20000//(max(len(texts)-200,0)+800)
        sections = texts.split('\n')
        texts = []
        for sect in sections:texts+=autosplit(sect,size)+['']
        self.texts = texts
        self.x = drift(0.1,width/2)
        self.y = drift(0.1,150,100)
        self.alpha = drift(0.1,1,0) # Alpha
        self.color = {'rgb':0} if colors is None else {colors[0]:colors[1]}
        self.style = style
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
        setfont(None,self.style,self.size)
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
            if text:
                image = alpha(render(text),ialpha)
                drawimage(image,(270,y),xalign=0)
            y -= self.size

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
        setcolor(rgb=0.95)
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
        setcolor(rgb=0.05)
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
        iseql.draw((ix,iy),ialpha)
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
    if type(background_image)==dict:
        background_image = next(iter(background_image.items()))
    if type(background_image) in {tuple,list}:
        setcolor(**{background_image[0]:tuple(map(float,background_image[1]))})
        fill()
    elif background_image is not None:
        if type(background_image)==str:background_image=loadimage(background_image)
        background_x.step()
        background_y.step()
        drawimage(background_image,(float(background_x),float(background_y)))
    else:
        setcolor(rgb=1.0)
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
    setcolor(rgb=0.05)
    img_glow = button_glow[0]
    setpolyclip([[ix-30,40],[ix,30],[ix+30,40],[ix+30,iy],[ix-30,iy]])
    fill()
    for particle in particles:
        px,py = particle[0:2]
        drawimage(img_glow,(px,py+height/2))
    # Upper half
    setcolor(rgb=0.05)
    img_glow = button_glow[3]
    setpolyclip([[ix-30,height-40],[ix,height-30],[ix+30,height-40],[ix+30,iy],[ix-30,iy]])
    fill()
    for particle in particles:
        px,py = particle[0:2]
        drawimage(img_glow,(px,py+height/2))
    # Text
    setcolor(rgb=0.95)
    setpolyclip()
    setfont(None,0,int(30*(0.5+ir)))
    drawimage(render('Hate'),(ix+40,40),xalign=0)
    setfont(None,0,int(30*(1.5-ir)))
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
        timer_remaining = timer_time-time()
        if timer_remaining>0:
            timer_size.target = 400/(timer_remaining+5)
            timer_str = str(timer_remaining)[:4]
        else:
            timer_time = None
            funcify(timer_func)()
    else:
        timer_size.target = 40
    timer_y.target = height if timer_time and timer_visible else height+300
    timer_size.step()
    itimer_size = float(timer_size)
    timer_radius = itimer_size*1.8
    if oy<height+timer_radius:
        setcolor(rgb=0.05)
        setpolyclip([[ox+timer_radius*cos(i*pi/32),oy+timer_radius*sin(i*pi/32)] for i in range(64)])
        fill()
        img_glow = button_glow[2]
        timer_particle_system.step()
        for particle in timer_particle_system.particles:
            px,py = particle[0:2]
            drawimage(img_glow,(px+ox,py+oy))
    setcolor(rgb=0.95)
    setfont(None,0,int(itimer_size))
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
        setcolor(rgba=(0.3,)*3+(0.8,))
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

def onkey(etype,ekey):
    """
    Handles key events
    """
    global player_name,player_name_edit,captions
    if player_name_edit and etype=='press':
        if ekey==222:ekey=39
        if ekey==8:
            player_name = player_name[:-1]
        elif chr(ekey).lower() in 'abcdefghijklmnopqrstuvwxyz-\' ' and len(player_name)<20:
            player_name += chr(ekey)
        captions[0].texts[1] = player_name if player_name else '<type something>'
bindkey('key event',onkey)

# ======================================================================================================================================================
#
# Functional utilities
#
# ======================================================================================================================================================

def autosplit(texts,size):
    """
    Automatically break up text, used by captions
    """
    linelength=1400//size
    result = []
    parts = texts.split(' ')[::-1]
    bl = len(texts)
    while bl>linelength:
        a = []
        al = -1
        tl = bl//ceil(bl/linelength)
        while al<tl:
            nx = parts.pop()
            ic = len(nx)+1
            al += ic
            bl -= ic
            a.append(nx)
        result.append(' '.join(a))
    result.append(' '.join(parts[::-1]))
    return result

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
            if len(params)==2 or globals().get(params[2],False): # Easy predicate
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
    def ifw_meter_condition():
        if comp(love_meter.target,value):
            funcify(if_true)()
        else:
            funcify(if_false)()
    return ifw_meter_condition

def timer_set(seconds,func=None,visible=True):
    """
    Set the timer to last a certain number of seconds, then call func
    Call with None, 0, False, etc. to disable the timer
    """
    global timer_time,timer_func,timer_visible
    if seconds:
        timer_time = time()+seconds
        timer_func = func
        timer_visible = visible
    else:
        timer_time = None

def fw_timer_set(seconds,func=None,visible=True):
    """
    Return a function to set the timer later
    """
    def ifw_timer_set():
        timer_set(seconds,func,visible)
    return ifw_timer_set

def fw_caption_set(*args,**kwargs):
    """
    Return a function to clear all captions and set it to the given
    """
    def ifw_caption_set():
        global captions
        clear_captions()
        captions.append(caption(*args,**kwargs))
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

def fw_var_set(name,value):
    """
    Set a global variable
    """
    def ifw_var_set():
        globals()[name]=value
    return ifw_var_set

def fw_var_branch(name,to):
    """
    Branch to using value as key if it exists, or -1 if it doesn't exist
    """
    def ifw_var_branch():
        v = globals().get(name,-1)
        try:
            funcify(to[v])()
        except:
            pass
    return ifw_var_branch

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

def fw_validate_name(func):
    """
    Proceed only if the name is valid
    """
    def ifw_validate_name():
        global player_name,player_name_edit
        # Capitalize
        ocs = list(player_name)
        cap = 0
        for i,c in enumerate(ocs):
            if c in '\'- ':
                if cap<2:break
                cap=0
            else:
                ocs[i] = c.lower() if cap else c.upper()
                cap+=1
        if cap>=2:
            player_name = ''.join(ocs)
            player_name_edit = False
            funcify(func)()
    return ifw_validate_name

def fw_ending(number):
    """
    Ending
    """
    pass

# ======================================================================================================================================================
#
# Initialize globals
#
# ======================================================================================================================================================

# Constants and configurations
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
palette.narration = ('rgb',drgb('C3D0D8')) # Grey
palette.player = ('rgb',drgb('E5A0BB')) # Pink
palette.lily = ('rgb',drgb('A0C4E5')) # Aqua
palette.yu = ('rgb',drgb('E5D489')) # Yellow
palette.rustam = ('rgb',drgb('E5A395')) # Orange
palette.teacher = ('rgb',drgb('97D8D4')) # Turqoise
palette.spare1 = ('rgb',drgb('D5F2A9')) # Lime
palette.spare2 = ('rgb',drgb('A0E5B4')) # Green
palette.spare4 = ('rgb',drgb('B9B7E5')) # Blue
palette.spare5 = ('rgb',drgb('D8A0E5')) # Purple
love_meter = drift(0.03,0.5) # 0 = hate, 1 = love
love_meter_x = drift(0.03,-200)
love_meter_particle_system = particle_system([[-200,-80],[-height/2,height/2]],[[0,2],[-1,1]],[[-0.01,0.01],[-0.01,0.01]],height/2+100,8*base_particles,2)
timer_time = None
timer_visible = True
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
player_name = 'Player'
player_name_edit = False

# ======================================================================================================================================================
#
# Story is hardcoded
#
# ======================================================================================================================================================

# ------------------------------------------------------------------------------------------------------------------------------------------------------
# Opening sequence

p_intro_a = fw_background_set(img=('rgb',(0,0,0))),fw_branch_to(['Play',fw_validate_name('p_1_1aa')]),fw_var_set('player_name',''),fw_var_set('player_name_edit',True),fw_caption_set('Enter your name:\n<type something>',palette.narration)
p_intro_ba = fw_background_set(img=('rgb',(0,0,0))),redir('p_intro_bb'),fw_caption_set('Whatever we are, I still remember the way we were',palette.narration,2)
p_intro_bb = fw_background_set(img='gallery2.png',cxy=(width/2,height/2)),redir('p_intro_bc')
p_intro_bc = redir('p_intro_bd'),fw_caption_set('Yu! What\'s wrong?',palette.player,prefix='player_name')
p_intro_bd = redir('p_intro_bd2'),fw_caption_set('Yu\nI\'ve lost her.',palette.yu)
p_intro_bd2 = redir('p_intro_be'),fw_caption_set('Yu\nIt\'s too late now.',palette.yu)
p_intro_be = redir('p_intro_bf'),fw_caption_set('Wait, what do you mean, who?',palette.player,prefix='player_name')
p_intro_bf = redir('p_intro_bg'),fw_caption_set('Yu\nLily.',palette.yu)
p_intro_bg = redir('p_intro_bh'),fw_caption_set('It\'s raining. Tonight is the world premiere of Yu\'s first major painting:',palette.narration)
p_intro_bh = redir('p_intro_bi'),fw_caption_set('Perennial Requiem',palette.narration,2)
p_intro_bi = redir('p_intro_bj'),fw_caption_set('A banquet is currently being held in his celebration at the Toronto Axolotl gallery.',palette.narration)
p_intro_bj = redir('p_intro_bk'),fw_caption_set('Tonight is the night Yu had prepared for for many months.',palette.narration)
p_intro_bk = redir('p_intro_bk2'),fw_caption_set('Tonight was supposed to be the night he would see Lily, his high school sweetheart, for the first time in 5 years.',palette.narration)
p_intro_bk2 = redir('p_intro_bl'),fw_caption_set('He had prepared to confess his love and apologize for the conflict that happened many years ago.',palette.narration)
p_intro_bl = redir('p_intro_bl'),fw_caption_set('That was the plan.',palette.narration)
p_intro_bm = redir('p_intro_bn'),fw_caption_set('Until Lily\'s new fiance walked in and kissed her on the cheek.',palette.narration)
p_intro_bn = redir('p_intro_bo'),fw_caption_set('Heartbroken, Yu sobs outside.',palette.narration)
p_intro_bn = redir('p_intro_bo'),fw_caption_set('He is your best friend having been in your class throughout high school.',palette.narration)
p_intro_bn = redir('p_intro_bo'),fw_caption_set('You want to help, but don\'t know how.',palette.narration)
p_intro_bo = redir('p_intro_bo2'),fw_caption_set('You think back to the time when you, Yu and Lily were all just students in business class.',palette.narration)
p_intro_bo2 = redir('p_intro_bo3'),fw_caption_set('The two friends were in love,',palette.narration)
p_intro_bo3 = redir('p_intro_bo4'),fw_caption_set('But never told each other,',palette.narration)
p_intro_bo4 = redir('p_intro_bp'),fw_caption_set('As fate had other plans.',palette.narration)
p_intro_bp = redir('p_intro_bq'),fw_caption_set('Until that fateful day...',palette.narration)
p_intro_bq = redir('p_intro_br'),fw_caption_set('That terrible misunderstanding...',palette.narration)
p_intro_br = redir('p_intro_a'),fw_caption_set('If you only encouraged them more back then, would this have happened?',palette.narration)
p_intro = p_intro_ba

# ------------------------------------------------------------------------------------------------------------------------------------------------------
# Part 1, scene 1: before business class

p_1_1aa = fw_background_set(img='classroom2.png',cxy=(width/2,height/2)),redir('p_1_1ab'),fw_caption_set('Early October.',palette.narration)
p_1_1ab = redir('p_1_1ac'),fw_caption_set('Before class.',palette.narration)
p_1_1ac = redir('p_1_1ad'),fw_caption_set('You\'re bored and waiting for the teacher to arrive.',palette.narration)
p_1_1ad = fw_branch_to(('Talk to Yu','p_1_2aa'),('Talk to Lily','p_1_3aa')),fw_timer_set(15,'p_1_4aa'),fw_meter_status(True)

# ------------------------------------------------------------------------------------------------------------------------------------------------------
# Part 1, scene 2: talking with Yu before class

p_1_2aa = redir('p_1_2ab'),fw_caption_set('Psst.',palette.player,prefix='player_name'),fw_var_set('f_1_2a',0)
p_1_2ab = redir('p_1_2ac'),fw_caption_set('Yu.',palette.player,prefix='player_name')
p_1_2ac = redir('p_1_2ad'),fw_caption_set('What\'re you drawing?',palette.player,prefix='player_name')
p_1_2ad = redir('p_1_2ae'),fw_caption_set('You catch a glimpse of a familiar flower as he closes his sketchbook.',palette.narration),fw_meter_add(0.1)
p_1_2ae = redir('p_1_2af'),fw_caption_set('Yu\nNothing.',palette.yu)
p_1_2af = redir('p_1_2ag'),fw_caption_set('You\'re drawing her again, aren\'t you?',palette.player,prefix='player_name')
p_1_2ag = redir('p_1_2ag2'),fw_caption_set('Yu\nIt\'s just a lilium.',palette.yu)
p_1_2ag2 = redir('p_1_2ag3'),fw_caption_set('Also known as a lily.',palette.narration)
p_1_2ag3 = redir('p_1_2ah'),fw_caption_set('The flower Lily is named after.',palette.narration)
p_1_2ah = redir('p_1_2ai'),fw_caption_set('Yu\nNothing more.',palette.yu)
p_1_2ai = redir('p_1_2aj'),fw_caption_set('Yu\nNothing less.',palette.yu,2)
p_1_2aj = redir('p_1_2ak'),fw_caption_set('Sure sure.',palette.player,prefix='player_name')
p_1_2ak = redir('p_1_2al'),fw_caption_set('Well, just a heads up,',palette.player,prefix='player_name')
p_1_2al = redir('p_1_2am'),fw_caption_set('She has a boyfriend.',palette.player,prefix='player_name')
p_1_2am = redir('p_1_2an')
p_1_2an = redir('p_1_2ao'),fw_caption_set('Yu\nCool.',palette.yu)
p_1_2ao = redir('p_1_2ap'),fw_caption_set('Alright mister nonchalant.',palette.player,prefix='player_name')
p_1_2ap = redir('p_1_4aa'),fw_caption_set('I\'ll leave you to your drawing then.',palette.player,prefix='player_name')

# ------------------------------------------------------------------------------------------------------------------------------------------------------
# Part 1, scene 3: talking with Lily before class

p_1_3aa = redir('p_1_3ab'),fw_caption_set('Hey Lily.',palette.player,prefix='player_name')
p_1_3ab = redir('p_1_3ac'),fw_caption_set('Did you read the whole syllabus?',palette.player,prefix='player_name')
p_1_3ac = redir('p_1_3ad'),fw_caption_set('Lily\nBusiness is my future.',palette.lily)
p_1_3ad = redir('p_1_3ae'),fw_caption_set('Lily\nI want to be prepared.',palette.lily)
p_1_3ae = redir('p_1_3af'),fw_caption_set('Touch\xe9.',palette.player,prefix='player_name')
p_1_3af = redir('p_1_3ag'),fw_caption_set('So...',palette.player,prefix='player_name')
p_1_3ag = redir('p_1_3ah'),fw_caption_set('Anything new with Rustam?',palette.player,prefix='player_name')
p_1_3ah = redir('p_1_3ai'),fw_caption_set('Lily\nUgh.',palette.lily,2)
p_1_3ai = redir('p_1_3aj'),fw_caption_set('Lily\nDon\'t even get me started.',palette.lily)
p_1_3aj = redir('p_1_3ak'),fw_caption_set('On what?',palette.player,prefix='player_name')
p_1_3ak = redir('p_1_3al'),fw_caption_set('Lily\nWe were supposed to go bowling tonight,',palette.lily)
p_1_3al = redir('p_1_3am'),fw_caption_set('Lily\nBut he was just invited to play League,',palette.lily)
p_1_3am = redir('p_1_3an'),fw_caption_set('Lily\nAnd...',palette.lily)
p_1_3an = redir('p_1_3ao'),fw_caption_set('Lily\nWell...',palette.lily)
p_1_3ao = redir('p_1_3ap')
p_1_3ap = redir('p_1_3aq'),fw_caption_set('Lily\nThere goes our plans.',palette.lily,2)
p_1_3aq = redir('p_1_3ar')
p_1_3ar = redir('p_1_3as'),fw_caption_set('Priorities, right?',palette.player,prefix='player_name')
p_1_3as = redir('p_1_3at'),fw_caption_set('Lily\nI mean, it wouldn\'t be so bad if he seemed to care.',palette.lily)
p_1_3at = redir('p_1_3au'),fw_caption_set('Why are you still with him?',palette.player,prefix='player_name')
p_1_3au = redir('p_1_3av'),fw_caption_set('Lily\nI\'ve ditched him a couple times for DECA anyways.',palette.lily)
p_1_3av = redir('p_1_3aw'),fw_caption_set('Lily\nI\'ll forgive him this time.',palette.lily)
p_1_3aw = fw_branch_to(('Whatever you say','p_1_3ba'),('No you shouldn\'t','p_1_3bb'),('Don\'t go easy on him.','p_1_3bc'),('You know who you should date instead?','p_1_3bd')),fw_timer_set(5,'p_1_3be')

p_1_3ba = redir('p_1_3be1'),fw_caption_set('Whatever you sa-',palette.player,prefix='player_name'),fw_timer_set(0.5,'p_1_3be1',False),fw_meter_add(-0.1)
p_1_3bb = redir('p_1_3be2'),fw_caption_set('No you shouldn-',palette.player,prefix='player_name'),fw_timer_set(0.5,'p_1_3be2',False),fw_meter_add(-0.02)
p_1_3bc = redir('p_1_3be3'),fw_caption_set('Don\'t go easy on hi-',palette.player,prefix='player_name'),fw_timer_set(0.7,'p_1_3be3',False),fw_meter_add(-0.05)
p_1_3bd = redir('p_1_3be4'),fw_caption_set('You know who you should date instea-',palette.player,prefix='player_name'),fw_timer_set(1.2,'p_1_3be4',False),fw_meter(-0.07)
p_1_3be1 = redir('p_1_3bf'),fw_caption_set('She shouldn\'t have been so forgiving. You should have given her a push in the right direction.',palette.narration)
p_1_3be2 = redir('p_1_3bf'),fw_caption_set('Strongly telling her it\'s a bad decision. Good choice.',palette.narration)
p_1_3be3 = redir('p_1_3bf'),fw_caption_set('A shove in the right direction, but not direct enough.',palette.narration)
p_1_3be4 = redir('p_1_3bf'),fw_caption_set('Perhaps you should be less aggressive about getting them together.',palette.narration)
p_1_3bf = redir('p_1_3bg'),fw_caption_set('Rustam\nYou talkin\' about me mate?',palette.rustam)
p_1_3bg = redir('p_1_3bh')
p_1_3bh = redir('p_1_3bi'),fw_caption_set('Lily\nWhatever.',palette.lily,2)
p_1_3bi = redir('p_1_3bi2'),fw_caption_set('Rustam\nJoin us in League sometime?',palette.rustam)
p_1_3bi2 = redir('p_1_3bi3'),fw_caption_set('Lily is mildly annoyed with Rustam.',palette.narration)
p_1_3bi3 = redir('p_1_3bj'),fw_caption_set('She considers breaking up.',palette.narration)
p_1_3bj = redir('p_1_4aa'),fw_caption_set('Lily\nNo.',palette.lily,2),fw_meter_add(0.15)

# ------------------------------------------------------------------------------------------------------------------------------------------------------
# Part 1, scene 4: business class

p_1_4aa = redir('p_1_4ab')
p_1_4ab = redir('p_1_4ac'),fw_caption_set('Mr.Faisal\nAlright class,',palette.teacher)
p_1_4ac = redir('p_1_4ad'),fw_caption_set('Mr.Faisal\nLet\'s begin.',palette.teacher)
p_1_4ad = redir('p_1_4ae'),fw_caption_set('Mr.Faisal\nToday\'s lesson:',palette.teacher)
p_1_4ae = redir('p_1_4af'),fw_caption_set('Mr.Faisal\nEtiquette among entrepreneurs.',palette.teacher)
p_1_4af = redir('p_1_4ag'),fw_caption_set('Mr.Faisal\nEveryone please take out your textbooks,',palette.teacher)
p_1_4ag = redir('p_1_4ah'),fw_caption_set('Mr.Faisal\nAnd turn to page 88.',palette.teacher)
p_1_4ah = redir('p_2_1aa'),fw_caption_set('Mr.Faisal\nLet\'s run through attendance...',palette.teacher)

# ------------------------------------------------------------------------------------------------------------------------------------------------------
# Part 2, scene 1: at cafe together

p_2_1aa = fw_background_set(img='cafe2.png',cxy=(width/2,height/2)),redir('p_2_1ab'),fw_caption_set('The next day.',palette.narration)
p_2_1ab = redir('p_2_1af'),fw_caption_set('The four of you are getting coffee as a group.',palette.narration)
p_2_1af = redir('p_2_1ag'),fw_caption_set('No-one is talking.',palette.narration)
p_2_1ac = redir('p_2_1ad'),fw_caption_set('Yu is tucked in the corner of the booth, sketching while sneaking glances at Lily.',palette.narration)
p_2_1ad = redir('p_2_1ae'),fw_caption_set('Lily is checking her phone.',palette.narration)
p_2_1ae = redir('p_2_1ag'),fw_caption_set('Rustam is discreetly eyeing the attractive barista.',palette.narration)
p_2_1ag = fw_branch_to(('Ask Rustam about his League of Legends night','p_2_1ba'),('Ask Yu about the business project','p_2_1ca')),fw_timer_set(15,'p_2_1da')

p_2_1ba = redir('p_2_1bb'),fw_caption_set('Rustam, how was your gaming night?',palette.player,prefix='player_name')
p_2_1bb = redir('p_2_1bc'),fw_caption_set('Rustam\nWe played \'till 4 AM.',palette.rustam)
p_2_1bc = redir('p_2_1bd'),fw_caption_set('Rustam\nSo lit.',palette.rustam)
p_2_1bd = redir('p_2_1be')
p_2_1be = redir('p_2_1bf'),fw_caption_set('Lily\nReally?',palette.lily,2)
p_2_1bf = redir('p_2_1bg'),fw_caption_set('Lily\nThat\'s how you spent the whole night?',palette.lily,2)
p_2_1bg = redir('p_2_1bh'),fw_caption_set('Lily\nDo you not sleep?',palette.lily,2)
p_2_1bh = redir('p_2_1bi'),fw_caption_set('Lily\nWhy can\'t you be a little less social?',palette.lily,2)
p_2_1bi = redir('p_2_1bj'),fw_caption_set('Lily\nWhy can\'t you be more like Yu?',palette.lily,3)
p_2_1bj = redir('p_2_1bk')fw_caption_set('Lily just declared she prefers Yu',palette.narration),fw_meter_add(0.02)
p_2_1bk = redir('p_2_1bl'),fw_caption_set('Yu\nIs that a compliment?',palette.yu)
p_2_1bl = fw_branch_to(('Yes','p_2_1ea2')),fw_timer_set(3,'p_2_1ea')

p_2_1ca = fw_var_set('f_2_1c',True),redir('p_2_1cb'),fw_caption_set('Yu,',palette.player,prefix='player_name')
p_2_1cb = redir('p_2_1cc'),fw_caption_set('How\'s your business project going?',palette.player,prefix='player_name')
p_2_1cc = redir('p_2_1cd'),fw_caption_set('Yu\nAlright.',palette.yu)
p_2_1cd = redir('p_2_1ce'),fw_caption_set('Okay...',palette.player,prefix='player_name')
p_2_1ce = redir('p_2_1cf'),fw_caption_set('Who are you paired up with?',palette.player,prefix='player_name')
p_2_1cf = redir('p_2_1cg'),fw_caption_set('Yu\nNo-one yet.',palette.yu)
p_2_1cg = redir('p_2_1ch'),fw_caption_set('Yu glances at Lily.',palette.narration)
p_2_1ch = redir('p_2_1ci'),fw_caption_set('She\'s looking at his sketchbook.',palette.narration)
p_2_1ci = redir('p_2_1cj'),fw_caption_set('Lily\nWow, that\'s cool.',palette.lily)
p_2_1cj = redir('p_2_1ck'),fw_caption_set('Lily\nWhat are you working on?',palette.lily)
p_2_1ck = redir('p_2_1ck2'),fw_caption_set('Yu\nNothing important.',palette.yu)
p_2_1ck2 = redir('p_2_1cl'),fw_caption_set('Yu quickly closes his sketchbook embarrassedly.',palette.narration)
p_2_1cl = redir('p_2_1cm'),fw_caption_set('Lily\nShow us.',palette.lily)
p_2_1cm = redir('p_2_1cn'),fw_caption_set('Rustam\nWhat are you hiding?',palette.rustam)
p_2_1cn = redir('p_2_1ed'),fw_caption_set('Yu\nWell...',palette.yu)

p_2_1da = redir('p_2_1db')
p_2_1db = redir('p_2_1dc'),fw_caption_set('So...',palette.player,prefix='player_name')
p_2_1dc = redir('p_2_1dd'),fw_caption_set('Why are we here again?',palette.player,prefix='player_name')
p_2_1dd = redir('p_2_1de')
p_2_1de = redir('p_2_1df'),fw_caption_set('Ugh, I\'m leaving.',palette.player,prefix='player_name')
p_2_1df = redir('p_2_2aa'),fw_caption_set('Still no response.',palette.narration),fw_meter_add(-0.1)

p_2_1ea2 = redir('p_2_1ea3'),fw_caption_set('Yes.',palette.player,prefix='player_name')
p_2_1ea3 = redir('p_2_1ea4'),fw_caption_set('Yu\nThanks.',palette.yu),fw_meter_add(0.02)
p_2_1ea4 = redir('p_2_1ea'),fw_caption_set('Yu\'s confidence has been boosted.',palette.narration)
p_2_1ea = redir('p_2_1eb'),fw_caption_set('Yu\nWell,',palette.yu)
p_2_1eb = redir('p_2_1ec'),fw_caption_set('Yu\nI like League too.',palette.yu)
p_2_1ec = redir('p_2_1ed'),fw_caption_set('Yu\nIn fact,',palette.yu)
p_2_1ed = redir('p_2_1ee'),fw_caption_set('Yu\nI\'ve drawn some sketches of Jhin the Virtuoso a few times in the past.',palette.yu)
p_2_1ee = redir('p_2_1ef'),fw_caption_set('Lily\nReally?',palette.lily)
p_2_1ef = redir('p_2_1eg'),fw_caption_set('Lily\nThat sounds pretty cool.',palette.lily)
p_2_1eg = fw_branch_to(('Ask Yu to show them to the group','p_2_1ga'),('Continue to ask Rustam about League','p_2_1ha','f_2_1c'))

p_2_1ga = redir('p_2_1gb'),fw_caption_set('Can we see?',palette.player,prefix='player_name')
p_2_1gb = redir('p_2_1gc'),fw_caption_set('Yu\nWell...',palette.yu)
p_2_1gc = redir('p_2_1gd'),fw_caption_set('Come on, your sketches are always fantastic.',palette.player,prefix='player_name')
p_2_1gd = redir('p_2_1ge'),fw_caption_set('He concedes and cracks the sketchbook open, flipping through the pages until he stops on a stippled depiction of Jhin the Virtuoso.',palette.narration)
p_2_1ge = redir('p_2_1gg'),fw_caption_set('Lily\nWow.',palette.lily,2)
p_2_1gg = redir('p_2_1gf'),fw_caption_set('Rustam\nNoice.',palette.rustam,2)
p_2_1gf = redir('p_2_1gg'),fw_caption_set('Lily\nThat\'s amazing.',palette.lily,2)
p_2_1gh = redir('p_2_1gh2'),fw_caption_set('Lily\nDo you want to be my partner for business?',palette.lily)
p_2_1gh2 = redir('p_2_1gh3'),fw_caption_set('Yu\nUmm... why?',palette.yu)
p_2_1gh3 = redir('p_2_1gi'),fw_caption_set('Yu is visibly blushing.',palette.narration)
p_2_1gi = redir('p_2_1gj'),fw_caption_set('Lily\nMy entrepreneurship idea is for an art gallery,',palette.lily)
p_2_1gj = redir('p_2_1gk'),fw_caption_set('Lily\nAnd your work would be the perfect demo.',palette.lily)
p_2_1gk = redir('p_2_1gl'),fw_caption_set('Rustam\nWait what?',palette.rustam)
p_2_1gl = redir('p_2_1gm'),fw_caption_set('Rustam\nI thought we were pairing up.',palette.rustam)
p_2_1gm = redir('p_2_1gn'),fw_caption_set('Lily\nI was going to ask you, but you were busy playing League last night.',palette.lily)
p_2_1gn = redir('p_2_1go'),fw_caption_set('Rustam\nBut I\'m your love,',palette.rustam)
p_2_1go = redir('p_2_1gp'),fw_caption_set('Rustam\nRight?',palette.rustam)
p_2_1gp = redir('p_2_1gq'),fw_caption_set('Rustam makes smooching faces.',palette.narration)
p_2_1gq = redir('p_2_1gr'),fw_caption_set('Lily\nEw.',palette.lily)
p_2_1gr = redir('p_2_1gs'),fw_caption_set('Lily\nStop that.',palette.lily)
p_2_1gs = redir('p_2_1gt'),fw_caption_set('Rustam\nNevar!',palette.rustam)
p_2_1gt = redir('p_2_1gu'),fw_caption_set('Rustam\nYou know you love me!',palette.rustam),fw_timer_set(1.0,'p_2_1gu',False)
p_2_1gu = redir('p_2_1gv'),fw_caption_set('Yu\nI\'ll do it.',palette.yu,2),fw_meter_add(0.25)
p_2_1gv = redir('p_2_1gw'),fw_caption_set('Everyone turns to Yu.',palette.narration)
p_2_1gw = redir('p_2_1gx')
p_2_1gx = redir('p_2_1gy')
p_2_1gy = redir('p_2_1gz'),fw_caption_set('Rustam\nWhat?',palette.rustam)
p_2_1gz = redir('p_2_1ga2'),fw_caption_set('Lily\nWoohoo!',palette.lily)
p_2_1ga2 = redir('p_2_1gb2'),fw_caption_set('Rustam\nReally bruh?',palette.rustam)
p_2_1gb2 = redir('p_2_1gc2'),fw_caption_set('Well,',palette.player,prefix='player_name')
p_2_1gc2 = redir('p_2_2aa'),fw_caption_set('This is going to be interesting.',palette.player,prefix='player_name')

p_2_1ha = redir('p_2_1hb'),fw_caption_set('What even is there to do at so late at night?',palette.player,prefix='player_name')
p_2_1hb = redir('p_2_1hc'),fw_caption_set('Rustam\nPlay League?',palette.rustam)
p_2_1hc = redir('p_2_1hd'),fw_caption_set('Nevermind sleep, do you not get bored?',palette.player,prefix='player_name')
p_2_1hd = redir('p_2_1he'),fw_caption_set('Rustam\nNew champion hype.',palette.rustam)
p_2_1he = redir('p_2_1hf'),fw_caption_set('Rustam\nTwo of them this time.',palette.rustam)
p_2_1hf = redir('p_2_1hg'),fw_caption_set('Huh?',palette.player,prefix='player_name')
p_2_1hg = redir('p_2_1hh'),fw_caption_set('What is it now?',palette.player,prefix='player_name')
p_2_1hh = redir('p_2_1hi'),fw_caption_set('Rustam\nXayah and Rakan.',palette.rustam)
p_2_1hi = redir('p_2_1hj'),fw_caption_set('Rustam\nBirds.',palette.rustam)
p_2_1hj = redir('p_2_1hk'),fw_caption_set('Rustam\nLovers.',palette.rustam)
p_2_1hk = redir('p_2_1hl'),fw_caption_set('You glance at Yu\'s open sketchbook and see that he\'s already drawing them.',palette.narration)
p_2_1hl = redir('p_2_1hm'),fw_caption_set('Rustam\nEhe.',palette.rustam)
p_2_1hm = redir('p_2_1hn'),fw_caption_set('Rustam\nThey\'re real fun to play.',palette.rustam)
p_2_1hn = fw_branch_to(('Notify Yu','p_2_1ia')),fw_timer_set(5,'p_2_1ja')

p_2_1ia = redir('p_2_1ib'),fw_caption_set('Hey Yu.',palette.player,prefix='player_name')
p_2_1ib = redir('p_2_1ic')
p_2_1ic = redir('p_2_1id'),fw_caption_set('What\'re you drawing?',palette.player,prefix='player_name')
p_2_1id = redir('p_2_1ie'),fw_caption_set('Can we see?',palette.player,prefix='player_name')
p_2_1ie = redir('p_2_1if')
p_2_1if = redir('p_2_1ge')

p_2_1ja = redir('p_2_1jb'),fw_caption_set('Lily\nIt\'s some brilliant marketing Riot has.',palette.lily),fw_var_set('f_2_1j',0)
p_2_1jb = redir('p_2_1jc'),fw_caption_set('Lily\nMake animated shorts to get people excited,',palette.lily)
p_2_1jc = redir('p_2_1jd'),fw_caption_set('Lily\nRelease it,',palette.lily)
p_2_1jd = redir('p_2_1je'),fw_caption_set('Lily\nThen put it on the free rotation a couple of weeks later.',palette.lily)
p_2_1je = redir('p_2_1jf'),fw_caption_set('Lily\nBy the time people stop caring,',palette.lily)
p_2_1jf = redir('p_2_1jg'),fw_caption_set('Lily\nThey roll out another.',palette.lily)
p_2_1jg = redir('p_2_1jh'),fw_caption_set('Rustam\nIs that all League is to you?',palette.rustam)
p_2_1jh = redir('p_2_1ji'),fw_caption_set('Rustam\nA case study?',palette.rustam)
p_2_1ji = redir('p_2_1jj'),fw_caption_set('Lily\nA rather interesting one, I\'ll say that.',palette.lily)
p_2_1jj = redir('p_2_1jk')
p_2_1jk = redir('p_2_1jl'),fw_caption_set('So...',palette.player,prefix='player_name')
p_2_1jl = redir('p_2_1jm'),fw_caption_set('Who\'s your partner?',palette.player,prefix='player_name')
p_2_1jm = redir('p_2_1jn'),fw_caption_set('Rustam\nLily?',palette.rustam)
p_2_1jn = redir('p_2_1jo')
p_2_1jo = redir('p_2_1jp'),fw_caption_set('Lily\nYes.',palette.lily),fw_meter_add(-0.05)
p_2_1jp = redir('p_2_1jq'),fw_caption_set('And you, Yu?',palette.player,prefix='player_name')
p_2_1jq = redir('p_2_1jr')
p_2_1jr = redir('p_2_1js'),fw_caption_set('Yu\nI\'m with you I guess.',palette.yu),fw_meter_condition('>',0.5,fw_meter_add(-0.35),fw_meter_add(-0.15))
p_2_1js = redir('p_2_1jt')
p_2_1jt = redir('p_2_2aa'),fw_caption_set('Lily\nYou should probably head home now.',palette.lily)

# ------------------------------------------------------------------------------------------------------------------------------------------------------
# Part 2, scene 2: at home

p_2_2aa = redir('p_2_2ab'),fw_caption_set('Later that day, as you\'re researching for your business project, you get two calls at once.',palette.narration)
p_2_2ab = redir('p_2_2ac'),fw_caption_set('From Yu and Rustam.',palette.narration)
p_2_2ac = fw_branch_to(('Yu','p_2_2ba'),('Rustam','p_2_2ca')),fw_timer_set(15,'p_2_2da')

p_2_2ba = redir('p_2_2bb'),fw_caption_set('Hey Yu.',palette.player,prefix='player_name')
p_2_2bb = redir('p_2_2bc'),fw_caption_set('Yu\nHiya.',palette.yu)
p_2_2bc = redir('p_2_2bd')
p_2_2bd = redir(fw_var_branch('f_1_2a',('p_2_2ga',fw_var_branch('f_2_1j',('p_2_2ea','p_2_2fa'))))),fw_caption_set('Any particular reason for calling?',palette.player,prefix='player_name')

p_2_2ca = redir('p_2_2cb'),fw_caption_set('Ayy, you\'re not playing League for once.',palette.player,prefix='player_name')
p_2_2cb = redir('p_2_2cc'),fw_caption_set('Rustam\nYeah, I was going to invite you.',palette.rustam)
p_2_2cc = redir('p_2_2cd'),fw_caption_set('I don\'t even have League.',palette.player,prefix='player_name')
p_2_2cd = redir('p_2_2ce'),fw_caption_set('Rustam\nI can wait for you to install it.',palette.rustam)
p_2_2ce = fw_branch_to(('Accept','p_2_2ha'),('Decline',fw_var_branch('f_2_1j',('p_2_2ia','p_2_2ja'))))

p_2_2da = redir('p_2_2db'),fw_caption_set('They can wait.',palette.narration)
p_2_2db = redir('p_2_2dc'),fw_caption_set('Rustam might be harassing Lily again,',palette.narration)
p_2_2dc = redir('p_3_1aa'),fw_caption_set('But it\'s not my problem.',palette.narration)

p_2_2ea = redir('p_2_2eb'),fw_caption_set('Yu\nNo. I just like to idle on call. That okay?',palette.yu)
p_2_2eb = redir('p_2_2ec'),fw_caption_set('Not even business?',palette.player,prefix='player_name')
p_2_2ec = redir('p_2_2ed'),fw_caption_set('Yu\nIt\'s going good.',palette.yu)
p_2_2ed = redir('p_2_2ee'),fw_caption_set('Yu\nLily works really fast.',palette.yu)
p_2_2ee = redir('p_2_2ef'),fw_caption_set('She\'s probably just euphoric from getting to work with you.',palette.player,prefix='player_name')
p_2_2ef = redir('p_2_2eg'),fw_caption_set('Yu\nHeh.',palette.yu),fw_meter_add(0.05)
p_2_2eg = redir('p_3_1aa'),fw_caption_set('Yu\nMaybe.',palette.yu)

p_2_2fa = redir('p_2_2fb'),fw_caption_set('Yu\nOur business project.',palette.yu)
p_2_2fb = redir('p_2_2fc'),fw_caption_set('Right.',palette.player,prefix='player_name')
p_2_2fc = redir('p_2_2fd'),fw_caption_set('Yu\nLet\'s get started.',palette.yu)
p_2_2fd = redir('p_2_2fe'),fw_caption_set('It\'s obvious Yu misses Lily.',palette.narration),fw_meter_add(-0.05)
p_2_2fe = redir('p_2_2ff'),fw_caption_set('He brings her up occasionaly,',palette.narration)
p_2_2ff = redir('p_2_2fg'),fw_caption_set('But by the end of the hour of work,',palette.narration)
p_2_2fg = redir('p_3_1aa'),fw_caption_set('He\'s forgotten about her.',palette.narration)

p_2_2ga = redir('p_2_2gb'),fw_caption_set('Yu\nI finished the drawing.',palette.yu),fw_var_set('f_2_2g',0)
p_2_2gb = redir('p_2_2gc'),fw_caption_set('The lilium?',palette.player,prefix='player_name')
p_2_2gc = redir('p_2_2gd'),fw_caption_set('Yu\nYeah.',palette.yu)
p_2_2gd = redir('p_2_2ge'),fw_caption_set('Yu\nSo I want to try commissioned art now.',palette.yu)
p_2_2ge = redir('p_2_2gf'),fw_caption_set('You\'re asking if I want anything drawn?',palette.player,prefix='player_name')
p_2_2gf = redir('p_2_2gg'),fw_caption_set('Yu\nMhm.',palette.yu)
p_2_2gg = redir('p_2_2gh')
p_2_2gh = redir('p_2_2gi'),fw_caption_set('Why don\'t you draw Lily?',palette.player,prefix='player_name')
p_2_2gi = redir('p_2_2gj'),fw_caption_set('Not a lilium,',palette.player,prefix='player_name')
p_2_2gj = redir('p_2_2gk'),fw_caption_set('Lily.',palette.player,2,prefix='player_name')
p_2_2gk = redir('p_2_2gl'),fw_meter_add(0.05)
p_2_2gl = redir('p_2_2gm'),fw_caption_set('Yu\nThanks for the excuse.',palette.yu)
p_2_2gm = redir('p_2_2gn'),fw_caption_set('You need an excuse?',palette.player,prefix='player_name')
p_2_2gn = redir('p_2_2go'),fw_caption_set('Yu\nKind of awkward drawing your friend,',palette.yu)
p_2_2go = redir('p_2_2gp'),fw_caption_set('Yu\nSo yes.',palette.yu)
p_2_2gp = redir('p_2_2gq'),fw_caption_set('Well,',palette.player,prefix='player_name')
p_2_2gq = redir('p_2_2gr'),fw_caption_set('Be sure to share it when you\'re done,',palette.player,prefix='player_name')
p_2_2gr = redir('p_3_1aa'),fw_caption_set('Alright?',palette.player,prefix='player_name')

p_2_2ha = redir('p_2_2hb'),fw_caption_set('One game won\'t hurt.',palette.player,prefix='player_name')
p_2_2hb = redir('p_2_2hc'),fw_caption_set('This should keep him off Lily for a while.',palette.narration)
p_2_2hc = redir('p_2_2hd'),fw_caption_set('Maybe she\'ll get annoyed and break up.',palette.narration)
p_2_2hd = redir('p_3_1aa'),fw_caption_set('It\'ll give Yu an opportunity to approach Lily anyways.',palette.narration),fw_meter_add(0.05)

p_2_2ia = redir('p_2_2ib'),fw_caption_set('Nah mate, I\'m busy.',palette.player,prefix='player_name')
p_2_2ib = redir('p_2_2ic'),fw_caption_set('Rustam\nI\'ll go bug Lily then.',palette.rustam)
p_2_2ic = redir('p_2_2id'),fw_caption_set('You have a business project to do.',palette.player,prefix='player_name')
p_2_2id = redir('p_2_2ie'),fw_caption_set('Rustam\nOh, did you think we\'d be working?',palette.rustam)
p_2_2ie = redir('p_2_2if'),fw_caption_set('Ugh, of course not.',palette.player,prefix='player_name')
p_2_2if = redir('p_3_1aa'),fw_caption_set('He hangs up.',palette.narration),fw_meter_add(-0.05)

p_2_2ja = redir('p_2_2jb'),fw_caption_set('Shouldn\'t we be doing our business project?',palette.player,prefix='player_name')
p_2_2jb = redir('p_2_2jc'),fw_caption_set('Rustam\nI wanted to have some fun first.',palette.rustam)
p_2_2jc = redir('p_2_2jd'),fw_caption_set('Rustam\nBut I guess we need to get started at some point, right?',palette.rustam)
p_2_2jd = redir('p_2_2je'),fw_caption_set('Wow, you\'re taking initiative?',palette.player,prefix='player_name')
p_2_2je = redir('p_2_2jf'),fw_caption_set('Rustam\nI\'ll only be starting it.',palette.rustam)
p_2_2jf = redir('p_2_2jg'),fw_caption_set('Rustam\nYou do the rest.',palette.rustam)
p_2_2jg = redir('p_2_2jh'),fw_caption_set('Of course.',palette.player,prefix='player_name')
p_2_2jh = redir('p_3_1aa'),fw_caption_set('At least this will give Yu and Lily some uninterrupted time together.',palette.narration),fw_meter_add(0.05)

# ------------------------------------------------------------------------------------------------------------------------------------------------------
# Part 3, scene 1: after school

p_3_1aa = redir(fw_meter_condition('>',0.7,fw_meter_condition('>=',0.9,'p_3_1ba','p_3_1ca'),'p_3_1da')),fw_caption_set('After school the next day.',palette.narration)

p_3_1ba = redir('p_3_1bb')
p_3_1bb = redir('p_3_1bc'),fw_caption_set('Lily\nHey Yu!',palette.lily)
p_3_1bc = redir('p_3_1bd'),fw_caption_set('Lily\nWait for me!',palette.lily)
p_3_1bd = redir('p_3_1be'),fw_caption_set('Yu\nHm?',palette.yu)
p_3_1be = redir('p_3_1bf'),fw_caption_set('Lily\nSo, about our business project...',palette.lily)
p_3_1bf = redir('p_3_1bg'),fw_caption_set('Rustam\nHey Yu.',palette.rustam)
p_3_1bg = redir('p_3_1bh'),fw_caption_set('Rustam\nYou partnered with mah bae?',palette.rustam)
p_3_1bh = redir('p_3_1bi'),fw_caption_set('Yu\nYeah?',palette.yu)
p_3_1bi = redir('p_3_1bj'),fw_caption_set('Rustam\nWhy do you always draw girls?',palette.rustam)
p_3_1bj = redir('p_3_1bk'),fw_caption_set('Rustam\nIt\'s because you can\'t get a real girlfriend, isn\'t it?',palette.rustam)
p_3_1bk = redir('p_3_1bl'),fw_caption_set('Rustam\nWho would ever kiss you?',palette.rustam)
p_3_1bl = redir('p_3_1bm'),fw_caption_set('Lily\nMe.',palette.lily)
p_3_1bm = redir('p_3_1bn'),fw_caption_set('Lily kisses Yu as Rustam stares in shock.',palette.narration),fw_meter_add(0.05)
p_3_1bn = redir('p_3_1bo'),fw_caption_set('Lily\nYou know,',palette.lily)
p_3_1bo = redir('p_3_1bp'),fw_caption_set('Lily\nI really like you.',palette.lily)
p_3_1bp = redir('p_3_1bq'),fw_caption_set('Yu\nMe too.',palette.yu)
p_3_1bq = redir('p_3_1br'),fw_caption_set('Rustam is still in shock.',palette.narration)
p_3_1br = redir('p_4_1aa'),fw_caption_set('Yu and Lily continue dating through the following months.',palette.narration)

p_3_1ca = redir('p_3_1cb'),fw_caption_set('Yu\nWhy don\'t we walk home together?',palette.yu)
p_3_1cb = redir('p_3_1cc'),fw_caption_set('Lily\nHuh?',palette.lily)
p_3_1cc = redir('p_3_1cd'),fw_caption_set('Yu\nIt gives us a chance to talk about our business project.',palette.yu)
p_3_1cd = redir('p_3_1ce'),fw_caption_set('Lily\nOh sure.',palette.lily),fw_meter_add(0.05)
p_3_1ce = redir('p_3_1cf'),fw_caption_set('Rustam\nWhat about me?',palette.rustam)
p_3_1cf = redir('p_3_1cg'),fw_caption_set('Lily\nTag along if you want.',palette.lily)
p_3_1cg = redir('p_3_1ch')
p_3_1ch = redir('p_3_1ci'),fw_caption_set('Rustam\nOkay then.',palette.rustam)
p_3_1ci = redir('p_4_1aa'),fw_caption_set('Yu and Lily remain best friends, but never progress to romance.',palette.narration)

p_3_1da = redir('p_3_1db'),fw_caption_set('Rustam\nLily?',palette.rustam)
p_3_1db = redir('p_3_1dc')
p_3_1dc = redir('p_3_1dd'),fw_caption_set('Lily\nBye Yu.',palette.lily)
p_3_1dd = redir('p_4_1aa'),fw_caption_set('Yu\nBye Lily.',palette.yu)

# ------------------------------------------------------------------------------------------------------------------------------------------------------
# Part 4, scene 1: at lunch, talking to Lily

p_4_1aa = redir('p_4_1ab'),fw_caption_set('A few days before university applications close.',palette.narration)
p_4_1ab = redir('p_4_1ac'),fw_caption_set('Hi Lily.',palette.player,prefix='player_name')
p_4_1ac = redir('p_4_1ad'),fw_caption_set('Lily\nHey.',palette.lily)
p_4_1ad = redir('p_4_1ae'),fw_caption_set('A few more days until university applications close.',palette.player,prefix='player_name')
p_4_1ae = redir('p_4_1af'),fw_caption_set('Lily\nWhy do they have to all be at the same time?',palette.lily)
p_4_1af = redir('p_4_1ag'),fw_caption_set('I guess they want to force you to choose.',palette.player,prefix='player_name')
p_4_1ag = redir('p_4_1ah'),fw_caption_set('Lily\nI...',palette.lily)
p_4_1ah = redir('p_4_1ai'),fw_caption_set('Lily\nStill don\'t know where I\'ll be going.',palette.lily)
p_4_1ai = redir('p_4_1aj'),fw_caption_set('No idea?',palette.player,prefix='player_name')
p_4_1aj = redir('p_4_1ak'),fw_caption_set('Lily\nWell,',palette.lily)
p_4_1ak = redir('p_4_1al'),fw_caption_set('Lily\nI\'m pretty sure I\'ll be going to UWaterloo.',palette.lily)
p_4_1al = redir(fw_meter_condition('>',0.6,'p_4_1ba','p_4_1ca')),fw_caption_set('Lily\nThey have a very promising business program.',palette.lily)

p_4_1ba = redir('p_4_1bb'),fw_caption_set('Yu said he\'s going to U of T.',palette.player,prefix='player_name')#smoothen
p_4_1bb = redir('p_4_1bc'),fw_caption_set('Lily\nOh?',palette.lily)
p_4_1bc = redir('p_4_1bd'),fw_caption_set('Lily\nWell,',palette.lily)
p_4_1bd = redir('p_4_1be'),fw_caption_set('Lily\nI won\'t sacrifice my career to be with my friend.',palette.lily)
p_4_1be = redir('p_4_2aa'),fw_caption_set('Fair enough.',palette.player,prefix='player_name')

p_4_1ca = redir('p_4_1cb'),fw_caption_set('Yu\'s going to UWaterloo too.',palette.player,prefix='player_name')
p_4_1cb = redir('p_4_1cc'),fw_caption_set('Lily\nWell,',palette.lily)
p_4_1cc = redir('p_4_2aa'),fw_caption_set('Lily\nIsn\'t that convenient?',palette.lily)

# ------------------------------------------------------------------------------------------------------------------------------------------------------
# Part 4, scene 2: at lunch, talking to Yu

p_4_2aa = redir('p_4_2ab'),fw_caption_set('Yu\nHoi!',palette.yu)
p_4_2ab = redir('p_4_2ac'),fw_caption_set('Hi Yu.',palette.player,prefix='player_name')
p_4_2ac = redir('p_4_2ad'),fw_caption_set('Have you been here this whole time?',palette.player,prefix='player_name')
p_4_2ad = redir('p_4_2ae'),fw_caption_set('Yu\nYeah.',palette.yu)
p_4_2ae = redir('p_4_2af'),fw_caption_set('Yu\nWhy, is that a problem?',palette.yu)
p_4_2af = redir('p_4_2ag'),fw_caption_set('Of course not.',palette.player,prefix='player_name')
p_4_2ag = redir('p_4_2ah'),fw_caption_set('You hang out wherever you want.',palette.player,prefix='player_name')
p_4_2ah = fw_branch_to(('Art',fw_var_branch('f_2_2g',('p_4_2ba','p_4_2ca'))),('University','p_4_2da','f2'))

p_4_2ba = redir('p_4_2bb'),fw_caption_set('Did you finish the painting?',palette.player,prefix='player_name')
p_4_2bb = redir('p_4_2bc'),fw_caption_set('The one of Lily, I mean.',palette.player,prefix='player_name')
p_4_2bc = redir('p_4_2bd'),fw_caption_set('Yu\nActually, yes.',palette.yu)
p_4_2bd = redir('p_4_2be'),fw_caption_set('And Lily doesn\'t know?',palette.player,prefix='player_name')
p_4_2be = redir('p_4_2bf'),fw_caption_set('Yu\nYup.',palette.yu)
p_4_2bf = redir('p_4_2bg'),fw_caption_set('Post it on your blog or something.',palette.player,prefix='player_name')
p_4_2bg = redir('p_4_2bh'),fw_caption_set('Yu\nWill she see it?',palette.yu)
p_4_2bh = redir('p_4_2bi'),fw_caption_set('At some point, maybe.',palette.player,prefix='player_name')
p_4_2bi = redir('p_4_2bj'),fw_caption_set('In any case, you shouldn\'t let that stop you.',palette.player,prefix='player_name')
p_4_2bj = redir('p_4_2bk'),fw_caption_set('Yu\nAlright.',palette.yu)
p_4_2bk = redir('p_end_aa'),fw_caption_set('Yu\nI\'ll do it later today.',palette.yu)

p_4_2ca = redir('p_4_2cb'),fw_caption_set('How\'s your art going?',palette.player,prefix='player_name')
p_4_2cb = redir('p_4_2cc'),fw_caption_set('Yu\nJust finished a painting of Xayah and Rakan.',palette.yu)
p_4_2cc = redir('p_4_2cd'),fw_caption_set('Oh, cool.',palette.player,prefix='player_name')
p_4_2cd = redir('p_4_2ce'),fw_caption_set('Yu\nThe school wants to steal it for their art gallery.',palette.yu)
p_4_2ce = redir('p_4_2cf'),fw_caption_set('Yu\nShould I let them?',palette.yu)
p_4_2cf = fw_branch_to(('Yes','p_4_2ea'),('No','p_4_2fa'))

p_4_2da = redir('p_4_2db'),fw_caption_set('Listen.',palette.player,prefix='player_name')
p_4_2db = redir('p_4_2dc'),fw_caption_set('Lily\'s going to go to U of T.',palette.player,prefix='player_name')
p_4_2dc = redir('p_4_2dd'),fw_caption_set('Disregard what she\'s saying.',palette.player,prefix='player_name')
p_4_2dd = redir('p_4_2de'),fw_caption_set('If you want to be with her,',palette.player,prefix='player_name')
p_4_2de = redir('p_4_2df'),fw_caption_set('You go to U of T too.',palette.player,prefix='player_name')
p_4_2df = redir('p_4_2dg'),fw_caption_set('Yu\nYou a time traveller or something like that?',palette.yu)
p_4_2dg = redir(fw_meter_condition('>',0.5,'p_end_ba','p_end_da')),fw_caption_set('I\'ll go with "something like that".',palette.player,prefix='player_name')

p_4_2ea = redir('p_4_2eb'),fw_caption_set('Yeah.',palette.player,prefix='player_name')
p_4_2eb = redir('p_4_2ec'),fw_caption_set('It\'s not like they\'ll claim it as their own.',palette.player,prefix='player_name')
p_4_2ec = redir('p_4_2ed'),fw_caption_set('More people will see it.',palette.player,prefix='player_name')
p_4_2ed = redir('p_end_ca'),fw_caption_set('Works for you too.',palette.player,prefix='player_name')

p_4_2fa = redir('p_4_2fb'),fw_caption_set('No.',palette.player,prefix='player_name')
p_4_2fb = redir('p_4_2fc'),fw_caption_set('It\'s your work.',palette.player,prefix='player_name')
p_4_2fc = redir('p_end_ca'),fw_caption_set('Share it in a way that gets you credit.',palette.player,prefix='player_name')

# ------------------------------------------------------------------------------------------------------------------------------------------------------
# Endings

p_end_aa = redir('p_end_aa2'),fw_caption_set('Yu published the painting for all to see.',palette.narration)
p_end_aa2 = redir('p_end_ab'),fw_caption_set('Lily was ecstatic when she saw it.',palette.narration)
p_end_ab = redir('p_end_ac'),fw_caption_set('They would be together right now,',palette.narration)
p_end_ac = redir('p_end_ad'),fw_caption_set('except they went to different universities.',palette.narration)
p_end_ad = redir('p_end_ae'),fw_caption_set('Lily went to University of Toronto,',palette.narration)
p_end_ae = redir('p_end_af'),fw_caption_set('And Yu went to University of Waterloo.',palette.narration)
p_end_af = redir('p_end_ag'),fw_caption_set('They won\'t meet again,',palette.narration)
p_end_ag = redir('p_end_ah'),fw_caption_set('Until that day,',palette.narration)
p_end_ah = redir('p_end_ai'),fw_caption_set('At the Toronto Axolotl Gallery.',palette.narration)
p_end_ai = fw_ending(1)

p_end_ba = redir('p_end_bb'),fw_caption_set('Yu and Lily both went to University of Toronto.',palette.narration)
p_end_bb = redir('p_end_bc'),fw_caption_set('They lived those 4 years of their lives together,',palette.narration)
p_end_bc = redir('p_end_bd'),fw_caption_set('And married soon after getting their baccalaureates.',palette.narration)
p_end_bd = fw_ending(2)

p_end_ca = redir('p_end_cb'),fw_caption_set('Lily never confessed her love to Yu,',palette.narration)
p_end_cb = redir('p_end_cc'),fw_caption_set('And Yu never confessed his love to Lily,',palette.narration)
p_end_cc = redir('p_end_cd'),fw_caption_set('Because they went to different universities.',palette.narration)
p_end_cd = redir('p_end_ce'),fw_caption_set('Yu went to University of Waterloo,',palette.narration)
p_end_ce = redir('p_end_cf'),fw_caption_set('And Lily went to University of Toronto.',palette.narration)
p_end_cf = redir('p_end_cg'),fw_caption_set('They\'re apart enough now,',palette.narration)
p_end_cg = redir('p_end_ch'),fw_caption_set('That when they meet again,',palette.narration)
p_end_ch = redir('p_end_ci'),fw_caption_set('At the Toronto Axolotl gallery',palette.narration)
p_end_ci = fw_ending(3)

p_end_da = None

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
