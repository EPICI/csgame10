# csgame10
Async by Rudy Li and Faith Lum. For (Mr.Cope's) ICS2O1 summative project.
See header in *main.py* for more info.

*main.py* redirects to *engine.jar*, so you can run either and it will start the game.

Jython 3.5 is not stable and therefore unfit for use. We are using Jython 2.7 with all `from __future__ import`s. This allows for easier rendering stuff. Java handles the low level graphics stuff, Python does all the fun stuff.

Rendering Issues
---
Sometimes you will see flashes of the wrong colour. Don't panic. That's just a side effect of multithreading.