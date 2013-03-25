import pyglet
import re
import random
import os
from pyglet.gl import *
from pyglet.window import key
from random import choice
from copy import copy, deepcopy
from event import Event
from grid import *
from config import *
from collections import defaultdict


class _Nodes(dict):

    def __getitem__(self, item):
        assert isinstance(item, Point)
        item = Vertex(*item.getAxes())
        return self.setdefault(item, item)


class _DictList(dict):

    def __setitem__(self, index, val):
        l = []
        l += val
        dict.__setitem__(self, index, l)

    def __getitem__(self, index):
        return self.setdefault(index, [])

    def __add__(self, other):
        edges = deepcopy(self)
        for key, val in other.listing():
            edges[key] += val
        return edges

    def listing(self):
        l = []
        for key, vals in self.items():
            for val in vals:
                l.append((key, val))
        return l


class Graph(object):
    def __init__(self):
        self.edge = _DictList()
        self._edge = _DictList()
        self.node = _Nodes()

    def __repr__(self):
        string = 'Vertices:\n'
        for v in self.node:
            string += '\t' + str(v) + '\n'
        return string

    def add_edge(self, a, b):
        a = self.node[a]
        b = self.node[b]
        a.syncLimits(b)
        self.edge[a] += b
        self._edge[b] += a

    def get_all_relations(self):
        if not hasattr(self, 'global_edge'):
            self.global_edge = self.edge + self._edge
        return self.global_edge

    def load_points(self, points):
        if len(points) % 6 != 0:
            raise ValueError('The number of reference most be multiple of 6')
        while points != []:
            p1 = Vertex(points.pop(0), points.pop(0), points.pop(0))
            p2 = Vertex(points.pop(0), points.pop(0), points.pop(0))
            self.add_edge(p1, p2)

    def get_edges(self):
        return self.edge.listing()

    def get_neighbors(self, vertex):
        return (self.edge + self._edge)[vertex]


class Map(Graph):

    edge_plane = {
        'x': 'yz',
        'y': 'z',
        'z': 'y',
    }

    def __init__(self):
        super(Map, self).__init__()
        self.plane = defaultdict(Plane)

    def gen_planes(self):

        for key, value in self.edge.listing():
            eaxis = key.getOrientation(value)
            paxes = self.edge_plane[eaxis]
            for paxis in paxes:
                num = getattr(key, paxis)
                name = paxis + str(num)
                self.plane[name].add_edge(key, value)
                self.plane[name].axis = paxis
                self.plane[name].num = num

        blackList = []
        for name, plane in self.plane.items():
            if len(plane.node) > 2:
                for vertex in plane.node.values():
                    vertex = self.node[vertex]
                    setattr(vertex.plane, plane.axis, plane.num)
            else:
                blackList.append(name)

        for name in blackList:
            del self.plane[name]

    def get_planes(self):
        return self.plane.values()

    def load_points(self, points):
        super(Map, self).load_points(points)
        self.gen_planes()


class Plane(Graph):

    def __init__(self):
        super(Plane, self).__init__()
        self.walls = []
        self.books = []
        self.axis = None
        self.num = None

    def __repr__(self):
        string = 'Axis:\t' + str(self.axis) + '\n'
        string += 'Num:\t' + str(self.num) + '\n'
        string += super(Plane, self).__repr__()
        return string


class Map3D(Config):

    def __init__(self, batch, points):
        super(Map3D, self).__init__()
        self.batch = batch
        self.graph = Map()
        self.graph.load_points(points)
        self.objects = []
        self.books = []
        self.generate()

    def draw_grid(self):
        glBegin(GL_LINES)
        glColor3f(0.0, 0.0, 0.0)
        end = self.unit * self.gridSize + self.alfa / 2
        step = self.alfa + self.beta
        for i in range(0, self.gridSize * 2 + 2):
            glVertex3i(end - i * step, -end - self.beta, 0)
            glVertex3i(end - i * step,  end + self.beta, 0)
            glVertex3i(end - i * step + self.beta, -end - self.beta, 0)
            glVertex3i(end - i * step + self.beta,  end + self.beta, 0)

            glVertex3i(-end - self.beta, end - i * step, 0)
            glVertex3i(end + self.beta, end - i * step, 0)
            glVertex3i(-end - self.beta, end - i * step + self.beta, 0)
            glVertex3i(end + self.beta, end - i * step + self.beta, 0)
        glEnd()

    def gen_walls(self, p1, p2, plane_axis, color):
        a = self.alfa
        b = self.beta
        edge_axis = p1.getOrientation(p2)
        prm2 = getattr(p1, edge_axis)
        prm1 = getattr(p2, edge_axis)
        shift = (a + b) / 2 if (abs(prm1 - prm2) - 1) % 2 == 0 else 0
        c = (abs(prm1 - prm2) - 1) * (a + b) + b
        m = min(prm1, prm2) * (a + b) + abs(prm1 - prm2) / 2 * (a + b) + shift
        relation = {
            'z': {
                 'x': [c, b, a / 4,  'm', 'vy', 'fz'],
                 'y': [b, c, a / 4, 'vx',  'm', 'fz'],
                 },
            'y': {
                 'z': [b, a / 4, c, 'vx', 'fy',  'm'],
                 'x': [c, a / 4, b,  'm', 'fy', 'vz'],
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

        width = relation[plane_axis][edge_axis][0]
        height = relation[plane_axis][edge_axis][1]
        thickness = relation[plane_axis][edge_axis][2]
        x1, x2 = extract(relation[plane_axis][edge_axis][3])
        y1, y2 = extract(relation[plane_axis][edge_axis][4])
        z1, z2 = extract(relation[plane_axis][edge_axis][5])
        b1 = copy(self.originalBox)
        b1.setAxes(Point(x1, y1, z1))
        b1.color = color
        b1.setScale(width, height, thickness)
        b1.activate()

        b2 = copy(self.originalBox)
        b2.setAxes(Point(x2, y2, z2))
        b2.color = color
        b2.setScale(width, height, thickness)
        b2.activate()
        #b1 = Box(width, height, thickness, color=color, pos=(x1, y1, z1))
        #b2 = Box(width, height, thickness, color=color, pos=(x2, y2, z2))
        return (b1, b2)

    def gen_limits(self, point, plane_axis, color):
        w = self.alfa + self.beta * 2
        t = self.beta
        h = self.alfa / 2
        rel = {
            'n': [w, t, h, 'y',  1],
            's': [w, t, h, 'y', -1],
            'e': [t, w, h, 'x',  1],
            'w': [t, w, h, 'x', -1],
            'u': [w, h, t, 'z',  1],
            'd': [w, h, t, 'z', -1],
            }
        boxes = []
        if plane_axis == 'z':
            limits = 'nsew'
        else:
            limits = 'ewud'
            rel['e'] = [t, h, w, 'x',  1]
            rel['w'] = [t, h, w, 'x', -1]
        for attrib in limits:
            if getattr(point, attrib):
                local = {}
                w = rel[attrib][0]  # width
                h = rel[attrib][1]  # height
                t = rel[attrib][2]  # thickness
                for axis in 'xyz':
                    local[axis] = getattr(point, axis) * (self.unit)
                local[rel[attrib][3]] += (self.unit) / 2 * rel[attrib][4]
                pos = (local['x'], local['y'], local['z'])
                currentBox = copy(self.originalBox)
                currentBox.setAxes(Point(*pos))
                currentBox.color = color
                currentBox.setScale(w, h, t)
                currentBox.activate()
                boxes.append(currentBox)
        return boxes

    def gen_books(self, p1, p2, color):
        books = []
        for point in p1.range(p2):
            currentBook = copy(self.originalBook)
            currentBook.setAxes(Point(*currentBook.translatePos(point)))
            currentBook.color = color
            currentBook.activate()
            books.append(currentBook)
        return books

    def generate(self):
        self.originalBox = Box(1, 1, 1)
        self.originalBook = StaticObject(model_name='sphere', scale=4)
        for plane in self.graph.plane.values():
            if plane.axis == 'z':
                color_limit = (0.0, 0.0, 1.0, 1.0)
                color_book = (0.0, 1.0, 1.0, 1.0)
            else:
                color_limit = (0.0, 0.8, 0.0, 1.0)
                color_book = (1.0, 0.8, 0.0, 1.0)

            for p1, p2 in plane.get_edges():
                plane.walls += self.gen_walls(p1, p2, plane.axis, color_limit)
                plane.books += self.gen_books(p1, p2, color_book)
            plane.books = set(plane.books)

            for point in plane.node.values():
                plane.walls += self.gen_limits(point, plane.axis, color_limit)


class Board(pyglet.window.Window):

    def __init__(self):
        pyglet.window.Window.__init__(self, resizable=True)
        self.eye = [-9.0, -10.0, 10.0]
        self.focus = [0.0, 0.0, 0.0]
        self.up = [0.0, 0.0, 1.0]
        self.width = 1024
        self.height = 1024
        self.curParam = self.eye
        self.step = 10.0
        #One-time GL setup
        glClearColor(1, 1, 1, 1)
        glColor3f(1, 0, 0)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_CULL_FACE)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_LINE_SMOOTH)
        glShadeModel(GL_SMOOTH)

        def vec(*args):
            return (GLfloat * len(args))(*args)
        #glEnable(GL_LIGHTING)
        self.lights = False
        glEnable(GL_LIGHT0)
        glLightfv(GL_LIGHT0, GL_POSITION, vec(-150, -150, 150, 0))
        glLightfv(GL_LIGHT0, GL_SPECULAR, vec(.5, .5, .5, .5))
        glLightfv(GL_LIGHT0, GL_DIFFUSE, vec(0.1, 0.1, .1, 1.0))

        self.batch = StaticObj.batch
        self.perspective = False
        self.size = 8

        self.gen_axes()

        self.alpha = 0.0
        self.label_batch = pyglet.graphics.Batch()
        self.label = pyglet.text.Label('0',
                                       font_name='White Rabbit',
                                       font_size=16,
                                       x=0,
                                       y=0,
                                       batch=self.label_batch,
                                       color=(0, 255, 255, 255))
        self.gconf = Config()  # Config file values
        self.pattern = re.compile(r'\s+')
        self.maps = os.listdir('data/maps')
        self.total_books = 0
        self.eaten_books = 0
        self.first_update = True

        self.getMap()

        self.active_plane = 'z0'
        self.altPlane = None

        #self.susan = StaticObj('susan', 20, pos=(-50.0, -50.0, 0.0))
        self.susan = StaticObj('susan', 20)
        self.susan.setAxes(Point(-50.0, -50.0, 0.0))
        self.susan.activate()
        '''for badguy in self.badGuys:
            self.setBadGuyStep(badguy)
            badguy.noMoreTarget = self.setBadGuyStep'''
        media = pyglet.resource.media
        self.pick = media('data/sound/get.wav', streaming=False)
        self.win = media('data/sound/win.wav', streaming=False)
        self.go = media('data/sound/game-over.wav', streaming=False)
        # Uncomment this line for a wireframe view
        # glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)

    def getMap(self, *args):
        currentmap = self.maps.pop(0)
        self.map = Map3D(self.batch, self.loadMap(currentmap))
        self.walls = []
        self.pause = True
        self.over = False
        self.label.text = 'Move you to start'
        for plane in self.map.graph.get_planes():
            self.walls += plane.walls
            self.total_books += len(plane.books)
            self.set_plane_opacity(plane, 0.1)
        self.allrel = self.map.graph.get_all_relations()
        self.set_plane_opacity(self.map.graph.plane['z0'], 1.0)
        monsterp, fartherp = self.getPlaneCorners(self.map.graph.plane['z0'])
        self.monster = HumanObject(
                self.allrel, monsterp, model_name='sphere', scale=self.size,
                color=(1.0, 0.0, 0.1, 1.0))
        self.monster.speed.onChange += self.resetBadGuysStep
        self.monster.onProxGridChange += self.updatePlane
        countBooks = 0
        for plane in self.map.graph.get_planes():
            countBooks += len(plane.books)

        self.badGuys = []
        for i in range(countBooks / 100):
            plane = random.choice(self.map.graph.plane.keys())
            print('Planex', plane)
            closerp, fartherp = self.getPlaneCorners(self.map.graph.plane[plane], monsterp)
            badGuy = RobotObject(
                    self.allrel, fartherp, model_name='bad', scale=3.0,
                    color=(1.0, 0.0, 0.0, 1.0))
            self.badGuys.append(badGuy)
            self.setBadGuyStep(badGuy)
            badGuy.noMoreTarget = self.setBadGuyStep


    def getPlaneCorners(self, plane, origin = Point()):
        closerp = plane.node[plane.node.keys()[0]]
        closerd = origin.distance(closerp)
        fartherp = plane.node[plane.node.keys()[0]]
        fartherd = origin.distance(fartherp)
        for node in plane.node:
            distance = origin.distance(node)
            print('meter', origin, node, distance)
            if distance < closerd:
                closerd = distance
                closerp = node
            if distance > fartherd:
                fartherd = distance
                fartherp = node
        return closerp, fartherp

    def updatePlane(self):
        g = self.map.graph
        plane = self.monster.proxGrid.plane
        print('Proxplane', plane)
        values = []
        for axis in plane.axes:
            num = getattr(plane, axis)
            if num != None:
                values.append(axis + str(num))
        print values
        if len(values) > 1:
            values.remove(self.active_plane)
            self.altPlane = values[0]
            self.set_plane_opacity(g.plane[self.altPlane], 0.4)
        elif self.altPlane != None:
            if self.monster.speed.axis != 'x':
                if self.monster.speed.axis == self.active_plane[0]:
                    self.set_plane_opacity(g.plane[self.active_plane], 0.1)
                    self.set_plane_opacity(g.plane[self.altPlane], 1.0)
                    self.active_plane = self.altPlane
                else:
                    self.set_plane_opacity(g.plane[self.altPlane], 0.1)
                self.altPlane = None

    def loadMap(self, filename):
        filemap = open(self.gconf.mapsdir + filename)
        pattern = re.compile(r'\s+')
        data = filemap.read()
        data = re.sub(pattern, '', data)
        if data[-1] == ',':
            data = data[:-1]
        return [int(n) for n in data.split(',')]

    def resetBadGuysStep(self):
        for badguy in self.badGuys:
            badguy.path = []

    def set_plane_opacity(self, plane, opacity):
        for wall in plane.walls:
            wall.setOpacity(opacity)

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
        edges = deepcopy(self.allrel)
        print edges
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
            sons = edges[current]
            for son in sons:
                if not son in visited and not son in frontier:
                    son.parent = current
                    frontier.append(son)
        raise ValueError("Path no found")

    def update(self, dt):

        if self.pause == False:
            self.monster.moveForward()
            self.monster.updateGrids()

            for badGuy in self.badGuys:
                badGuy.moveForward()
                badGuy.updateGrids()

            for plane in self.map.graph.get_planes():
                book = self.colliding(self.monster, plane.books)
                if book != None:
                    plane.books.remove(book)
                    self.pick.play()
                    self.eaten_books += 1
                    self.label.text = str(self.eaten_books * 100)
                    break
            badguy = self.colliding(self.monster, self.badGuys)
            if badguy != None:
                self.pause = True
                self.over = True
                self.label.text = 'GAME OVER'
                self.label.color = (255,0,0,255)
                self.go.play()

        if self.first_update:
            self.eaten_books -= 1
            self.total_books -= 1
            self.first_update = False

        if self.total_books == self.eaten_books and not self.pause:
            if len(self.maps) < 1:
                self.label.text = 'Game completed'
            else:
                self.label.text = 'Winner!!'
                pyglet.clock.schedule_once(self.getMap, 3)
            self.pause = True
            self.win.play()

    def gen_axes(self):
        glLineWidth(2)

        vertex_list = self.batch.add(6, GL_LINES, None,
            ('v3f/stream', (0, 0, 0,  100, 0, 0,
                            0, 0, 0,  0, 100, 0,
                            0, 0, 0,  0, 0, 100)
            ),
            ('c4B/stream', (255, 0, 0, 255,  255, 0, 0, 255,
                            0, 255, 0, 255,  0, 255, 0, 255,
                            0, 0, 255, 255,  0, 0, 255, 255)
            )
        )

        glLineWidth(1)

    def on_draw(self):
        # Clear buffers
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        # Draw Grid
        self.map.draw_grid()

        glPushMatrix()
        glTranslatef(-100, 100, 160)
        glRotatef(90, 1, 0, 0)
        glRotatef(-45, 0, 1, 0)
        self.label_batch.draw()
        glPopMatrix()

        self.batch.draw()
        self.monster.draw_faces()
        [guy.draw_faces() for guy in self.badGuys]

    def on_resize(self, width, height):
        glViewport(0, 0, self.width, self.height)
        glMatrixMode(GL_PROJECTION)
        self.initView()
        return pyglet.event.EVENT_HANDLED

    def initView(self):
        glLoadIdentity()
        if self.perspective:
            gluPerspective(
                90.0,                                    # Field Of View
                float(self.width) / float(self.height),  # aspect ratio
                1.0,                                     # z near
                1000.0)                                  # z far
        else:
            glOrtho(-150, 150, -150, 150, -300, 300)
        gluLookAt(*(self.eye + self.focus + self.up))

    def on_key_press(self, symbol, modifiers):
        glLoadIdentity()
        if symbol == key.P:
            #self.perspective = not self.perspective
            self.label.text = 'Move you to resume'
            self.pause = True
        elif symbol == key.O:
            if self.lights:
                self.lights = False
                glDisable(GL_LIGHTING)
            else:
                self.lights = True
                glEnable(GL_LIGHTING)
        elif symbol == key.X:
            self.curParam = self.eye
            self.step = 10.0
        elif symbol == key.Y:
            self.curParam = self.focus
            self.step = 10.0
        elif symbol == key.Z:
            self.step = 0.1
            self.curParam = self.up
        elif symbol == key.NUM_7:
            self.curParam[0] = round(self.curParam[0] + self.step, 1)
        elif symbol == key.NUM_8:
            self.curParam[1] = round(self.curParam[1] + self.step, 1)
        elif symbol == key.NUM_9:
            self.curParam[2] = round(self.curParam[2] + self.step, 1)
        elif symbol == key.NUM_1:
            self.curParam[0] = round(self.curParam[0] - self.step, 1)
        elif symbol == key.NUM_2:
            self.curParam[1] = round(self.curParam[1] - self.step, 1)
        elif symbol == key.NUM_3:
            self.curParam[2] = round(self.curParam[2] - self.step, 1)
        elif symbol in [key.RIGHT, key.L, key.F] and not self.over:
            self.pause = False
            self.monster.setDirection('e')
        elif symbol in [key.LEFT, key.J, key.S] and not self.over:
            self.pause = False
            self.monster.setDirection('w')
        elif symbol in [key.UP, key.I] and not self.over:
            self.pause = False
            self.monster.setDirection('n')
        elif symbol in [key.DOWN, key.K] and not self.over:
            self.pause = False
            self.monster.setDirection('s')
        elif symbol == key.E and not self.over:
            self.pause = False
            self.monster.setDirection('u')
        elif symbol == key.D and not self.over:
            self.pause = False
            self.monster.setDirection('d')

        self.initView()
        return pyglet.event.EVENT_HANDLED

    def colliding(self, object1, objectList):
        for object2 in objectList:
            minDistanceX = object1.width / 2 + object2.width / 2
            minDistanceY = object1.height / 2 + object2.height / 2
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
