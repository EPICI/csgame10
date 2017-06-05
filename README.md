# csgame10
Contingency by Rudy Li and Faith Lum, 2017. For (Mr.Cope's) ICS2O1 summative project.

Run
=
Try `main.py` first. If it does not work, it is due to an OS related issue. Run `engine.jar` directly instead. This is guaranteed to start up the game, unless you don't have the Java runtime installed, in which case you should install it.'

No installation should be needed.

Documentation
=
Docstrings can be found in the Python source, with a brief description of what each section does and additional comments for clarification of specific code snippets.

Files
=
All files, except the Jython library, are in the same folder, because of permissions - the program is only allowed to (by default) access files in its own directory.

- `engine.jar` is the engine. It is written in Java and has code for rendering and other low level tasks. It is used by `main.py` and treated as a library.
- `jython-standalone-2.7.0.jar` is Jython 2.7.0, the Python implementation we are using to allow for an engine in Java.
- `main.py` is the game itself, and contains code exclusive to this game. This includes the story, visuals, and an extensive framework to handle events, character animations, particles, etc. Details for each section can be found in comments in the source.
- Anything that ends in `.png` is an image and is used for visuals.
