import pyglet
from pyglet.gl import *
from pyglet.window import key

class Sphere():
    def __init__(self, red = 0.0, green = 0.0, blue = 0.0, radius = 5.0, slices = 12, stacks = 12):
        self.red    = red
        self.green  = green
        self.blue   = blue
        self.radius = radius
        self.slices = slices
        self.stacks = stacks
        self.q = gluNewQuadric()
        self.posX = 0.0
        self.posY = 0.0
        self.deltaX = 0.0
        self.deltaY = 0.0

    def draw(self):
        self.move()
        glColor3f(self.red, self.green, self.blue)
        #gluQuadricDrawStyle(q,GLU_LINE)
        gluQuadricDrawStyle(self.q,GLU_FILL)
        glPushMatrix()
        glTranslatef(self.posX, self.posY, 0.0)
        gluSphere(self.q, self.radius, self.slices, self.stacks)
        glPopMatrix()

    def move(self):
        self.posX += self.deltaX
        self.posY += self.deltaY

    def stop(self):
        self.deltaX = 0.0
        self.deltaY = 0.0

class Board(pyglet.window.Window):

    def __init__(self):
        pyglet.window.Window.__init__(self, resizable=True)
        self.eye   = [0.0, -10.0, 100.0]
        self.focus = [0.0, 0.0, 0.0]
        self.up    = [0.0, 1.0, 0]
        self.currentParameter = self.eye
        self.speed = 1.0
        #One-time GL setup
        glClearColor(1, 1, 1, 1)
        glColor3f(1, 0, 0)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_CULL_FACE)
        self.monster = Sphere(0.0, 0.0, 0.1)

        # Uncomment this line for a wireframe view
        # glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)

    def on_draw(self):

        # Clear buffers
        glClear(GL_COLOR_BUFFER_BIT  | GL_DEPTH_BUFFER_BIT)
        # Draw Grid
        glBegin(GL_LINES)
        glColor3f(0.0, 0.0, 0.0)
        for i in range(0,21):
            glVertex3f(100 - i*10.0,-100., 0.)
            glVertex3f(100 -i*10.0, 100., 0.)

            glVertex3f(-100., 100 - i*10.0, 0.)
            glVertex3f( 100., 100 - i*10.0, 0.)
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
        self.monster.draw()
    
    def on_resize(self, width, height):
        glViewport(0,0,self.width,self.height)
        glMatrixMode(GL_PROJECTION)
        self.initView()
        return pyglet.event.EVENT_HANDLED

    def initView(self):
        glLoadIdentity()
        gluPerspective(
            90.0,                                   # Field Of View
            float(self.width)/float(self.height),   # aspect ratio
            1.0,                                    # z near
            1000.0)                                 # z far
        gluLookAt(*(self.eye + self.focus + self.up))

    def on_key_press(self, symbol, modifiers):
        glLoadIdentity()
        if symbol == key.A:
            self.currentParameter = self.eye
            self.speed = 1.0
        elif symbol == key.B:
            self.currentParameter = self.focus
            self.speed = 1.0
        elif symbol == key.C:
            self.speed = 0.1
            self.currentParameter = self.up
        elif symbol == key.NUM_7:
            self.currentParameter[0] = round(self.currentParameter[0] + self.speed,1)
        elif symbol == key.NUM_8:
            self.currentParameter[1] = round(self.currentParameter[1] + self.speed,1)
        elif symbol == key.NUM_9:
            self.currentParameter[2] = round(self.currentParameter[2] + self.speed,1)
        elif symbol == key.NUM_1:
            self.currentParameter[0] = round(self.currentParameter[0] - self.speed,1)
        elif symbol == key.NUM_2:
            self.currentParameter[1] = round(self.currentParameter[1] - self.speed,1)
        elif symbol == key.NUM_3:
            self.currentParameter[2] = round(self.currentParameter[2] - self.speed,1)
        elif symbol == key.RIGHT:
            self.monster.deltaX = 1.0
            self.monster.deltaY = 0.0
        elif symbol == key.LEFT:
            self.monster.deltaX = -1.0
            self.monster.deltaY = 0.0
        elif symbol == key.UP:
            self.monster.deltaY = 1.0
            self.monster.deltaX = 0.0
        elif symbol == key.DOWN:
            self.monster.deltaY = -1.0
            self.monster.deltaX = 0.0
        elif symbol == key.SPACE:
            self.monster.stop()

        print(self.eye + self.focus + self.up)
        self.initView()
        return pyglet.event.EVENT_HANDLED
    
win = Board()

pyglet.app.run()
