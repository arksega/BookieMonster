import pyglet
from pyglet.gl import *
key = pyglet.window.key

win   = pyglet.window.Window(resizable=True)

eye   = [0.0, -10.0, 10.0]
focus = [0.0, 0.0, 0.0]
up    = [0.0, 1.0, 0.0]
currentParameter = eye
unidad = 1.0
posX = 0.0
posY = 0.0
posZ = 0.0

@win.event
def on_draw():
    
    # Clear buffers
    glClear(GL_COLOR_BUFFER_BIT  | GL_DEPTH_BUFFER_BIT)
    # Draw Grid
    glBegin(GL_LINES)
    glColor3f(0.0, 0.0, 0.0)
    for i in range(10):
        glVertex3f(i*10.0,-100., 0.)
        glVertex3f(i*10.0, 100., 0.)
        
        glVertex3f(-i*10.0,-100., 0.)
        glVertex3f(-i*10.0, 100., 0.)

        glVertex3f(-100., i*10.0, 0.)
        glVertex3f( 100., i*10.0, 0.)

        glVertex3f(-100.,-i*10.0, 0.)
        glVertex3f( 100.,-i*10.0, 0.)
    glEnd()

    # Draw axes
    batch = pyglet.graphics.Batch()
    vertex_list = batch.add(6, GL_LINES, None,        
        ('v3f/stream', ( 0,0,0,  100,0,0,
                         0,0,0,  0,100,0,
                         0,0,0,  0,0,100)
        ),
        ('c4B/stream', ( 255,0,0,255, 255,0,0,255,
                         0,255,0,255, 0,255,0,255,
                         0,0,255,255, 0,0,255,255)
        )
    )
    batch.draw()
    
    #batch = pyglet.graphics.Batch()
    drawSphere()

def drawSphere():
    # Draw sphere
    glColor3f(0.0, 0.0, 0.0)
    q = gluNewQuadric()
    #gluQuadricDrawStyle(q,GLU_LINE)
    gluQuadricDrawStyle(q,GLU_FILL)
    glPushMatrix()
    glTranslatef(posX, posY, 0.0)
    gluSphere(q,5.0,20,20)
    glPopMatrix()
    
@win.event
def on_resize(width, height):
    glViewport(0,0,width,height)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective( 
        90.0,                            # Field Of View
        float(width)/float(height),  # aspect ratio
        1.0,                             # z near
        1000.0)                           # z far
    # INITIALIZE THE MODELVIEW MATRIX FOR THE TRACKBALL CAMERA
    print "update"
    gluLookAt(*(eye + focus + up))
    glMatrixMode(GL_MODELVIEW)
    return pyglet.event.EVENT_HANDLED

@win.event
def on_key_press(symbol, modifiers):
    glLoadIdentity()
    global currentParameter, unidad , posX, posY, posZ
    if symbol == key.A:
        currentParameter = eye
        unidad = 1.0
    elif symbol == key.B:
        currentParameter = focus
        unidad = 1.0
    elif symbol == key.C:
        unidad = 0.1
        currentParameter = up
    elif symbol == key.NUM_7:
        currentParameter[0] = round(currentParameter[0] + unidad,1)
    elif symbol == key.NUM_8:
        currentParameter[1] = round(currentParameter[1] + unidad,1)
    elif symbol == key.NUM_9:
        currentParameter[2] = round(currentParameter[2] + unidad,1)
    elif symbol == key.NUM_1:
        currentParameter[0] = round(currentParameter[0] - unidad,1)
    elif symbol == key.NUM_2:
        currentParameter[1] = round(currentParameter[1] - unidad,1)
    elif symbol == key.NUM_3:
        currentParameter[2] = round(currentParameter[2] - unidad,1)
    elif symbol == key.RIGHT:
        posX += 1.0
    elif symbol == key.LEFT:
        posX -= 1.0
    elif symbol == key.UP:
        posY += 1.0
    elif symbol == key.DOWN:
        posY -= 1.0

    print(eye + focus + up)
    gluLookAt(*(eye + focus + up))
    glMatrixMode(GL_MODELVIEW)
    return pyglet.event.EVENT_HANDLED
    
#One-time GL setup
glClearColor(1, 1, 1, 1)
glColor3f(1, 0, 0)
glEnable(GL_DEPTH_TEST)
glEnable(GL_CULL_FACE)

# Uncomment this line for a wireframe view
glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)

pyglet.app.run()
