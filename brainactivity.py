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
from OpenGL.GL.shaders import *

# Register global variables
brain = None

angle_x = 0
angle_y = 0

prev_x = 0
prev_y = 0

screen_w = 800
screen_h = 600

def init():
    """
    Initialize OpenGL and GLUT
    """

    global screen_w
    global screen_h
    
    # Initialize engine
    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_DEPTH | GLUT_SRGB)
    glutInitWindowSize(screen_w, screen_h)
    glutInitWindowPosition(200,50);
    glutCreateWindow('Brain Activity 3D')
   
    # Z-buffer
    glEnable(GL_DEPTH_TEST)

    # Perpective
    glMatrixMode(GL_PROJECTION)
    gluPerspective(45, 4/3, 0.5, 400)

    glMatrixMode(GL_MODELVIEW)

    # Enable basic lighting
    glEnable(GL_LIGHTING)

    # Add light sources
    glEnable(GL_LIGHT0)
    
    # Blending
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
    
    # Set up shaders
    with open("brain_vertex_shader.glsl") as vertex_shader, open("brain_fragment_shader.glsl") as fragment_shader:    
        program = compileProgram(
            compileShader(vertex_shader.read(), GL_VERTEX_SHADER),
            compileShader(fragment_shader.read(), GL_FRAGMENT_SHADER),
        )
    
    # Use shaders
    glUseProgram(program)
    
    # Start main loop
    glutMainLoop()

def reshape(w, h):
    """
    Process reshaping of the window
    """
    screen_w = w
    screen_h = h

def display():
    """
    Main drawing function
    """
    global brain
    global angle_x
    global angle_y

    # Clear screen
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);

    #Light source 0
    glLightfv(GL_LIGHT0, GL_AMBIENT, [0, 0, 0, 1])
    glLightfv(GL_LIGHT0, GL_DIFFUSE, [1, 1, 1, 1])
    glLightfv(GL_LIGHT0, GL_SPECULAR, [1, 1, 1, 1])
    glLightfv(GL_LIGHT0, GL_POSITION, [0, 0, 110, 0])
    
    # Material front   
    glMaterialfv(GL_FRONT, GL_AMBIENT, [0.2, 0.2, 0.2, 1])
    glMaterialfv(GL_FRONT, GL_DIFFUSE, [0.8, 0.8, 0.8, 1])
    glMaterialfv(GL_FRONT, GL_SPECULAR, [0, 0, 0, 1])
    glMaterialfv(GL_FRONT, GL_SHININESS, 0)
    glMaterialfv(GL_FRONT, GL_EMISSION, [0, 0, 0, 1])
    
    # Material back   
    glMaterialfv(GL_BACK, GL_AMBIENT, [0.2, 0.2, 0.2, 1])
    glMaterialfv(GL_BACK, GL_DIFFUSE, [0.8, 0.8, 0.8, 1])
    glMaterialfv(GL_BACK, GL_SPECULAR, [0, 0, 0, 1])
    glMaterialfv(GL_BACK, GL_SHININESS, 0)
    glMaterialfv(GL_BACK, GL_EMISSION, [0, 0, 0, 1])
    
    # Set up the camera
    glLoadIdentity()
    gluLookAt(200, 200, 200, 0, 0, 0, 0, 0, 1)

    # Draw brain
    glPushMatrix()
    glRotatef(angle_x, 0, 0, 1)
    glRotatef(angle_y, 1, 0, 0)
    glCallList(brain.gl_list)
    glPopMatrix()

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
    # once we pressed the left button this corresponds to the start of the rotation
    global prev_x
    global prev_y
    if state == GLUT_DOWN and button == GLUT_LEFT_BUTTON:
        prev_x = x
        prev_y = y
    pass

def mouse_drag(x, y):
    """
    Process mouse events
    """
    global screen_w
    global screen_h
    global angle_x
    global angle_y
    global prev_x
    global prev_y
    
    dx = x - prev_x
    dy = y - prev_y
    
    # could be done more precisely
    angle_x += dx 
    angle_y += -dy
    
    prev_x = x
    prev_y = y
    
    #angle_x = (360 / float(screen_w)) * x;
    #angle_y = (-1)*(360 / float(screen_h)) * y ;

def keyboard():
    """
    Process keyboard events
    """
    pass

def init_model():
    """
    Load model from Wavefront .obj file
    """
    global brain
    brain = objloader.OBJ('brain_20k.obj', 'model', swapyz=False)

def main():
    """
    Build the main pipeline
    """
    init()


# Start the program
main()

