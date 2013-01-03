import pyglet
from pyglet.gl import *
from pyglet.window import key
from OpenGL.GLUT import *
from random import choice
from copy import copy, deepcopy
from event import Event
from grid import *

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

    def get_all_relations(self):
        full = dict()
        for i in self.relations:
            for j in self.relations[i]:
                if not full.has_key(j):
                    full[j] = dict()
                if not full.has_key(i):
                    full[i] = dict()
                full[j][i] = self.relations[i][j]
                full[i][j] = self.relations[i][j]
        return full

    def load_points(self, points):
        if len(points) % 6 != 0:
            raise ValueError('The number of reference most be multiple of 6')
        while points != []:
            p1 = Vertex(points.pop(0), points.pop(0), points.pop(0))
            p2 = Vertex(points.pop(0), points.pop(0), points.pop(0))
            self.add_edge(p1, p2)

    def get_edges(self):
        for i in self.relations:
            for j in self.relations[i]:
                yield (i, j, self.relations[i][j])

class Map(Graph):
    def __init__(self):
        super(Map, self).__init__()
        self.planes = dict()
        self.planes['v'] = dict()
        self.planes['h'] = dict()

    def add_planes(self):

        def add_plane_v(a, b, orientation):
            if not isinstance(self.planes['v'].get(a.y, None), Plane):
                self.planes['v'][a.y] = Plane('v')
            self.planes['v'][a.y].add_edge(a, b)

        def add_plane_h(a, b, orientation):
            if not isinstance(self.planes['h'].get(a.z, None), Plane):
                self.planes['h'][a.z] = Plane('h')
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

    def __init__(self, orientation):
        super(Plane, self).__init__()
        self.walls = []
        self.books = []
        self.orientation = orientation

class Map3D(object):
    def __init__(self, batch, points, alfa = 10, beta = 2):
        self.alfa = alfa
        self.beta = beta
        self.batch = batch
        self.graph = Map()
        self.graph.load_points(points)
        self.objects = []
        self.books = []
        self.generate()

    def gen_walls(self, p1, p2, edge_orientation, plane_orientation, color):
        orientation_axis = {'h':'x', 'v':'z', 'a':'y'}
        a = self.alfa
        b = self.beta
        param2 = p1.__getattribute__(orientation_axis[edge_orientation])
        param1 = p2.__getattribute__(orientation_axis[edge_orientation])
        shift = (a + b) / 2 if (abs(param1 - param2) - 1) % 2 == 0 else 0
        c = (abs(param1 - param2) - 1) * (a + b) + b
        m = min(param1, param2) * (a + b) + abs(param1 - param2) / 2 * (a + b) + shift
        relation = {
            'h':{
                'h':[c, b, a/2,  'm', 'vy', 'fz'],
                'a':[b, c, a/2, 'vx',  'm', 'fz'],
                },
            'v':{
                'v':[b, a/2, c, 'vx', 'fy',  'm'],
                'h':[c, a/2, b,  'm', 'fy', 'vz'],
                }
            }

        def extract(string):
            if string == 'm':
                return (m, m)
            if string[0] == 'v':
                v1 = p1.__getattribute__(string[1]) * (a + b) - (a + b) / 2
                v2 = v1 + a + b
                return (v1, v2)
            if string[0] == 'f':
                f = p1.__getattribute__(string[1]) * (a + b)
                return (f, f)

        width = relation[plane_orientation][edge_orientation][0]
        height = relation[plane_orientation][edge_orientation][1]
        thickness = relation[plane_orientation][edge_orientation][2]
        x1, x2 = extract(relation[plane_orientation][edge_orientation][3])
        y1, y2 = extract(relation[plane_orientation][edge_orientation][4])
        z1, z2 = extract(relation[plane_orientation][edge_orientation][5])
        b1 = Box(self.batch, width, height, thickness, color = color, pos = (x1,y1,z1))
        b2 = Box(self.batch, width, height, thickness, color = color, pos = (x2,y2,z2))
        return (b1, b2)

    def gen_limits(self, point, plane_orientation, color):
        w = self.alfa + self.beta * 2
        t = self.beta
        h = self.alfa / 2
        rel = {
            'n':[w, t, h, 'y',  1],
            's':[w, t, h, 'y', -1],
            'e':[t, w, h, 'x',  1],
            'w':[t, w, h, 'x', -1],
            'u':[w, h, t, 'z',  1],
            'd':[w, h, t, 'z', -1],
            }
        boxes = []
        if plane_orientation == 'h':
            limits = 'nsew'
        else:
            limits = 'ewud'
            rel['e'] = [t, h, w, 'x',  1]
            rel['w'] = [t, h, w, 'x', -1]
        for attrib in limits:
            if point.__getattribute__(attrib):
                local = {}
                width       = rel[attrib][0]
                height      = rel[attrib][1]
                thickness   = rel[attrib][2]
                for axis in 'xyz':
                    local[axis] = point.__getattribute__(axis) * (self.beta + self.alfa)
                local[rel[attrib][3]] = local[rel[attrib][3]] + (self.alfa + self.beta) / 2 * rel[attrib][4]
                boxes.append(Box(self.batch, width, height, thickness, color = color, pos = (local['x'], local['y'], local['z'])))
        return boxes

    def gen_books(self, p1, p2, color):
        books = []
        for point in p1.range(p2):
            books.append(GridObject(file_name='sphere.obj', scale=4, color = color, grid = point))
        return books

    def generate(self):
        for plane in self.graph.get_planes():
            if plane.orientation == 'h':
                color_limit = (0.0, 0.0, 1.0, 1.0)
                color_book  = (0.0, 1.0, 1.0, 1.0)
            else:
                color_limit = (0.0, 0.8, 0.0, 1.0)
                color_book  = (1.0, 0.8, 0.0, 1.0)

            for p1,p2, orientation in plane.get_edges():
                plane.walls += self.gen_walls(p1, p2, orientation, plane.orientation, color_limit)
                plane.books += self.gen_books(p1, p2, color_book)
            plane.books = set(plane.books)

            for point in plane.vertices:
                plane.walls += self.gen_limits(point, plane.orientation, color_limit)

class Board(pyglet.window.Window):

    def __init__(self):
        pyglet.window.Window.__init__(self, resizable=True)
        self.eye   = [-9.0, -10.0, 10.0]
        self.focus = [0.0, 0.0, 0.0]
        self.up    = [0.0, 0.0, 1.0]
        self.width = 1024
        self.height = 1024
        self.currentParameter = self.eye
        self.speed = 1.0
        #One-time GL setup
        glutInitDisplayMode(GLUT_RGBA | GLUT_DOUBLE | GLUT_ALPHA | GLUT_DEPTH)
        glClearColor(1, 1, 1, 1)
        glColor3f(1, 0, 0)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_CULL_FACE)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable (GL_LINE_SMOOTH)
        glShadeModel(GL_SMOOTH)

        def vec(*args):
            return (GLfloat * len(args))(*args)
        #glEnable(GL_LIGHTING)
        self.lights = False
        glEnable(GL_LIGHT0)
        glLightfv(GL_LIGHT0, GL_POSITION, vec(-150, -150, 150, 0))
        glLightfv(GL_LIGHT0, GL_SPECULAR, vec(.5, .5, .5, .5))
        glLightfv(GL_LIGHT0, GL_DIFFUSE, vec(0.1, 0.1, .1, 1.0))

        self.batch = pyglet.graphics.Batch()
        self.perspective = False
        self.alfa = 10
        self.beta = 2
        self.gridSize = 10
        self.size = 8
        self.change = (self.alfa - self.size) / 2

        self.gen_axes()
        self.walls = []

        self.alpha = 0.0
        self.label = pyglet.text.Label('0',
                                       font_name='Times New Roman',
                                       font_size=50,
                                       x=-150,
                                       y=10,
                                       batch=self.batch,
                                       color=(0,0,0,255))
        self.map = Map3D(self.batch, [
                                    2, 0,0, 3, 0,0,
                                    3,0,0,  3,1,0,
                                    3,0,0,  8,0,0,
                                    8,1,0, 3,1,0,
                                    8,1,0, 8,0,0,
                                    8,0,0, 9,0,0,
                                    9, 0,0, 9,-4,0,
                                    9,-4,0, 2,-4,0,
                                    2,-4,0, 2, 0,0,

                                    2,0,0,  2,0,9,

                                    2,0,9,  2,4,9,
                                    2,4,9,  -2,4,9,
                                    -2,4,9, -2,0,9,
                                    -2,0,9, 2,0,9,

                                    2,0,9,  6,0,9,
                                    6,0,9,  6,-4,9,
                                    6,-4,9, 2,-4,9,
                                    2,-4,9, 2,0,9,

                                    2,-4,0,  2,-4,4,
                                    2,-4,4,  9,-4,4,
                                    9,-4,4,  9,-4,0,
                                    9,-4,0,  9,-4,-4,
                                    9,-4,-4, 2,-4,-4,
                                    ]
                       )

        self.total_books = 0
        for plane in self.map.graph.get_planes():
            self.walls += plane.walls
            self.total_books += len(plane.books)
        self.eaten_books = 0
        self.first_update = True
        self.all_relations = self.map.graph.get_all_relations()
        
        vertex = self.map.graph.vertices[Point(2, 0, 0)]
        self.monster = HumanObject(self.all_relations, vertex, file_name='sphere.obj', scale=self.size, color=(1.0, 0.0, 0.1, 1.0))
        self.monster.speed.onChange += self.resetBadGuysStep

        self.active_plane_type = 'h'
        self.active_plane = 0
        self.set_plane_opacity(self.map.graph.planes['h'][0], 1.0)

        self.susan = ImportedObject3D('susan.obj', 20, pos=(-50.0, -50.0, 0.0))
        self.badGuys = []
        vertex = self.map.graph.vertices[Point(9,0,0)]
        self.badGuys.append(RobotObject(self.all_relations, vertex, file_name='bad.obj', scale=3.0, color=(1.0, 0.0, 0.0, 1.0)))
        for badguy in self.badGuys:
            self.setBadGuyStep(badguy)
            badguy.noMoreTarget = self.setBadGuyStep

        # Uncomment this line for a wireframe view
        # glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)

    def resetBadGuysStep(self):
        for badguy in self.badGuys:
            badguy.path = []

    def set_plane_opacity(self, plane, opacity):
        for wall in plane.walls:
            wall.vertex_list.colors = (wall.vertex_list.colors[:3] + [opacity]) * 36

        for book in plane.books:
            book.setOpacity(opacity)

    def setBadGuyStep(self, guy):
        self.badGuyStepNormal(guy)

    def badGuyStepRandom(self, guy):
        '''random'''
        if guy.grid == guy.target:
            vertices = copy(guy.connected)
            print 'Keys', vertices
            if len(vertices) > 1:
                del vertices[guy.origin]
            guy.updateTarget(choice(vertices))

    def badGuyStepNormal(self, guy):
        '''normal'''
        if guy.grid != self.monster.grid:
            print 'Points2', guy.origin, self.monster.origin, self.monster
            vertices = copy(guy.connections)
            path = self.generatePath(guy.origin, copy(self.monster.origin))
            print 'Path1:', path
            target = self.monster.target
            if None != target:
                path.append(target)
            print 'Path2:', path
            guy.target = path.pop(0)
            guy.path = path
        else:
            guy.stop()

    def generatePath(self, source, destination):
        edges = deepcopy(self.all_relations)
        visited = []
        source.parent = None
        frontier = [source]
        print 'Points:', source, destination
        while len(frontier) != 0:
            print 'Frontier', frontier
            current = frontier.pop()
            if current == destination:
                path = []
                while current.parent != None:
                    path.insert(0, current)
                    current = current.parent
                return path

            visited.append(current)
            sons = edges[current].keys()
            for son in sons:
                if not son in visited and not son in frontier:
                    son.parent = current
                    frontier.append(son)
        raise ValueError("Path no found")

    def update(self, dt):

        self.monster.moveForward()
        self.monster.updateGrids()

        for badGuy in self.badGuys:
            badGuy.moveForward()
            badGuy.updateGrids()

        if self.first_update:
            self.eaten_books -= 1
            self.total_books -= 1
            self.first_update = False

        for plane in self.map.graph.get_planes():
            book = self.colliding(self.monster, plane.books)
            if book != None:
                plane.books.remove(book)
                self.eaten_books += 1
                self.label.text = str(self.eaten_books * 100)
                break

        if self.total_books == self.eaten_books:
            self.label.text = "Winner!!"

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
        self.monster.draw_faces()
        [guy.draw_faces() for guy in self.badGuys]
        #self.susan.draw_points()
        self.susan.draw_faces()
        for plane in self.map.graph.get_planes():
            for book in plane.books:
                book.draw_faces()
        glFlush()

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
        elif symbol == key.O:
            if self.lights:
                self.lights = False
                glDisable(GL_LIGHTING)
            else:
                self.lights = True
                glEnable(GL_LIGHTING)
        elif symbol == key.X:
            self.currentParameter = self.eye
            self.speed = 10.0
        elif symbol == key.Y:
            self.currentParameter = self.focus
            self.speed = 10.0
        elif symbol == key.Z:
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
        elif symbol in [key.RIGHT, key.L, key.F]:
            self.monster.setDirection('e')
        elif symbol in [key.LEFT, key.J, key.S]:
            self.monster.setDirection('w')
        elif symbol in [key.UP, key.I]:
            self.monster.setDirection('n')
        elif symbol in [key.DOWN, key.K]:
            self.monster.setDirection('s')
        elif symbol == key.E:
            self.monster.setDirection('u')
        elif symbol == key.D:
            self.monster.setDirection('d')

        self.initView()
        return pyglet.event.EVENT_HANDLED

    def colliding(self, object1, objectList):
        for object2 in objectList:
            minDistanceX = object1.width     / 2 + object2.width / 2
            minDistanceY = object1.height    / 2 + object2.height / 2
            minDistanceZ = object1.thickness / 2 + object2.thickness / 2
            distanceX = abs(object1.x - object2.x)
            distanceY = abs(object1.y - object2.y)
            distanceZ = abs(object1.z - object2.z)
            if  distanceX < minDistanceX \
                    and  distanceY < minDistanceY \
                    and  distanceZ < minDistanceZ:
                return object2
        return None

if __name__ == '__main__':
    win = Board()
    pyglet.clock.schedule_interval(win.update, 0.033)
    pyglet.app.run()
