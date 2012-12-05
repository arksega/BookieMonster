import pyglet
from pyglet.gl import *
from pyglet.window import key

class Point(object):
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z
        self.n, self.s, self.e, self.w, self.u, self.d = [True] * 6

    def __eq__(self,other):
        return self.x == other.x and self.y == other.y and self.z == other.z

    def __str__(self):
        return 'Point' + repr((self.x, self.y, self.z, self.n, self.s, self.e, self.w, self.u, self.d))

    def __repr__(self):
        return 'Point' + repr((self.x, self.y, self.z))

    def __hash__(self):
        return self.x * 100 + self.y * 10 + self.z

class Graph(object):
    def __init__(self):
        self.relations = dict()
        self.vertices = dict()

    def __repr__(self):
        string = 'Vertices:\n'
        for v in self.vertices:
            string += str(v) + '\n'
        return string

    def get_orientation(self, a, b):
        if   a.y == b.y and a.z == b.z:
            return 'h'
        elif a.z == b.z and a.x == b.x:
            return 'a'
        elif a.x == b.x and a.y == b.y:
            return 'v'
        raise ValueError('Vertices not alligned')

    def get_stored_vertex(self, vertex):
        if not vertex in self.vertices:
            self.vertices[vertex] = vertex
        return self.vertices[vertex]

    def update_limits(self, a, b, orientation):
        relation = {
            'h':'xewud',
            'a':'ynsud',
            'v':'zudns',
            }
        def updater_limits(a,b,param):
            if a.__getattribute__(param[0]) < b.__getattribute__(param[0]):
                a.__setattr__(param[1], False)
                b.__setattr__(param[2], False)
            else:
                a.__setattr__(param[2], False)
                b.__setattr__(param[1], False)

        updater_limits(a, b, relation[orientation])

    def add_edge(self, a ,b):
        if a == b:
            raise ValueError('No edges between same vertex')

        a = self.get_stored_vertex(a)
        b = self.get_stored_vertex(b)

        if not self.relations.has_key(a):
            self.relations[a] = dict()

        orientation = self.get_orientation(a, b)
        self.relations[a][b] = orientation
        self.update_limits(a, b, orientation)

    def load_points(self, points):
        if len(points) % 6 != 0:
            raise ValueError('The number of reference most be multiple of 6')
        while points != []:
            p1 = Point(points.pop(0), points.pop(0), points.pop(0))
            p2 = Point(points.pop(0), points.pop(0), points.pop(0))
            self.add_edge(p1, p2)

    def get_edges(self):
        for i in self.relations:
            for j in self.relations[i]:
                yield (i,j)

class Map(Graph):
    def __init__(self):
        super(Map, self).__init__()
        self.planes = dict()
        self.planes['v'] = dict()
        self.planes['h'] = dict()

    def add_planes(self):

        def add_plane_v(a, b, orientation):
            if not isinstance(self.planes['v'].get(a.y, None), Plane):
                self.planes['v'][a.y] = Plane()
            self.planes['v'][a.y].add_edge(a, b)

        def add_plane_h(a, b, orientation):
            if not isinstance(self.planes['h'].get(a.z, None), Plane):
                self.planes['h'][a.z] = Plane()
            self.planes['h'][a.z].add_edge(a, b)

        for a in self.relations:
            for b in self.relations[a]:
                orientation = self.relations[a][b]

                if orientation == 'v':
                    add_plane_v(a, b, orientation)
                if orientation == 'a':
                    add_plane_h(a, b, orientation)
                if orientation == 'h':
                    add_plane_v(a, b, orientation)
                    add_plane_h(a, b, orientation)

        for plane in self.planes['v'].keys():
            valid = False
            for vertex in self.planes['v'][plane].vertices:
                if not vertex.u or not vertex.d:
                    valid = True
            if not valid:
                self.planes['v'].pop(plane)

        for plane in self.planes['h'].keys():
            valid = False
            for vertex in self.planes['h'][plane].vertices:
                if not vertex.n or not vertex.s:
                    valid = True
            if not valid:
                self.planes['h'].pop(plane)

    def get_planes(self):
        return self.planes['h'].values() + self.planes['v'].values()

    def load_points(self, points):
        super(Map, self).load_points(points)
        self.add_planes()

class Plane(Graph):

    def __init__(self):
        super(Plane, self).__init__()
        self.walls = []

class Object3D(object):

    def __init__(self, width, height, thickness, color = (0.0, 0.0, 0.0), pos = (0.0, 0.0, 0.0)):
        self.red    = color[0]
        self.green  = color[1]
        self.blue   = color[2]
        self.posX   = pos[0]
        self.posY   = pos[1]
        self.posZ   = pos[2]
        self.width = width
        self.height = height
        self.thickness = thickness

class Box(Object3D):
    def __init__(self, batch, width, height, thickness, color = (0.0, 0.0, 0.0), pos = (0.0, 0.0, 0.0)):
        super(Box, self).__init__(width, height, thickness, color, pos)
        self.x1 = self.posX + width / 2
        self.y1 = self.posY + height / 2
        self.z1 = self.posZ + thickness / 2
        self.x2 = self.posX - width / 2
        self.y2 = self.posY - height / 2
        self.z2 = self.posZ - thickness / 2
        self.batch = batch

        self.vertex_list = self.batch.add(36, GL_TRIANGLES, None,
            ('v3f/stream', (
                    # Front
                    self.x1,self.y1,self.z1, self.x2,self.y1,self.z1, self.x1,self.y2,self.z1,
                    self.x2,self.y1,self.z1, self.x2,self.y2,self.z1, self.x1,self.y2,self.z1,

                    # Back
                    self.x1,self.y2,self.z2, self.x2,self.y1,self.z2, self.x1,self.y1,self.z2,
                    self.x2,self.y2,self.z2, self.x2,self.y1,self.z2, self.x1,self.y2,self.z2,

                    # Left
                    self.x1,self.y1,self.z2, self.x1,self.y1,self.z1, self.x1,self.y2,self.z1,
                    self.x1,self.y1,self.z2, self.x1,self.y2,self.z1, self.x1,self.y2,self.z2,

                    # Right
                    self.x2,self.y1,self.z1, self.x2,self.y1,self.z2, self.x2,self.y2,self.z1,
                    self.x2,self.y1,self.z2, self.x2,self.y2,self.z2, self.x2,self.y2,self.z1,

                    # Top
                    self.x2,self.y1,self.z1, self.x1,self.y1,self.z1, self.x1,self.y1,self.z2,
                    self.x2,self.y1,self.z2, self.x2,self.y1,self.z1, self.x1,self.y1,self.z2,

                    # Bottom
                    self.x1,self.y2,self.z1, self.x2,self.y2,self.z1, self.x1,self.y2,self.z2,
                    self.x2,self.y2,self.z1, self.x2,self.y2,self.z2, self.x1,self.y2,self.z2)
                ),
                ('c4f/stream', (self.red, self.green, self.blue, 1.0) * 36)
        )

class Sphere(Object3D):
    def __init__(self, radius = 5.0, slices = 12, stacks = 12, color = (0.0, 0.0, 0.0), pos = (0.0, 0.0, 0.0)):
        super(Sphere, self).__init__(radius * 2, radius * 2, radius * 2, color, pos)
        self.radius = radius
        self.slices = slices
        self.stacks = stacks
        self.q = gluNewQuadric()
        self.deltaX = 0.0
        self.deltaY = 0.0
        self.deltaZ = 0.0

    def draw(self):
        glColor3f(self.red, self.green, self.blue)
        gluQuadricDrawStyle(self.q,GLU_LINE)
        #gluQuadricDrawStyle(self.q,GLU_FILL)
        glPushMatrix()
        glTranslatef(self.posX, self.posY, self.posZ)
        gluSphere(self.q, self.radius, self.slices, self.stacks)
        glPopMatrix()

    def moveForward(self):
        self.posX += self.deltaX
        self.posY += self.deltaY
        self.posZ += self.deltaZ

    def moveBack(self):
        self.posX -= self.deltaX
        self.posY -= self.deltaY
        self.posZ -= self.deltaZ

    def stop(self):
        self.deltaX = 0.0
        self.deltaY = 0.0
        self.deltaZ = 0.0

class Map3D(object):
    def __init__(self, batch, points, alfa = 10, beta = 2):
        self.alfa = alfa
        self.beta = beta
        self.batch = batch
        self.graph = Map()
        self.graph.load_points(points)
        print self.graph.planes
        self.objects = []
        self.generate()

    def generate(self):
        for plane in self.graph.get_planes():
            for p1,p2 in plane.get_edges():
                if p1.x != p2.x:
                    if (abs(p1.x - p2.x) - 1) % 2 == 0:
                        shift = (self.alfa + self.beta) / 2
                    else:
                        shift = 0
                    width = (abs(p1.x - p2.x) - 1) * (self.alfa + self.beta) - self.beta
                    height = self.beta
                    thickness = self.alfa
                    x = min(p1.x, p2.x) * (self.alfa + self.beta) + abs(p2.x - p1.x) / 2 * (self.alfa + self.beta) + shift
                    y1 = p1.y * (self.alfa + self.beta) - (self.alfa + self.beta) / 2
                    y2 = y1 + self.alfa + self.beta
                    z = p1.z * (self.alfa + self.beta)
                    plane.walls.append(Box(self.batch, width, height, thickness,color=(1.0,1.0,0.0), pos=(x,y1,z)))
                    plane.walls.append(Box(self.batch, width, height, thickness,color=(1.0,1.0,0.0), pos=(x,y2,z)))
                elif p1.y != p2.y:
                    if (abs(p1.y - p2.y) - 1) % 2 == 0:
                        shift = (self.alfa + self.beta) / 2
                    else:
                        shift = 0
                    width = self.beta
                    height = (abs(p1.y - p2.y) - 1) * (self.alfa + self.beta) + self.beta
                    thickness = self.alfa
                    y = min(p1.y, p2.y) * (self.alfa + self.beta) + abs(p2.y - p1.y) / 2 * (self.alfa + self.beta) + shift
                    x2 = p1.x * (self.alfa + self.beta) - (self.alfa + self.beta) / 2
                    x1 = x2 + self.alfa + self.beta
                    z = p1.z * (self.alfa + self.beta)
                    plane.walls.append(Box(self.batch, width, height, thickness,color=(0.0,1.0,1.0), pos=(x1,y,z)))
                    plane.walls.append(Box(self.batch, width, height, thickness,color=(0.0,1.0,1.0), pos=(x2,y,z)))
                elif p1.z != p2.z:
                    if (abs(p1.z - p2.z) - 1) % 2 == 0:
                        shift = (self.alfa + self.beta) / 2
                    else:
                        shift = 0
                    width = self.beta
                    height = self.alfa
                    thickness = (abs(p1.z - p2.z) - 1) * (self.alfa + self.beta) + self.beta
                    z = min(p1.z, p2.z) * (self.alfa + self.beta) + abs(p2.z - p1.z) / 2 * (self.alfa + self.beta) + shift
                    y = p1.y * (self.alfa + self.beta)
                    x2 = p1.x * (self.alfa + self.beta) - (self.alfa + self.beta) / 2
                    x1 = x2 + self.alfa + self.beta
                    plane.walls.append(Box(self.batch, width, height, thickness,color=(1.0,0.0,1.0), pos=(x1,y,z)))
                    plane.walls.append(Box(self.batch, width, height, thickness,color=(1.0,0.0,1.0), pos=(x2,y,z)))

            for point in plane.vertices:
                if point.n:
                    width = self.alfa + self.beta * 2
                    height = self.beta
                    thickness = self.alfa
                    x = point.x * (self.beta + self.alfa)
                    y = point.y * (self.beta + self.alfa) + (self.alfa + self.beta) / 2
                    z = point.z * (self.beta + self.alfa)
                    plane.walls.append(Box(self.batch, width, height, thickness,color=(1.0,0.0,1.0), pos=(x,y,z)))
                if point.s:
                    width = self.alfa + self.beta * 2
                    height = self.beta
                    thickness = self.alfa
                    x = point.x * (self.beta + self.alfa)
                    y = point.y * (self.beta + self.alfa) - (self.alfa + self.beta) / 2
                    z = point.z * (self.beta + self.alfa)
                    plane.walls.append(Box(self.batch, width, height, thickness,color=(0.0,0.0,1.0), pos=(x,y,z)))
                if point.e:
                    width = self.beta
                    height = self.alfa
                    thickness = self.alfa
                    y = point.y * (self.beta + self.alfa)
                    x = point.x * (self.beta + self.alfa) + (self.alfa + self.beta) / 2
                    z = point.z * (self.beta + self.alfa)
                    plane.walls.append(Box(self.batch, width, height, thickness,color=(1.0,0.0,0.0), pos=(x,y,z)))
                if point.w:
                    width = self.beta
                    height = self.alfa
                    thickness = self.alfa
                    y = point.y * (self.beta + self.alfa)
                    x = point.x * (self.beta + self.alfa) - (self.alfa + self.beta) / 2
                    z = point.z * (self.beta + self.alfa)
                    plane.walls.append(Box(self.batch, width, height, thickness,color=(0.0,1.0,0.0), pos=(x,y,z)))
                if point.u:
                    width = self.alfa + self.beta * 2
                    height = self.alfa
                    thickness = self.beta
                    y = point.y * (self.beta + self.alfa)
                    x = point.x * (self.beta + self.alfa)
                    z = point.z * (self.beta + self.alfa) + (self.alfa + self.beta) / 2
                    plane.walls.append(Box(self.batch, width, height, thickness,color=(0.0,0.0,0.0), pos=(x,y,z)))
                if point.d:
                    width = self.alfa + self.beta * 2
                    height = self.alfa
                    thickness = self.beta
                    y = point.y * (self.beta + self.alfa)
                    x = point.x * (self.beta + self.alfa)
                    z = point.z * (self.beta + self.alfa) - (self.alfa + self.beta) / 2
                    plane.walls.append(Box(self.batch, width, height, thickness,color=(0.0,0.0,0.0), pos=(x,y,z)))

class Board(pyglet.window.Window):

    def __init__(self):
        pyglet.window.Window.__init__(self, resizable=True)
        self.eye   = [5.0, -10.0, 20.0]
        self.focus = [0.0, 0.0, 0.0]
        self.up    = [0.0, 0.0, 1.0]
        self.width = 1024
        self.height = 1024
        self.currentParameter = self.eye
        self.speed = 1.0
        #One-time GL setup
        glClearColor(1, 1, 1, 1)
        glColor3f(1, 0, 0)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_CULL_FACE)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable (GL_LINE_SMOOTH)
        self.batch = pyglet.graphics.Batch()
        self.monster = Sphere(color=(1.0, 0.0, 0.1), pos=(29.0,0.0,0.0), radius = 4.0)
        self.gen_axes()
        self.walls = []

        self.alpha = 0.0
        self.perspective = False
        self.alfa = 10
        self.beta = 2
        self.gridSize = 10
        self.map = Map3D(self.batch, [2, 0,0, 3, 0,0,
                                    3,0,0,  3,1,0,
                                    3,0,0,  8,0,0,
                                    8,1,0, 3,1,0,
                                    8,1,0, 8,0,0,
                                    8,0,0, 9,0,0,
                                    9, 0,0, 9,-4,0,
                                    9,-4,0, 2,-4,0,
                                    2,-4,0, 2, 0,0,

                                    2,0,0,  2,0,9,
                                    -4,4,0,  -4,4,9,
                                    -4,4,9,  0 ,4,9,
                                    -4,4,9,  -4,0,9,
                                    -4,4,9,  -4,8,9,

                                    -2,-2,2, -6,-2,2,
                                    -6,-2,2, -6,-2,6,
                                    -6,-2,6, -2,-2,6,
                                    -2,-2,6, -2,-2,2,
                                    ]
                       )
        for plane in self.map.graph.get_planes():
            self.walls += plane.walls

        # Uncomment this line for a wireframe view
        # glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)

    def update(self, dt):
        self.monster.moveForward()
        if self.colliding(self.monster, self.walls):
            self.monster.moveBack()
            self.monster.stop()

    def gen_axes(self):
        glLineWidth(2)

        vertex_list = self.batch.add(6, GL_LINES, None,
            ('v3f/stream', ( 0,0,0,  100,0,0,
                            0,0,0,  0,100,0,
                            0,0,0,  0,0,100)
            ),
            ('c4B/stream', ( 255,0,0,255, 255,0,0,255,
                            0,255,0,255, 0,255,0,255,
                            0,0,255,255, 0,0,255,255)
            )
        )

        glLineWidth(1)

    def on_draw(self):
        # Clear buffers
        glClear(GL_COLOR_BUFFER_BIT  | GL_DEPTH_BUFFER_BIT)
        # Draw Grid

        glBegin(GL_LINES)
        glColor3f(0.0, 0.0, 0.0)
        end = self.alfa * self.gridSize + self.beta * self.gridSize + self.alfa / 2
        step = self.alfa + self.beta
        for i in range(0,self.gridSize * 2 + 2):
            glVertex3i(end - i * step,-end - self.beta, 0)
            glVertex3i(end - i * step, end + self.beta, 0)
            glVertex3i(end - i * step + self.beta,-end - self.beta, 0)
            glVertex3i(end - i * step + self.beta, end + self.beta, 0)

            glVertex3i(-end - self.beta, end - i * step, 0)
            glVertex3i( end + self.beta, end - i * step, 0)
            glVertex3i(-end - self.beta, end - i * step + self.beta, 0)
            glVertex3i( end + self.beta, end - i * step + self.beta, 0)
        glEnd()

        self.batch.draw()
        self.monster.draw()
    
    def on_resize(self, width, height):
        glViewport(0,0,self.width,self.height)
        glMatrixMode(GL_PROJECTION)
        self.initView()
        return pyglet.event.EVENT_HANDLED

    def initView(self):
        glLoadIdentity()
        if self.perspective:
            gluPerspective(
                90.0,                                   # Field Of View
                float(self.width)/float(self.height),   # aspect ratio
                1.0,                                    # z near
                1000.0)                                 # z far
        else:
            glOrtho(-150, 150, -150, 150, -300, 300);
        gluLookAt(*(self.eye + self.focus + self.up))

    def on_key_press(self, symbol, modifiers):
        glLoadIdentity()
        if symbol == key.P:
            self.perspective = not self.perspective
        elif symbol == key.X:
            self.currentParameter = self.eye
            self.speed = 10.0
        elif symbol == key.Y:
            self.currentParameter = self.focus
            self.speed = 10.0
        elif symbol == key.Z:
            self.speed = 0.1
            self.currentParameter = self.up
        elif symbol == key.NUM_ADD:
            self.alpha += 0.1
            plane = self.map.graph.planes['h'][0]
            for wall in plane.walls:
                wall.vertex_list.colors = (wall.vertex_list.colors[:3] + [self.alpha]) * 36
        elif symbol == key.NUM_SUBTRACT:
            self.alpha -= 0.1
            plane = self.map.graph.planes['h'][0]
            for wall in plane.walls:
                wall.vertex_list.colors = (wall.vertex_list.colors[:3] + [self.alpha]) * 36
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
        elif symbol in [key.RIGHT, key.L, key.F]:
            self.monster.stop()
            self.monster.deltaX = 1.0
        elif symbol in [key.LEFT, key.J, key.S]:
            self.monster.stop()
            self.monster.deltaX = -1.0
        elif symbol in [key.UP, key.I]:
            self.monster.stop()
            self.monster.deltaY = 1.0
        elif symbol in [key.DOWN, key.K]:
            self.monster.stop()
            self.monster.deltaY = -1.0
        elif symbol == key.E:
            self.monster.stop()
            self.monster.deltaZ = 1.0
        elif symbol == key.D:
            self.monster.stop()
            self.monster.deltaZ = -1.0
        elif symbol == key.SPACE:
            self.monster.stop()

        print(self.eye + self.focus + self.up)
        self.initView()
        return pyglet.event.EVENT_HANDLED
    
    def colliding(self, object1, objectList):
        for object2 in objectList:
            minDistanceX = object1.width     / 2 + object2.width / 2
            minDistanceY = object1.height    / 2 + object2.height / 2
            minDistanceZ = object1.thickness / 2 + object2.thickness / 2
            distanceX = abs(object1.posX - object2.posX)
            distanceY = abs(object1.posY - object2.posY)
            distanceZ = abs(object1.posZ - object2.posZ)
            if  distanceX < minDistanceX \
                    and  distanceY < minDistanceY \
                    and  distanceZ < minDistanceZ:
                return True
        return False

if __name__ == '__main__':
    win = Board()
    pyglet.clock.schedule_interval(win.update, 0.033)
    pyglet.app.run()
