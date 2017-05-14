package core;

import java.util.*;
import java.util.concurrent.*;
import java.io.*;
import java.nio.file.Files;
import java.awt.*;
import java.awt.event.*;
import java.awt.image.*;
import java.awt.geom.*;
import javax.imageio.*;
import javax.swing.*;
import org.python.core.*;
import org.python.util.*;

/**
 * The main engine. Sets up Jython and executes main.py with the interpreter.
 * <br>
 * Python 3 is requested, but sadly Jython 3.5 is not ready for use. They
 * recommend Jython 2.7. To compensate, some fixes are executed before the script.
 * Obviously not all Python 3 will work, but some of the more standard stuff like
 * division and printing will be Python 3 style.
 * <br>
 * Extremely verbose low level stuff like rendering and event handling are written
 * here in Java. Everything else should be in Python.
 * 
 * @author Rudy Li
 * @version 1.0
 */
public class engine {
	
	/**
	 * The interpreter object
	 */
	public static PythonInterpreter _interpreter;
	/**
	 * The window
	 */
	public static JFrame _frame;
	/**
	 * The panel, which is actually an anonymous class with image drawing
	 */
	public static JPanel _panel;
	/**
	 * Dummy graphics used for stuff like font metrics
	 */
	public static Graphics2D _dummy_graphics = new BufferedImage(1,1,BufferedImage.TYPE_INT_ARGB).createGraphics();
	/**
	 * The canvas which gets drawn on
	 */
	public static BufferedImage _canvas;
	/**
	 * The graphics for the canvas
	 */
	public static Graphics2D _canvas_graphics;
	/**
	 * Gets pushed to at the end of a frame
	 */
	public static BufferedImage _draw;
	/**
	 * View width
	 */
	public static int _width = 1;
	/**
	 * View height
	 */
	public static int _height = 1;
	/**
	 * Frame delay: 1000/framerate because milliseconds
	 */
	public static double _frame_delay = 1;
	/**
	 * Used to track precise frame delay
	 */
	public static double _time = System.currentTimeMillis();
	/**
	 * Events list
	 */
	public static ConcurrentLinkedDeque<PyObject> _events = new ConcurrentLinkedDeque<>();
	/**
	 * Matrices, like Processing
	 */
	public static ArrayList<AffineTransform> _matrices = new ArrayList<>();
	/**
	 * Font currently in use
	 */
	public static Font _font = new Font("Arial",Font.PLAIN,16);
	/**
	 * All listeners
	 */
	public static HashMap<Object,Object> _listeners = new HashMap<>();
	/**
	 * Mouse position
	 */
	public static int[] _mousepos = new int[2];
	/**
	 * Log file name
	 */
	public static String _log = "log_"+Long.toHexString(System.nanoTime()*0x98119ad03b64eb09L)+".txt";
	/**
	 * The original print streams
	 */
	public static PrintStream _stdout,_stderr;

	/**
	 * The main method
	 * 
	 * @param args ignored
	 */
	public static void main(String[] args) {
		// Redirect stdout
		try{
			PrintStream ps = new PrintStream(_log);
			_stdout=System.out;
			_stderr=System.err;
			System.setOut(ps);
			System.setErr(ps);
			System.out.println("This is a log file. stdout and stderr are redirected here.");
			System.out.println("This file is deleted when the program exits normally, so the file sticking around after the program exits means something went wrong. It may not be a critical error but it is something");
			System.out.println("------------------------------------------------------------");
		}catch(IOException e){
			e.printStackTrace();
		}
		// Create blank image
		_canvas = new BufferedImage(_width,_height,BufferedImage.TYPE_INT_ARGB);
		_canvas_graphics = _canvas.createGraphics();
		// Instantiate interpreter
		_interpreter = new PythonInterpreter();
		// Setup window
		_panel = new JPanel(){
			public Dimension getPreferredSize(){
				return new Dimension(_width,_height);
			}
			public void paint(Graphics g){
				if(_draw!=null){
					int ix = getWidth(), iy = getHeight();
					g.drawImage(_draw, 0, 0, ix, iy, this);
				}
			}
		};
		_panel.addMouseMotionListener(new MouseMotionListener(){

			@Override
			public void mouseDragged(MouseEvent event) {
				_mousepos[0] = event.getX();
				_mousepos[1] = event.getY();
			}

			@Override
			public void mouseMoved(MouseEvent event) {
				_mousepos[0] = event.getX();
				_mousepos[1] = event.getY();
			}
			
		});
		_frame = new JFrame("");
		_frame.add(_panel);
		_frame.pack();
		_frame.setVisible(true);
		_frame.setDefaultCloseOperation(JFrame.DISPOSE_ON_CLOSE);
		_frame.addWindowListener(new WindowListener(){

			@Override
			public void windowActivated(WindowEvent arg0) {}

			@Override
			public void windowClosed(WindowEvent arg0) {
				die();
			}

			@Override
			public void windowClosing(WindowEvent arg0) {}

			@Override
			public void windowDeactivated(WindowEvent arg0) {}

			@Override
			public void windowDeiconified(WindowEvent arg0) {}

			@Override
			public void windowIconified(WindowEvent arg0) {}

			@Override
			public void windowOpened(WindowEvent arg0) {}
			
		});
		_frame.requestFocusInWindow();
		// Run header
		_interpreter.exec("from __future__ import absolute_import, division, generators, unicode_literals, print_function, nested_scopes, with_statement");
		_interpreter.exec("range=xrange\nint=long");
		_interpreter.exec("class layermatrix:\n\tdef __init__(self,layer=None):\n\t\tself.layer=layer\n\tdef __enter__(self):\n\t\treturn pushmatrix(self.layer)\n\tdef __exit__(self,*args):\n\t\tpopmatrix()\n\t\treturn False");
		_interpreter.set("_jython", new PyInteger(1));
		// Run script
		_interpreter.execfile("main.py");
		die();
	}
	
	public static void die(){
		// Signal closing in log
		System.out.println("------------------------------------------------------------");
		System.out.println("Closing");
		// Close print streams
		System.out.close();
		System.err.close();
		System.setOut(_stdout);
		System.setErr(_stderr);
		// Final garbage collection
		System.gc();
		// Delete log file
		if(!new File(_log).delete())System.out.println("Unable to delete log file");
		// Clean up frame
		_frame.dispose();
		// Clean up interpreter
		_interpreter.cleanup();
		_interpreter.close();
		// Exit
		System.exit(0);
	}
	
	/**
	 * Attempts to extract a pair
	 * 
	 * @param obj
	 * @return
	 */
	public static PyObject[] getpairfrom(PyObject obj,boolean asymmetric){
		if(asymmetric || obj.isSequenceType()){
			return new PyObject[]{obj.__getitem__(0),obj.__getitem__(1)};
		}else{
			return new PyObject[]{obj,obj};
		}
	}
	
	public static PyObject mousepos(){
		return new PyTuple(new PyInteger(_mousepos[0]),new PyInteger(_mousepos[1]));
	}
	
	/**
	 * Add a mouse listener and add it to the map
	 * <br>
	 * Function will be called with type, x, y
	 * 
	 * @param key used later to remove
	 * @param function function to call
	 * @return true if there was no mapping for the key
	 */
	public static boolean bindmouse(PyObject key,PyObject function){
		MouseListener listener = new MouseListener(){
			
			PyString CLICK = new PyString("click"),
					ENTER = new PyString("enter"),
					EXIT = new PyString("exit"),
					PRESS = new PyString("press"),
					RELEASE = new PyString("release");
			
			void call(MouseEvent event,PyString type){
				function.__call__(new PyObject[]{type,new PyInteger(event.getX()),new PyInteger(event.getY())},new String[0]);
			}

			@Override
			public void mouseClicked(MouseEvent event) {
				call(event,CLICK);
			}

			@Override
			public void mouseEntered(MouseEvent event) {
				call(event,ENTER);
			}

			@Override
			public void mouseExited(MouseEvent event) {
				call(event,EXIT);
			}

			@Override
			public void mousePressed(MouseEvent event) {
				call(event,PRESS);
			}

			@Override
			public void mouseReleased(MouseEvent event) {
				call(event,RELEASE);
			}
			
		};
		_panel.addMouseListener(listener);
		return _listeners.put(key, listener)==null;
	}
	
	/**
	 * Add a key press listener and add it to the map
	 * <br>
	 * Function will be called with type, key code
	 * 
	 * @param key used later to remove
	 * @param function function to call
	 * @return true if there was no mapping for the key
	 */
	public static boolean bindkey(PyObject key,PyObject function){
		KeyListener listener = new KeyListener(){
			
			PyString PRESS = new PyString("press"),
					RELEASE = new PyString("release"),
					TYPE = new PyString("type");
			
			void call(KeyEvent event,PyString type){
				function.__call__(new PyObject[]{type,new PyInteger(event.getKeyCode())},new String[0]);
			}

			@Override
			public void keyPressed(KeyEvent event) {
				call(event,PRESS);
			}

			@Override
			public void keyReleased(KeyEvent event) {
				call(event,RELEASE);
			}

			@Override
			public void keyTyped(KeyEvent event) {
				call(event,TYPE);
			}
			
		};
		_panel.addKeyListener(listener);
		return _listeners.put(key, listener)==null;
	}
	
	/**
	 * Unbinds a mouse or key listener
	 * 
	 * @param key key to use in lookup
	 * @return true if the key was found (guaranteed success)
	 */
	public static boolean unbind(PyObject key){
		Object listener = _listeners.get(key);
		if(listener==null)return false;
		if(listener instanceof MouseListener)
			_panel.removeMouseListener((MouseListener)listener);
		else if(listener instanceof KeyListener)
			_panel.removeKeyListener((KeyListener)listener);
		else
			throw new AssertionError("listener ("+listener+") is neither a mouse listener nor a key listener");
		return true;
	}
	
	/**
	 * Sets the clip/mask
	 * 
	 * @param clip a shape object
	 */
	public static void setclip(Shape clip){
		if(clip==null)
			_canvas_graphics.setClip(0,0,_width,_height);
		else
			_canvas_graphics.setClip(clip);
	}
	
	/**
	 * Loads an image from file
	 * 
	 * @param name filename or path
	 * @return image
	 */
	public static BufferedImage loadimage(String name) throws IOException {
		return ImageIO.read(new File(name));
	}
	
	/**
	 * Change the font
	 * 
	 * @param name font name, null or empty for no change
	 * @param style style bitmask, -1 for no change
	 * @param size size, -1 for no change
	 */
	public static void setFont(String name,int style,int size){
		_font = new Font(
				name==null||name.length()==0?_font.getFamily():name,
				style<0?_font.getStyle():style,
				size<0?_font.getSize():size
				);
	}
	
	/**
	 * Render the str() of an object, black
	 * 
	 * @param obj
	 * @return
	 */
	public static BufferedImage render(PyObject obj){
		return render(obj,Color.BLACK);
	}
	
	/**
	 * Render the str() of an object with the given color
	 * 
	 * @param obj
	 * @param color
	 * @return
	 */
	public static BufferedImage render(PyObject obj,Color color){
		String text = obj.__str__().asString();
		FontMetrics fm = _dummy_graphics.getFontMetrics(_font);
		int width = fm.stringWidth(text), height = fm.getHeight();
		BufferedImage image = new BufferedImage(width,height,BufferedImage.TYPE_INT_ARGB);
		Graphics2D g = image.createGraphics();
		g.setColor(color);
		g.setFont(_font);
		g.drawString(text, 0, fm.getAscent());
		g.dispose();
		return image;
	}
	
	/**
	 * Draw an image
	 * <br>
	 * First argument is the image, second is coordinates
	 * <br>
	 * Use keywords to specify alignment
	 * 
	 * @param args
	 * @param keywords
	 */
	public static void drawimage(PyObject[] args,String[] keywords){
		int kwlen = keywords.length, alen = args.length-kwlen;
		if(alen!=2)throw new IllegalArgumentException("drawimage expected 2 arguments, got "+alen);
		BufferedImage image = (BufferedImage)args[0].__tojava__(BufferedImage.class);
		PyObject[] xy = getpairfrom(args[1],true);
		double x = xy[0].asDouble(), y = xy[1].asDouble();
		PyObject xal = null, yal = null;
		for(int i=alen,j=0;j<kwlen;i++,j++){
			String key = keywords[j];
			PyObject value = args[i];
			switch(key.toLowerCase()){
			case "horizontal_alignment":
			case "horizontalalignment":
			case "horizontal_align":
			case "horizontalalign":
			case "horizontal":
			case "x_alignment":
			case "xalignment":
			case "x_align":
			case "xalign":
			case "x":xal=value;break;
			case "vertical_alignment":
			case "verticalalignment":
			case "vertical_align":
			case "verticalalign":
			case "vertical":
			case "y_alignment":
			case "yalignment":
			case "y_align":
			case "yalign":
			case "y":yal=value;break;
			case "both_alignment":
			case "bothalignment":
			case "both_align":
			case "bothalign":
			case "both":
			case "xy_alignment":
			case "xyalignment":
			case "xy_align":
			case "xyalign":
			case "xy":{
				PyObject[] pair = getpairfrom(value,true);
				xal = pair[0];
				yal = pair[1];
			}
			default:throw new IllegalArgumentException("alignment key ("+key+") not recognized");
			}
		}
		double xalign = 0.5, yalign = 0.5;
		if(xal!=null){
			xalign=xal.asDouble();
			if(!Double.isFinite(xalign))xalign=0.5;
		}
		if(yal!=null){
			yalign=yal.asDouble();
			if(!Double.isFinite(yalign))yalign=0.5;
		}
		x -= xalign*image.getWidth();
		y -= yalign*image.getHeight();
		AffineTransform at = new AffineTransform(getmatrix(-1));
		at.preConcatenate(new AffineTransform(new double[]{1d,0d,0d,-1d,x,_height-y}));
		_canvas_graphics.drawImage(image, at, _panel);
	}
	
	/**
	 * Apply a shear transform
	 * <br>
	 * To be clear, x is adding some constant times y and y is adding some constant times x
	 * 
	 * @param args
	 * @param keywords
	 */
	public static void shear(PyObject[] args,String[] keywords){
		int kwlen = keywords.length, alen = args.length-kwlen;
		PyObject xmult = null, ymult = null;
		if(alen!=0){
			if(alen==1){
				PyObject[] pair = getpairfrom(args[0],true);
				xmult = pair[0];
				ymult = pair[1];
			}else if(alen==2){
				xmult = args[0];
				ymult = args[1];
			}else{
				throw new IllegalArgumentException("shear expected at most 2 arguments, got "+alen);
			}
		}
		for(int i=alen,j=0;j<kwlen;i++,j++){
			String key = keywords[j];
			PyObject value = args[i];
			switch(key.toLowerCase()){
			case "horizontal":
			case "x_multiplier":
			case "xmultiplier":
			case "x_mult":
			case "xmult":
			case "xbyy":
			case "x_by_y":
			case "x":
			case "sx":xmult=value;break;
			case "vertical":
			case "y_multiplier":
			case "ymultiplier":
			case "y_mult":
			case "ymult":
			case "ybyx":
			case "y_by_x":
			case "y":
			case "sy":ymult=value;break;
			case "xy_multiplier":
			case "xymultiplier":
			case "xy_mult":
			case "xymult":
			case "xy":
			case "both":
			case "dxy":{
				PyObject[] pair = getpairfrom(value,true);
				xmult = pair[0];
				ymult = pair[1];
			}
			default:throw new IllegalArgumentException("shear key ("+key+") not recognized");
			}
		}
		if(xmult!=null || ymult!=null){
			double sx = 0, sy = 0;
			if(xmult!=null){
				sx = xmult.asDouble();
				if(!Double.isFinite(sx))sx=0;
			}
			if(ymult!=null){
				sy = ymult.asDouble();
				if(!Double.isFinite(sy))sy=0;
			}
			getmatrix(-1).shear(sx, sy);
		}
	}
	
	/**
	 * Apply a scale transform
	 * 
	 * @param args
	 * @param keywords
	 */
	public static void scale(PyObject[] args,String[] keywords){
		int kwlen = keywords.length, alen = args.length-kwlen;
		PyObject xmult = null, ymult = null;
		if(alen!=0){
			if(alen==1){
				PyObject[] pair = getpairfrom(args[0],false);
				xmult = pair[0];
				ymult = pair[1];
			}else if(alen==2){
				xmult = args[0];
				ymult = args[1];
			}else{
				throw new IllegalArgumentException("scale expected at most 2 arguments, got "+alen);
			}
		}
		for(int i=alen,j=0;j<kwlen;i++,j++){
			String key = keywords[j];
			PyObject value = args[i];
			switch(key.toLowerCase()){
			case "horizontal":
			case "x_multiplier":
			case "xmultiplier":
			case "x_mult":
			case "xmult":
			case "x":
			case "sx":xmult=value;break;
			case "vertical":
			case "y_multiplier":
			case "ymultiplier":
			case "y_mult":
			case "ymult":
			case "y":
			case "sy":ymult=value;break;
			case "xy_multiplier":
			case "xymultiplier":
			case "xy_mult":
			case "xymult":
			case "xy":
			case "both":
			case "sxy":{
				PyObject[] pair = getpairfrom(value,false);
				xmult = pair[0];
				ymult = pair[1];
			}
			default:throw new IllegalArgumentException("scale key ("+key+") not recognized");
			}
		}
		if(xmult!=null || ymult!=null){
			double sx = 1, sy = 1;
			if(xmult!=null){
				sx = xmult.asDouble();
				if(!Double.isFinite(sx))sx=1;
				if(Math.abs(sx)<1e-15)throw new IllegalArgumentException("zero or near zero x scale factor "+sx);
			}
			if(ymult!=null){
				sy = ymult.asDouble();
				if(!Double.isFinite(sy))sy=1;
				if(Math.abs(sy)<1e-15)throw new IllegalArgumentException("zero or near zero x scale factor "+sy);
			}
			getmatrix(-1).scale(sx, sy);
		}
	}
	
	/**
	 * Apply a rotate transform
	 * <br>
	 * Must use either "radians" or "degrees" keyword
	 * 
	 * @param args
	 * @param keywords
	 */
	public static void rotate(PyObject[] args,String[] keywords){
		int kwlen = keywords.length, alen = args.length-kwlen;
		if(alen!=0 || kwlen!=1)throw new IllegalArgumentException("rotate takes one keyword argument");
		String okey = keywords[0], key = okey.toLowerCase();
		PyObject value = args[0];
		double angle = value.asDouble();
		if(!Double.isFinite(angle))throw new IllegalArgumentException("rotate angle ("+angle+") must be finite");
		// Do contains check to be lenient
		boolean rc = "radians".contains(key), dc = "degrees".contains(key);
		if(rc){
			if(dc){
				throw new IllegalArgumentException("rotate key ("+okey+") must be either radians or degrees, both matched");
			}else{
				getmatrix(-1).rotate(angle);
			}
		}else{
			if(dc){
				getmatrix(-1).rotate(Math.toRadians(angle));
			}else{
				throw new IllegalArgumentException("rotate key ("+okey+") must be either radians or degrees, neither matched");
			}
		}
	}
	
	/**
	 * Apply a translate transformation
	 * 
	 * @param args
	 * @param keywords
	 */
	public static void translate(PyObject[] args,String[] keywords){
		int kwlen = keywords.length, alen = args.length-kwlen;
		PyObject xoffset = null, yoffset = null;
		if(alen!=0){
			if(alen==1){
				PyObject[] pair = getpairfrom(args[0],true);
				xoffset = pair[0];
				yoffset = pair[1];
			}else if(alen==2){
				xoffset = args[0];
				yoffset = args[1];
			}else{
				throw new IllegalArgumentException("translate expected at most 2 arguments, got "+alen);
			}
		}
		for(int i=alen,j=0;j<kwlen;i++,j++){
			String key = keywords[j];
			PyObject value = args[i];
			switch(key.toLowerCase()){
			case "right":
			case "horizontal":
			case "x_offset":
			case "xoffset":
			case "x":
			case "dx":xoffset=value;break;
			case "up":
			case "vertical":
			case "y_offset":
			case "yoffset":
			case "y":
			case "dy":yoffset=value;break;
			case "xy_offset":
			case "xyoffset":
			case "xy":
			case "both":
			case "dxy":{
				PyObject[] pair = getpairfrom(value,true);
				xoffset = pair[0];
				yoffset = pair[1];
			}
			default:throw new IllegalArgumentException("translate key ("+key+") not recognized");
			}
		}
		if(xoffset!=null || yoffset!=null){
			double dx = 0, dy = 0;
			if(xoffset!=null){
				dx = xoffset.asDouble();
				if(!Double.isFinite(dx))dx=0;
			}
			if(yoffset!=null){
				dy = yoffset.asDouble();
				if(!Double.isFinite(dy))dy=0;
			}
			getmatrix(-1).translate(dx, dy);
		}
	}
	
	/**
	 * Duplicates the top matrix
	 */
	public static void pushmatrix(){
		pushmatrix(getmatrix(-1));
	}
	
	/**
	 * Adds a copy of the given matrix to the stack
	 * <br>
	 * If null, will add the identity matrix
	 * 
	 * @param matrix transform matrix
	 */
	public static void pushmatrix(AffineTransform matrix){
		_matrices.add(matrix==null?new AffineTransform():new AffineTransform(matrix));
	}
	
	/**
	 * Removes the top matrix and returns it
	 * 
	 * @return transform matrix
	 */
	public static AffineTransform popmatrix(){
		return _matrices.remove(_matrices.size()-1);
	}
	
	/**
	 * Get matrix at index
	 * <br>
	 * Use negative to get from the end of the list
	 * 
	 * @param index index
	 * @return transform matrix
	 */
	public static AffineTransform getmatrix(int index){
		int n = _matrices.size();
		return _matrices.get(index+((index>>-1)&n));
	}
	
	/**
	 * Infinite iterator to use as the main loop
	 * 
	 * @return an iterable to be used for the main loop
	 */
	public static PyObject mainloop(){
		return new PyObject(){
			public PyObject __iter__(){
				return this;
			}
			public PyObject __iternext__(){
				_canvas_graphics.dispose();
				_draw = _canvas;
				_canvas = new BufferedImage(_width,_height,BufferedImage.TYPE_INT_ARGB);
				_canvas_graphics = _canvas.createGraphics();
				_panel.repaint();
				long now = System.currentTimeMillis();
				_time += _frame_delay;
				if(_time>now){
					long delay = (long)(_time-now)+1;
					try{
						Thread.sleep(delay);
					}catch(InterruptedException e){
						e.printStackTrace();
					}
				}else if(_time<now){//Lag fix
					_time=now;
				}
				while(!_events.isEmpty()){
					PyObject event = _events.pollFirst();
					event.__call__();
				}
				_matrices.clear();
				_matrices.add(new AffineTransform());
				return this;
			}
		};
	}
	
	/**
	 * Resize the window
	 * <br>
	 * Call with (x,y) tuple, x,y args, or preferably using keywords
	 * 
	 * @param args
	 * @param keywords
	 */
	public static void resize(PyObject[] args,String[] keywords){
		int kwlen = keywords.length, alen = args.length-kwlen;
		PyObject newWidth = null, newHeight = null;
		if(alen!=0){
			if(alen==1){
				PyObject[] pair = getpairfrom(args[0],true);
				newWidth = pair[0];
				newHeight = pair[1];
			}else if(alen==2){
				newWidth = args[0];
				newHeight = args[1];
			}else{
				throw new IllegalArgumentException("resize expected at most 2 arguments, got "+alen);
			}
		}
		for(int i=alen,j=0;j<kwlen;i++,j++){
			String key = keywords[j];
			PyObject value = args[i];
			switch(key.toLowerCase()){
			case "x":
			case "width":newWidth=value;break;
			case "y":
			case "height":newHeight=value;break;
			case "xy":
			case "both":
			case "dimensions":{
				PyObject[] pair = getpairfrom(value,true);
				newWidth = pair[0];
				newHeight = pair[1];
			}
			default:throw new IllegalArgumentException("resize key ("+key+") not recognized");
			}
		}
		if(newWidth!=null || newHeight!=null){
			if(newWidth!=null){
				int width = newWidth.asInt();
				if(width<=0)throw new IllegalArgumentException("width ("+width+") must be positive");
				_width = width;
			}
			if(newHeight!=null){
				int height = newHeight.asInt();
				if(height<=0)throw new IllegalArgumentException("height ("+height+") must be positive");
				_height = height;
			}
			_frame.pack();
		}
	}
	
	/**
	 * Set the new framerate
	 * <br>
	 * Call with keyword "delay" instead to set frame delay
	 * 
	 * @param args
	 * @param keywords
	 */
	public static void framerate(PyObject[] args,String[] keywords){
		int kwlen = keywords.length, alen = args.length-kwlen;
		if((alen+kwlen)!=1)throw new IllegalArgumentException("must either use positional or keyword argument");
		if(alen!=0){
			double rate = args[0].asDouble();
			if(!Double.isFinite(rate))throw new IllegalArgumentException("framerate ("+rate+") must be finite");
			if(rate<=0)throw new IllegalArgumentException("framerate ("+rate+") must be positive");
			_frame_delay = 1000d/rate;
		}else{
			String key = keywords[0];
			PyObject value = args[alen];
			double delay;
			switch(key.toLowerCase()){
			case "framedelay":
			case "frame_delay":
			case "delay":delay=value.asDouble();break;
			case "framerate":
			case "frame_rate":
			case "rate":delay=100d/value.asDouble();break;
			default:throw new IllegalArgumentException("'"+key+"' is an invalid keyword argument for this function");
			}
			if(!Double.isFinite(delay))throw new IllegalArgumentException("delay ("+delay+") must be finite");
			if(delay<=0)throw new IllegalArgumentException("delay ("+delay+") must be positive");
			_frame_delay = delay;
		}
	}

}