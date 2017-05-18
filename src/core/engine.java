package core;

import java.util.*;
import java.util.concurrent.*;
import java.io.*;
import java.nio.file.Files;
import java.awt.*;
import java.awt.event.*;
import java.awt.image.*;
import java.beans.PropertyChangeListener;
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
 * @version 1.2
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
	public static Graphics2D _dummy_graphics = blankimage(1,1).createGraphics();
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
	 * Color currently in use
	 */
	public static Color _color;
	/**
	 * All listeners
	 */
	public static HashMap<Object,Object> _listeners = new HashMap<>();
	/**
	 * Mouse position
	 */
	public static double[] _mousepos = new double[2];
	/**
	 * Log file name
	 */
	public static String _log = "log_"+Long.toHexString(System.nanoTime()*0x98119ad03b64eb09L)+".txt";
	/**
	 * The original print streams
	 */
	public static PrintStream _stdout,_stderr;
	/**
	 * Whether to print debug output
	 */
	public static boolean _debug;

	/**
	 * The main method
	 * 
	 * @param args
	 */
	public static void main(String[] args) {
		String scriptName = "main.py";
		// Read command line arguments
		for(int i=0;i<args.length;){
			String arg = args[i++];
			switch(arg){
			case "-debug":{
				_debug=true;
				break;
			}
			case "-file":{
				scriptName = args[i++];
				break;
			}
			}
		}
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
		_canvas = blankimage(_width,_height);
		_canvas_graphics = _canvas.createGraphics();
		_color = _canvas_graphics.getColor();
		// Instantiate interpreter
		if(_debug)System.out.println("Starting Python interpreter");
		_interpreter = new PythonInterpreter();
		if(_debug)System.out.println("Python interpreter ready!");
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
				updatemousepos(event);
			}

			@Override
			public void mouseMoved(MouseEvent event) {
				updatemousepos(event);
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
		_panel.setFocusable(true);
		_panel.requestFocusInWindow();
		// Run header
		_interpreter.exec("from __future__ import absolute_import, division, generators, unicode_literals, print_function, nested_scopes, with_statement");
		_interpreter.exec("range=xrange\nint=long");
		_interpreter.exec("class layermatrix:\n\tdef __init__(self,layer=None):\n\t\tself.layer=getmatrix(-1) if layer is None else layer\n\tdef __enter__(self):\n\t\tpushmatrix(self.layer)\n\t\treturn getmatrix(-1)\n\tdef __exit__(self,*args):\n\t\tpopmatrix()\n\t\treturn False");
		_interpreter.set("_jython", new PyInteger(1));
		// Run script
		try{
			_interpreter.execfile(scriptName);
		}catch(Exception e){
			e.printStackTrace();
		}
		die();
	}
	
	/**
	 * Murder the program
	 */
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
		if(!new File(_log).delete()){
			System.out.println("Unable to delete log file");
		}
		// Clean up frame
		_frame.dispose();
		// Clean up interpreter
		_interpreter.cleanup();
		_interpreter.close();
		// Exit
		System.exit(0);
	}
	
	/**
	 * Make a blank (0 alpha, black) image
	 * 
	 * @param width
	 * @param height
	 * @return
	 */
	public static BufferedImage blankimage(int width,int height){
		BufferedImage result = new BufferedImage(width,height,BufferedImage.TYPE_INT_ARGB);
		result.setRGB(0, 0, width, height, new int[width], 0, 0);
		return result;
	}
	
	/**
	 * Attempts to extract a pair
	 * 
	 * @param obj
	 * @return
	 */
	public static PyObject[] getpairfrom(PyObject obj,boolean asymmetric){
		return getgroupfrom(obj,asymmetric,2);
	}
	
	/**
	 * Attempts to extract a group
	 * 
	 * @param obj
	 * @param asymmetric
	 * @param count
	 * @return
	 */
	public static PyObject[] getgroupfrom(PyObject obj,boolean asymmetric,int count){
		PyObject[] result = new PyObject[count];
		if(asymmetric || obj.isSequenceType()){
			for(int i=0;i<count;i++)
				result[i] = obj.__getitem__(i);
		}else{
			for(int i=0;i<count;i++)
				result[i] = obj;
		}
		return result;
	}
	
	/**
	 * Updates mouse position
	 * <br>
	 * Meant for internal use
	 * 
	 * @param event
	 */
	public static void updatemousepos(MouseEvent event){
		double[] mpos = _mousepos;
		mpos[0] = event.getX()*(double)_width/_panel.getWidth();
		mpos[1] = _height-event.getY()*(double)_height/_panel.getHeight();
	}
	
	/**
	 * Get the current mouse position
	 * 
	 * @return
	 */
	public static PyObject mousepos(){
		return new PyTuple(new PyFloat(_mousepos[0]),new PyFloat(_mousepos[1]));
	}
	
	/**
	 * Add a mouse listener and add it to the map
	 * <br>
	 * Function will be called with type, xy, button number
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
				if(_debug)System.out.println("Mouse "+type+" at ("+event.getX()+","+event.getY()+")");
				function.__call__(new PyObject[]{type,mousepos(),new PyInteger(event.getButton())},new String[0]);
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
		if(_debug){
			MouseListener[] listeners = _panel.getMouseListeners();
			boolean found = false;
			for(MouseListener olistener:listeners){
				found = found || listener==olistener;
			}
			if(found)
				System.out.println("Mouse listener added");
			else
				throw new AssertionError("Mouse listener not added");
		}
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
				int key = event.getKeyCode();
				if(key==0)key = event.getKeyChar();
				if(_debug)System.out.println("Key "+type+": "+key);
				function.__call__(new PyObject[]{type,new PyInteger(key)},new String[0]);
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
		if(_debug){
			KeyListener[] listeners = _panel.getKeyListeners();
			boolean found = false;
			for(KeyListener olistener:listeners){
				found = found || listener==olistener;
			}
			if(found)
				System.out.println("Key listener added");
			else
				throw new AssertionError("Key listener not added");
		}
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
		_listeners.remove(key);
		if(listener instanceof MouseListener){
			_panel.removeMouseListener((MouseListener)listener);
		}else if(listener instanceof KeyListener){
			_panel.removeKeyListener((KeyListener)listener);
		}else{
			throw new AssertionError("listener ("+listener+") is neither a mouse listener nor a key listener");
		}
		return true;
	}
	
	/**
	 * Fills the current clip
	 */
	public static void fill(){
		_canvas_graphics.fillRect(0, 0, _width, _height);
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
	 * Sets the clip/mask as a polygon
	 * <br>
	 * Empty list will reset the clip
	 * 
	 * @param args
	 * @param keywords
	 * @return true if successful
	 */
	public static boolean setpolyclip(PyObject[] args,String[] keywords){
		int kwlen = keywords.length, alen = args.length-kwlen;
		if(kwlen!=0)throw new IllegalArgumentException("setpolyclip expected a sequence");
		if(alen==0){
			setclip(null);
			return true;
		}else if(alen==1){
			PyObject iter = args[0];
			if(iter.isSequenceType()){
				int n = iter.__len__();
				int[] xs = new int[n], ys = new int[n];
				for(int i=0;i<n;i++){
					PyObject group = iter.__getitem__(i);
					xs[i] = (int)Math.round(group.__getitem__(0).asDouble());
					ys[i] = _height-(int)Math.round(group.__getitem__(1).asDouble());
				}
				try{
					setclip(new Polygon(xs,ys,n));
					return true;
				}catch(Exception e){
					e.printStackTrace();
					return false;
				}
			}else if(Py.None.equals(iter)){
				setclip(null);
				return true;
			}else{
				throw new IllegalArgumentException("setpolyclip expected a sequence");
			}
		}else{
			int[] xs = new int[alen], ys = new int[alen];
			for(int i=0;i<alen;i++){
				PyObject group = args[i];
				xs[i] = (int)Math.round(group.__getitem__(0).asDouble());
				ys[i] = (int)Math.round(group.__getitem__(1).asDouble());
			}
			try{
				setclip(new Polygon(xs,ys,alen));
				return true;
			}catch(Exception e){
				e.printStackTrace();
				return false;
			}
		}
	}
	
	/**
	 * Loads an image from file
	 * 
	 * @param name filename or path
	 * @return image
	 */
	public static BufferedImage loadimage(String name) throws IOException {
		BufferedImage image = ImageIO.read(new File(name));
		int width = image.getWidth(), height = image.getHeight();
		BufferedImage result = blankimage(width,height);
		int[] array = new int[width*height];
		image.getRGB(0, 0, width, height, array, width*(height-1), -width);
		result.setRGB(0, 0, width, height, array, 0, width);
		return result;
	}
	
	/**
	 * Set the colour with RGB/HSV
	 * 
	 * @param args
	 * @param keywords
	 */
	public static PyObject setcolor(PyObject[] args,String[] keywords){
		int kwlen = keywords.length, alen = args.length-kwlen;
		if(alen!=0 || kwlen!=1)throw new IllegalArgumentException("setcolor expected a single keyword argument");
		String okey = keywords[0];
		String key = okey.toLowerCase();
		PyObject value = args[0];
		PyObject[] components = getgroupfrom(value,false,3);
		double a = components[0].asDouble(), b = components[1].asDouble(), c = components[2].asDouble();
		Color color;
		if("rgb".equals(key)){
			color = new Color((int)Math.round(a*255),(int)Math.round(b*255),(int)Math.round(c*255));
		}else if("hsv".equals(key) || "hsb".equals(key)){
			color = Color.getHSBColor((float)a,(float)b,(float)c);
		}else if("hsl".equals(key)){
			b*=c<0.5?c:1-c;
			color = Color.getHSBColor((float)a,(float)(2*b/(b+c)),(float)(b+c));
		}else{
			throw new IllegalArgumentException("type key ("+key+") not recognized");
		}
		_color=color;
		_canvas_graphics.setColor(color);
		return Py.java2py(color);
	}
	
	/**
	 * Change the font
	 * 
	 * @param name font name, null or empty for no change
	 * @param style style bitmask, -1 for no change
	 * @param size size, -1 for no change
	 */
	public static void setfont(String name,int style,int size){
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
		String text = obj.__str__().asString();
		FontMetrics fm = _dummy_graphics.getFontMetrics(_font);
		int width = fm.stringWidth(text), height = fm.getHeight();
		BufferedImage image = blankimage(width,height);
		Graphics2D g = image.createGraphics();
		g.setFont(_font);
		g.setColor(_color);
		g.scale(1, -1);
		g.drawString(text, 0, fm.getAscent()-height);
		g.dispose();
		return image;
	}
	
	/**
	 * Alphas an image and returns the result
	 * 
	 * @param image the original image
	 * @param multiply value to multiply by (constrains)
	 * @return alpha'd image
	 */
	public static BufferedImage alpha(BufferedImage image,double multiply){
		int x = image.getWidth(), y = image.getHeight();
		BufferedImage result = blankimage(x,y);
		for(int i=0;i<x;i++){
			for(int j=0;j<y;j++){
				int oc = image.getRGB(i, j);
				int alpha = (int)Math.round((oc>>>24)*multiply);
				if(alpha>255)alpha=255;
				if(alpha<0)alpha=0;
				int nc = (oc&0xffffff)|(alpha<<24);
				result.setRGB(i, j, nc);
			}
		}
		return result;
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
			getmatrix(-1).preConcatenate(AffineTransform.getShearInstance(sx, sy));
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
			AffineTransform at = getmatrix(-1);
			double[] mat = new double[6];
			at.getMatrix(mat);
			mat[0]*=sx;mat[1]*=sx;
			mat[2]*=sy;mat[3]*=sy;
			at.setTransform(new AffineTransform(mat));
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
			}
		}else{
			if(dc){
				angle = Math.toRadians(angle);
			}else{
				throw new IllegalArgumentException("rotate key ("+okey+") must be either radians or degrees, neither matched");
			}
		}
		double sin = Math.sin(angle), cos = Math.cos(angle);
		AffineTransform at = getmatrix(-1);
		double[] mat = new double[6];
		at.getMatrix(mat);
		double t1 = mat[0], t2 = mat[2];
		mat[0] = cos*t1+sin*t2;
		mat[2] = cos*t2-sin*t1;
		t1 = mat[1];t2 = mat[3];
		mat[1] = cos*t1+sin*t2;
		mat[3] = cos*t2-sin*t1;
		at.setTransform(new AffineTransform(mat));
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
			AffineTransform at = getmatrix(-1);
			double[] mat = new double[6];
			at.getMatrix(mat);
			mat[4] = dx*mat[0]+dy*mat[2]+mat[4];
			mat[5] = dx*mat[1]+dy*mat[3]+mat[5];
			at.setTransform(new AffineTransform(mat));
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
				_panel.requestFocusInWindow();
				_canvas_graphics.dispose();
				_draw = _canvas;
				_canvas = blankimage(_width,_height);
				_canvas_graphics = _canvas.createGraphics();
				_panel.repaint();
				setclip(null);
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
