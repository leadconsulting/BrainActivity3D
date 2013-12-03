"""

Main file of the application

  * Read data from Emotiv
  * Compute 3D positions of activity sources
  * Plot them inside 3D model of the brain

"""

from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
from lib import objloader
from lib.epoc import Epoc
from lib.sourcelocalizer import SourceLocalizer
from OpenGL.GL.shaders import *
from threading import Thread
from cgkit.cgtypes import *
import traceback
import time

# Register global variables
brain = None
program = None
epoc = None
sample_sec = 5
localizer = None
source_locations = []
rotation_matrix = mat4(1.0)
prev_x = 0
prev_y = 0

screen_w = 800
screen_h = 600
zoom_factor = 1.0
# Drawing mode for fragment shader:
#   0 - simple color
#   1 - blinn model
#   2 - xray
p_shader_mode = 0



def initgl():
    """
    Initialize OpenGL and GLUT
    """

    global screen_w
    global screen_h
    global program
    global p_shader_mode

    
    # Initialize engine
    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_DEPTH | GLUT_SRGB)
    glutInitWindowSize(screen_w, screen_h)
    glutInitWindowPosition(200,50);
    glutCreateWindow('Brain Activity 3D')
   
    # Z-buffer
    glEnable(GL_DEPTH_TEST)

    # Enable basic lighting
    glEnable(GL_LIGHTING)

    # Add light sources
    glEnable(GL_LIGHT0)
    
    # Blending
    glClearColor(0.7, 0.7, 0.7, 1)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    
    # Initialize model
    init_model()

    # Initialize functions
    glutReshapeFunc(reshape)
    glutDisplayFunc(display)
    glutIdleFunc(idle)
    glutMouseFunc(mouse)
    glutMotionFunc(mouse_drag)
    glutKeyboardFunc(keyboard)
    glutSpecialFunc(keyboard)
    
    # Set up shaders
    with open("brain_vertex_shader.glsl") as vertex_shader, open("brain_fragment_shader.glsl") as fragment_shader:    
        program = compileProgram(
            compileShader(vertex_shader.read(), GL_VERTEX_SHADER),
            compileShader(fragment_shader.read(), GL_FRAGMENT_SHADER),
        )
    
    # Use shaders
    glUseProgram(program)
    p_shader_mode = glGetUniformLocation(program, 'shader_mode')
    if p_shader_mode in (None,-1):
        print 'Warning, no uniform: %s'%( 'shader_mode' )

    # Start main loop
    glutMainLoop()

def initepoc():
    global epoc
    epoc = Epoc(sample_sec)
    epoc_reader_thread = Thread(target=epoc.read_dummy_samples)
    epoc_reader_thread.start()

def initsourceloc():
    global localizer
    localizer = SourceLocalizer(epoc)
    source_localizer_thread = Thread(target=localize_sources)
    source_localizer_thread.start()

def reshape(w, h):
    """
    Process reshaping of the window
    """
    screen_w = w
    screen_h = h
    glViewport(0, 0, w, h)
    setProjectionMatrix(w,h)
    
def setProjectionMatrix (width, height):
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective (45.0, (3.0*width)/(4.0*height), 0.5, 500.0)
    glMatrixMode(GL_MODELVIEW)
    
def display():
    """
    Main drawing function
    """
    global screen_w
    global screen_h
    global brain
    global p_shader_mode
    
    # Clear screen
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);
    
    # Initialize view-transform matrix
    glLoadIdentity()

    # Light source 0
    glLightfv(GL_LIGHT0, GL_AMBIENT, [0, 0, 0, 1])
    glLightfv(GL_LIGHT0, GL_DIFFUSE, [1, 1, 1, 1])
    glLightfv(GL_LIGHT0, GL_SPECULAR, [1, 1, 1, 1])
    glLightfv(GL_LIGHT0, GL_POSITION, [0, 0, 1, 0])
    
    # Set up the camera    
    gluLookAt(0, 300, 0, 0, 0, 0, 0, 0, 1)
    
    # Draw things
    draw_background()
    glScale(zoom_factor, zoom_factor, zoom_factor)
    draw_sources()
    draw_electrodes()
    glDepthMask(False)
    draw_brain()
    glDepthMask(True)
    
    glEnable(GL_LIGHTING)
    # Switch buffers
    glutSwapBuffers()


def idle():
    """
    Computation to be performed during idle
    """
    display()

def mouse(button, state, x, y):
    """
    Process mouse events
    """
    global zoom_factor
    global screen_w
    global screen_h
    
    # Once we pressed the left button this corresponds to the start of the rotation
    global prev_x
    global prev_y
    
    if state == GLUT_DOWN and button == GLUT_LEFT_BUTTON:
        prev_x = x
        prev_y = y
    # MouseWheel
    if button == 3:
        if zoom_factor <= 20.0:
            zoom_factor += 0.05
    if button == 4 :
        if zoom_factor >= 0.1:
            zoom_factor -= 0.05
        
def mouse_drag(x, y):
    """
    Process mouse events
    """
    global prev_x   # Location where mouse was pressed
    global prev_y
    global rotation_matrix # Current rotation matrix
    
    dx = x - prev_x
    dy = y - prev_y
   
    # Compute an 'object vector' which is a corresponding axis in object's coordinates
    object_axis_vector = rotation_matrix.inverse()*vec3([0, 0, 1])
    rotation_matrix = rotation_matrix.rotate(360*3.14*dx/(screen_w * 180), object_axis_vector)

    object_axis_vector = rotation_matrix.inverse()*vec3([1, 0, 0])
    rotation_matrix = rotation_matrix.rotate(360*3.14*dy/(screen_h * 180), object_axis_vector)
    
    # Save current coordinates as old ones
    prev_x = x
    prev_y = y

def keyboard(key, x, y):
    """
    Process keyboard events
    """
    global rotation_matrix
    
    if key == GLUT_KEY_LEFT:
        # Compute an 'object vector' which is a corresponding axis in object's coordinates  
        object_axis_vector = rotation_matrix.inverse()*vec3([0, 0, 1])
        rotation_matrix = rotation_matrix.rotate(3.14/90, object_axis_vector)
    if key == GLUT_KEY_RIGHT:
        object_axis_vector = rotation_matrix.inverse()*vec3([0, 0, 1])
        rotation_matrix = rotation_matrix.rotate(-3.14/90, object_axis_vector)
    if key == GLUT_KEY_UP:
        object_axis_vector = rotation_matrix.inverse()*vec3([1, 0, 0])
        rotation_matrix = rotation_matrix.rotate(3.14/90, object_axis_vector)
    if key == GLUT_KEY_DOWN:
        object_axis_vector = rotation_matrix.inverse()*vec3([1, 0, 0])
        rotation_matrix = rotation_matrix.rotate(-3.14/90, object_axis_vector)
    elif key == chr(27):
        exit(0)

def init_model():
    """
    Load model from Wavefront .obj file
    """
    global brain
    brain = objloader.OBJ('brain_20k_colored_properly.obj', 'model', swapyz=False)

def main():
    """
    Build the main pipeline
    """
    initepoc()
    initsourceloc()
    initgl()

def draw_brain():

    global p_shader_mode
    glColor3f(0, 0, 0)
    
    # Material front   
    glMaterialfv(GL_FRONT, GL_AMBIENT, [0.2, 0.2, 0.2, 1])
    glMaterialfv(GL_FRONT, GL_DIFFUSE, [0.8, 0.8, 0.8, 1])
    glMaterialfv(GL_FRONT, GL_SPECULAR, [0, 0, 0, 1])
    glMaterialfv(GL_FRONT, GL_SHININESS, 0)
    glMaterialfv(GL_FRONT, GL_EMISSION, [0, 0, 0, 1])
    
    glPushMatrix()
    glUniform1i(p_shader_mode, 2) # xray

    try:
        glMultMatrixf(rotation_matrix.toList())
        glCallList(brain.gl_list)
    except:
        traceback.print_exc()
    finally:
        glPopMatrix()

def draw_electrodes():
    global p_shader_mode

    # Material front   
    glMaterialfv(GL_FRONT, GL_AMBIENT, [0.2, 0.2, 0.2, 1])
    glMaterialfv(GL_FRONT, GL_DIFFUSE, [0.4, 0.4, 0.9, 1])
    glMaterialfv(GL_FRONT, GL_SPECULAR, [0, 0, 0, 1])
    glMaterialfv(GL_FRONT, GL_SHININESS, 0)
    glMaterialfv(GL_FRONT, GL_EMISSION, [0, 0, 0, 1])

    glUniform1i(p_shader_mode, 1) # blinn
    
    glPushMatrix()
    glMultMatrixf(rotation_matrix.toList())
    
    for coordinate in epoc.coordinates:
        draw_electrode(coordinate[0], coordinate[1])
    
    glPopMatrix()

def draw_electrode(position, label):
    glColor3f(0.18, 0.31, 0.31)
    glPushMatrix()
    glTranslate(position[0],  position[1],  position[2])
    draw_label(label)
    glutSolidSphere(5, 20, 20)
    glPopMatrix()

def draw_label(text):
    global program 
    glUseProgram(0)
    glDisable(GL_LIGHTING)
    glRasterPos2f(0+2*zoom_factor, 3+2*zoom_factor)
    glutBitmapString(GLUT_BITMAP_HELVETICA_18, text)
    glEnable(GL_LIGHTING)
    glUseProgram(program)

def draw_source(position):    
    glMaterialfv(GL_FRONT, GL_AMBIENT, [0.2, 0.2, 0.2, 1])
    glMaterialfv(GL_FRONT, GL_DIFFUSE, [0.9, 0.3, 0.3, 1])
    glMaterialfv(GL_FRONT, GL_SPECULAR, [0, 0, 0, 1])
    glMaterialfv(GL_FRONT, GL_SHININESS, 0)
    glMaterialfv(GL_FRONT, GL_EMISSION, [0, 0, 0, 1])

    glUniform1i(p_shader_mode, 1) # blinn

    glPushMatrix()
    glTranslate(position[0],  position[1],  position[2])
    glutSolidSphere(5, 20, 20)
    glPopMatrix()

def localize_sources():
    '''
    This function is run via thread
    '''
    global localizer
    global source_locations
    global sample_sec

    while True:
        localizer.set_data(epoc.sample)
        locations = []
        for sn in range(localizer.number_of_sources):
            locations.append(localizer.localize(sn))

        source_locations = locations

        time.sleep(sample_sec)

def draw_sources():
    global source_locations

    glPushMatrix()
    glMultMatrixf(rotation_matrix.toList())
    for source in source_locations:
        draw_source(source)
    glPopMatrix()

def draw_background(): 
    glUniform1i(p_shader_mode, 0)
    glBegin(GL_QUADS)
    glColor3f(0.53, 0.81, 0.98)
    glVertex3f(-300.0, -100.0, -200.0)
    glVertex3f(300.0, -100.0, -200.0)
    glColor3f(0.93, 0.91, 0.67)
    glVertex3f(300.0, -100.0, 200.0)
    glVertex3f(-300.0, -100.0, 200.0)
    glEnd()   

# Start the program
main()

