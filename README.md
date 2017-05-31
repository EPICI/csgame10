# csgame10
Contingency by Rudy Li and Faith Lum, 2017. For (Mr.Cope's) ICS2O1 summative project.
See header in `main.py` for more info.

`main.py` redirects to `engine.jar`. You should run `main.py`, but if it doesn't work (OS problems), run `engine.jar` directly.

Jython 3.5 is not stable and therefore unfit for use. We are using Jython 2.7 with all `from __future__ import`s plus a short header. This allows for easier rendering stuff. Java handles the low level graphics stuff, Python does all the fun stuff.

Events *require* concurrency, but nothing else needs it. However, Java's AWT and Swing libraries have multithreading behind the scenes, and to work, have to. There are various places where this is used, and the most common problem is that various operations with a wide range of costs are queued (to be non-blocking) rather than computed immediately. For example, the Python script may set the colour just before rendering, and the colour change may not register until after rendering. Then the image has the wrong colour. This is why we force a rerender every frame, since if we get unlucky, the first render, which then gets reused, has the wrong colour, wrong font, or some other problem. You will probably see some visual glitches, but the game usually fixes itself quickly.

All resources, including images, are in the same folder, because permissions. If they were in their own folders, access could be denied. The program always has permission to read and write to its own directory.