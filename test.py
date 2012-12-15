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

class Object3D(object):

    def __init__(self, width, height, thickness, color = (0.0, 0.0, 0.0, 1.0), pos = (0.0, 0.0, 0.0)):
        self.red    = color[0]
        self.green  = color[1]
        self.blue   = color[2]
        self.alpha  = color[3]
        self.posX   = pos[0]
        self.posY   = pos[1]
        self.posZ   = pos[2]
        self.width = width
        self.height = height
        self.thickness = thickness

class Box(Object3D):
    def __init__(self, batch, width, height, thickness, color = (0.0, 0.0, 0.0, 1.0), pos = (0.0, 0.0, 0.0)):
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
                ('c4f/stream', (self.red, self.green, self.blue, 0.1) * 36)
        )

class Sphere(Object3D):
    def __init__(self, radius = 5.0, slices = 12, stacks = 12, color = (0.0, 0.0, 0.0, 1.0), pos = (0.0, 0.0, 0.0)):
        super(Sphere, self).__init__(radius * 2, radius * 2, radius * 2, color, pos)
        self.radius = radius
        self.slices = slices
        self.stacks = stacks
        self.q = gluNewQuadric()
        self.deltaX = 0.0
        self.deltaY = 0.0
        self.deltaZ = 0.0

    def __eq__(self, other):
        return self.posX == other.posX and self.posY == other.posY and self.posZ == other.posZ

    def __hash__(self):
        return hash((self.posX, self.posY, self.posZ))

    def __repr__(self):
        return str((self.posX, self.posY, self.posZ))

    def draw(self):

        glColor4f(self.red, self.green, self.blue,self.alpha)
        #gluQuadricDrawStyle(self.q,GLU_LINE)
        gluQuadricDrawStyle(self.q,GLU_FILL)
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

    def gen_books(self, p1, p2, orientation, color):
        orientation_axis = {'h':'x', 'v':'z', 'a':'y'}
        books = []
        orientation = orientation_axis[orientation]
        param1 = p1.__getattribute__(orientation)
        param2 = p2.__getattribute__(orientation)
        f1,f2 =  set(['x', 'y', 'z']) - set([orientation])
        local = {}
        local[f1] = p1.__getattribute__(f1) * (self.beta + self.alfa)
        local[f2] = p1.__getattribute__(f2) * (self.beta + self.alfa)
        for pos in range(min(param1, param2), max(param1, param2) + 1):
            local[orientation] = pos * (self.beta + self.alfa)
            books.append(Sphere(color = color, pos = (local['x'], local['y'], local['z']), radius = 2))
        return books

    def generate(self):
        for plane in self.graph.get_planes():
            if plane.orientation == 'h':
                color_limit = (0.0, 0.0, 1.0, 1.0)
                color_book  = (0.0, 1.0, 1.0, 0.0)
            else:
                color_limit = (0.0, 0.8, 0.0, 1.0)
                color_book  = (1.0, 0.8, 0.0, 0.0)

            for p1,p2, orientation in plane.get_edges():
                plane.walls += self.gen_walls(p1, p2, orientation, plane.orientation, color_limit)
                plane.books += self.gen_books(p1, p2, orientation, color_book)
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
        glClearColor(1, 1, 1, 1)
        glColor3f(1, 0, 0)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_CULL_FACE)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable (GL_LINE_SMOOTH)
        self.batch = pyglet.graphics.Batch()
        self.size = 8
        self.monster = Sphere(color=(1.0, 0.0, 0.1, 1.0), pos=(24.0,-12.0,0.0), radius = self.size / 2)
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
        self.perspective = False
        self.alfa = 10
        self.beta = 2
        self.gridSize = 10
        self.change = (self.alfa - self.size) / 2
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

        self.grid_monster = self.pos_to_grid(self.monster)
        self.active_plane_type = 'h'
        self.active_plane = 0
        self.set_plane_opacity(self.map.graph.planes['h'][0], 1.0)

        # Uncomment this line for a wireframe view
        # glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)

    def set_plane_opacity(self, plane, opacity):
        for wall in plane.walls:
            wall.vertex_list.colors = (wall.vertex_list.colors[:3] + [opacity]) * 36

        for book in plane.books:
            book.alpha = opacity

    def pos_to_grid(self, obj):
        x = self.axis_to_grid(obj.posX)
        y = self.axis_to_grid(obj.posY)
        z = self.axis_to_grid(obj.posZ)
        return [x, y, z]

    def axis_to_grid(self, pos):
        ''' Get a float position and return de coordinate number in the grid'''
        if pos == 0:
            return 0
        shift = self.alfa / 2 + self.beta / 2
        if abs(pos) < shift:
            x = 0
        else:
            x = self.get_units(abs(pos) - shift, self.alfa + self.beta)
        return int(x * (pos / abs(pos)))

    def grid_to_axis(self, grid):
        ''' Get an int of coordinate grid and return de float position'''
        return grid * (self.alfa + self.beta)

    def get_units(self, a, b):
        r = int(a / b)
        if a % b > 0:
            r += 1
        return r

    def update(self, dt):
        self.monster.moveForward()
        if self.colliding(self.monster, self.walls) != None:
            self.monster.moveBack()
            self.monster.stop()

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

        if self.total_books == self.eaten_books:
            self.label.text = "Winner!!"

        ref = self.grid_to_axis(self.active_plane)
        #print self.pos_to_grid(self.monster), self.monster.posX, self.monster.posY, self.monster.posZ, candidate, self.active_plane, ref

        candidate = None
        if self.active_plane_type == 'h':
            for key in self.map.graph.planes['v'].keys():
                ref2 = self.grid_to_axis(key)
                if self.monster.posY + self.change >= ref2 and self.monster.posY - self.change <= ref2:
                    candidate = key
                    self.set_plane_opacity(self.map.graph.planes['v'][candidate], 0.5)
                else:
                    self.set_plane_opacity(self.map.graph.planes['v'][key], 0.1)
            if not (self.monster.posZ + self.change >= ref and self.monster.posZ - self.change <= ref):
                if candidate != None:
                    self.set_plane_opacity(self.map.graph.planes['v'][candidate], 1.0)
                    self.set_plane_opacity(self.map.graph.planes['h'][self.active_plane], 0.1)
                    self.active_plane = candidate
                    self.active_plane_type = 'v'
                else:
                    self.monster.moveBack()
                    self.monster.stop()

        elif self.active_plane_type == 'v':
            for key in self.map.graph.planes['h'].keys():
                ref2 = self.grid_to_axis(key)
                if self.monster.posZ + self.change >= ref2 and self.monster.posZ - self.change <= ref2:
                    candidate = key
                    self.set_plane_opacity(self.map.graph.planes['h'][candidate], 0.5)
                else:
                    self.set_plane_opacity(self.map.graph.planes['h'][key], 0.1)
            if not (self.monster.posY + self.change >= ref and self.monster.posY - self.change <= ref):
                if candidate != None:
                    self.set_plane_opacity(self.map.graph.planes['h'][candidate], 1.0)
                    self.set_plane_opacity(self.map.graph.planes['v'][self.active_plane], 0.1)
                    self.active_plane = candidate
                    self.active_plane_type = 'h'
                else:
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
        for plane in self.map.graph.get_planes():
            for book in plane.books:
                book.draw()
    
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
                return object2
        return None

if __name__ == '__main__':
    win = Board()
    pyglet.clock.schedule_interval(win.update, 0.033)
    pyglet.app.run()
