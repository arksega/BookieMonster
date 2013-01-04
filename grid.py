from pyglet.gl import *
from pyglet.graphics import Batch
from operator import add, sub, methodcaller
from point import *


class Object3D(Point):

    def __init__(self, width, height, thickness, \
            color=(0.0, 0.0, 0.0, 1.0), pos=(0, 0, 0)):
        super(Object3D, self).__init__(*pos)
        self.red = color[0]
        self.green = color[1]
        self.blue = color[2]
        self.alpha = color[3]
        self.width = width
        self.height = height
        self.thickness = thickness


class ImportObj(Object3D):

    def __init__(self, file_name, scale, *args, **kwargs):
        if 'batch' in kwargs:
            self.batch = kwargs.pop('batch')
        if args != ():
            super(ImportObj, self).__init__(scale, args[0], args[1], **kwargs)
        else:
            super(ImportObj, self).__init__(scale, scale, scale, **kwargs)
        self.vertices = []
        self.faces = []
        self.normals = []
        self.scale = scale
        self.load_file(file_name)

    def load_file(self, file_name):
        if not hasattr(self, 'batch'):
            self.batch = Batch()
        file = open(file_name)
        f = 0
        for line in file.readlines():
            if line[0:2] == 'v ':
                self.vertices += [float(x) * self.scale for x in line[2:].split()]
            elif line[0:2] == 'vn':
                self.normals += [float(x) * self.scale for x in line[2:].split()]
            elif line[0:2] == 'f ':
                self.faces += [x for x in line[2:].split()]
                f += 1
        colors = (self.red, self.green, self.blue, self.alpha) * (len(self.vertices) / 3)
        self.vertices_vertex_list = pyglet.graphics.vertex_list(len(self.vertices) / 3,
                                                                ('v3f', self.vertices),
                                                                ('c4f', colors)
                                                                )
        real_faces = []
        real_normals = []
        for vertex in self.faces:
            vertex, normal = [int(n) for n in vertex.split('//')]
            vertex -= 1
            normal -= 1
            for n in range(3):
                real_faces.append(self.vertices[vertex * 3 + n])
                real_normals.append(self.normals[normal * 3 + n])
        colors = (self.red, self.green, self.blue, self.alpha) * (len(self.faces))
        self.faces_vertex_list = self.batch.add(len(self.faces), GL_TRIANGLES, None,
                                                                ('v3f', real_faces),
                                                                ('n3f', real_normals),
                                                                ('c4f', colors)
                                                                )

    def draw_points(self):
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        self.vertices_vertex_list.draw(GL_POINTS)
        glPopMatrix()

    def draw_faces(self):
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        self.batch.draw()
        glPopMatrix()

    def setOpacity(self, opacity):
        self.faces_vertex_list.colors = (self.faces_vertex_list.colors[:3] + [opacity]) * len(self.faces)


class Box(Object3D):

    def __init__(self, batch, width, height, thickness, **kwargs):
        super(Box, self).__init__(width, height, thickness, **kwargs)
        self.x1 = self.x + width / 2
        self.y1 = self.y + height / 2
        self.z1 = self.z + thickness / 2
        self.x2 = self.x - width / 2
        self.y2 = self.y - height / 2
        self.z2 = self.z - thickness / 2
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


class Grid(object):

    alfa = 10
    beta = 2
    unit = alfa + beta


class GridObject(ImportObj, Grid):

    def __init__(self, grid=Point(), **kwargs):
        if not isinstance(grid, Point):
            raise ValueError('grid parameter should be Point instance')
        pos = [x * self.unit for x in grid.getAxes()]
        super(GridObject, self).__init__(kwargs.pop('file_name'), \
                                        kwargs.pop('scale'), \
                                        pos=pos, **kwargs)
        self.grid = deepcopy(grid)


class MobileObject(GridObject):

    pendingAction = None
    connections = None

    def __init__(self, vertices, grid=Point(), **kwargs):
        assert isinstance(vertices, dict)
        super(MobileObject, self).__init__(grid, **kwargs)
        self.grid = deepcopy(grid)
        self.proxGrid = deepcopy(grid)
        self.origin = deepcopy(grid)
        self.speed = Speed()
        self.vertices = vertices
        self.updateConnections()

    def updateConnections(self):
        self.connections = self.vertices[self.origin] + [self.origin]

    def updateGrids(self):
        proxGrid = self.calcProxGrid()
        if self.proxGrid != proxGrid:
            self.updateProxGrid(proxGrid)
        elif self.isCentered() and self.grid != self.proxGrid:
            self.updateMainGrid(proxGrid)

    def updateMainGrid(self, grid):
        self.grid = deepcopy(self.proxGrid)
        if self.grid in self.connections:
            self.origin = deepcopy(self.proxGrid)
            self.updateConnections()
            self.updateOrigin()

    def updateOrigin(self):
        raise NotImplementedError

    def updateProxGrid(self, grid):
        if grid == self.grid:
            self.proxGrid = copy(self.grid)
        elif grid in self.connections:
            self.proxGrid = self.connections[self.connections.index(grid)]
        else:
            axis = self.grid.getOrientation(grid)
            grid.disableLimits(axis)
            self.proxGrid = grid

    def calcProxGrid(self):
        proxGrid = Vertex()
        for axis in self.axes:
            pos = getattr(self, axis)
            if pos == 0:
                setattr(proxGrid, axis, 0)
            else:
                sign = pos / abs(pos)
                pos = abs(pos)
                pos += self.unit / 2
                setattr(proxGrid, axis, int(pos / self.unit * sign))
        return proxGrid

    def isCentered(self):
        count = 0
        for axis in self.axes:
            pos = getattr(self, axis)
            count += pos % self.unit
        return count == 0

    def calcTarget(self):
        if self.speed.axis == None:
            return None
        for vertex in self.connections:
            try:
                if self.grid.isBetween(self.origin, vertex):
                    return vertex
            except:
                pass
        raise AttributeError('Target not found')

    def setTarget(self, target):
        axis = self.grid.getOrientation(target)
        targetVal = getattr(target, axis)
        _localVal = getattr(self.grid, axis)
        self.speed.set(axis, 1 if _localVal < targetVal else -1)
        self.origin = self.target

    target = property(calcTarget, setTarget)

    def moveForward(self):
        self.move(add)

    def moveBack(self):
        self.move(sub)

    def move(self, operator):
        for axis in self.speed.axes:
            pos   = getattr(self, axis)
            speed = getattr(self.speed, axis)
            setattr(self, axis, operator(pos, speed))

    def stop(self):
        for axis in self.speed.axes:
            setattr(self.speed, axis, 0)
        self.speed.axis = None


class HumanObject(MobileObject):

    direction_speed = {
        'e': ['x',  1],
        'w': ['x', -1],
        'n': ['y',  1],
        's': ['y', -1],
        'u': ['z',  1],
        'd': ['z', -1],
    }

    def __init__(self, vertices, grid=Point(), **kwargs):
        super(HumanObject, self).__init__(vertices, grid, **kwargs)
        self.onProxGridChange = Event()

    def updateOrigin(self):
        if self.pendingAction:
            self.speed.set(*self.pendingAction)
            self.pendingAction = None
        self.verifySpeed()

    def verifySpeed(self):
        if self.speed.direction and getattr(self.grid, self.speed.direction):
            self.stop()

    def setDirection(self, direction):
        if not getattr(self.proxGrid, direction):
            axis = self.direction_speed[direction][0]
            val  = self.direction_speed[direction][1]
            if self.speed.axis == None or self.speed.axis == axis:
                self.speed.set(axis, val)
            else:
                self.pendingAction = (axis, val)

    def updateProxGrid(self, grid):
        super(HumanObject, self).updateProxGrid(grid)
        self.onProxGridChange()


class RobotObject(MobileObject):

    def __init__(self, vertices, grid=Point(), **kwargs):
        super(RobotObject, self).__init__(vertices, grid, **kwargs)
        self.noMoreTarget = Event()

    def updateOrigin(self):
        if self.path != []:
            self.target = self.path.pop(0)
        else:
            self.noMoreTarget(self)
