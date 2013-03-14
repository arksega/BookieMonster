from pyglet.gl import *
from pyglet.graphics import Batch
from operator import add, sub, mul, methodcaller
from point import *
from config import *


class Object3D(Point):

    def __init__(self, width, height, thickness, \
            color=(0.0, 0.0, 0.0, 1.0), pos=(0, 0, 0)):
        super(Object3D, self).__init__(*pos)
        self.color = color
        self.width = width
        self.height = height
        self.thickness = thickness


class Importer(Object3D):

    conf = Config()

    def __init__(self, model_name, scale, *args, **kwargs):
        '''Should initialize the bach before call this member'''
        if args != ():
            super(Importer, self).__init__(scale, args[0], args[1], **kwargs)
            self.height = args[0]
            self.thickness = args[1]
        else:
            super(Importer, self).__init__(scale, scale, scale, **kwargs)
            self.height = scale
            self.thickness = scale
        self.scale = scale
        self.load_file(model_name)
        self.model_name = model_name

    def __del__(self):
        self.vtx_list.delete()

    def load_file(self, model_name):
        self.vertices = []
        self.faces = {}
        self.normals = []
        model_file = open(self.conf.modelsdir + model_name + '.obj')
        f = 0
        self.useMaterials = False
        zone = 'main'
        for line in model_file.readlines():
            if line[0:2] == 'v ':
                self.vertices += [float(x) for x in line[2:].split()]
            elif line[0:2] == 'vn':
                self.normals += [float(x) for x in line[2:].split()]
            elif line[0:2] == 'f ':
                self.faces[zone] = self.faces.get(zone, []) + [x for x in line[2:].split()]
                f += 1
            elif line.startswith('usemtl'):
                zone = line.split()[1]
                self.useMaterials = True
        model_file.close()



class DinamicObj(Importer):

    def __init__(self, *args, **kwargs):
        self.batch = Batch()
        super(DinamicObj, self).__init__(*args, **kwargs)

    def draw_faces(self):
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glScalef(self.scale, self.height, self.thickness)
        self.batch.draw()
        glPopMatrix()


class StaticObj(Importer):

    batch = Batch()

    def __init__(self, *args, **kwargs):
        super(StaticObj, self).__init__(*args, **kwargs)
        real_vertices = []
        real_normals = []
        if not self.faces.has_key('main'):
            print self.model_name
            exit(1)
        for vertex in self.faces['main']:
            vertex, normal = [int(n) for n in vertex.split('//')]
            vertex -= 1
            normal -= 1
            for n in range(3):
                real_vertices.append(self.vertices[vertex * 3 + n])
                real_normals.append(self.normals[normal * 3 + n])
        self.vertices = real_vertices
        self.normals = real_normals
        print self.model_name
        #print self.vertices, self.normals, self.colors
        #print len(self.vertices), len(self.normals), len(self.colors), len(self.faces['main'])

    def activate(self):
        self.colors = self.color * (len(self.faces['main']))
        self.vtx_list = self.batch.add(
                len(self.faces['main']), GL_TRIANGLES, None,
                ('v3f', self.vertices), ('n3f', self.normals), ('c4f', self.colors))
        self.__setScale()
        self.__setPos()

    def setScale(self, w, h, t):
       self.scale = w
       self.height = h
       self.thickness = t

    def __setScale(self):
        self.__setTransform(mul, (self.scale, self.height, self.thickness))

    def __setPos(self):
        self.__setTransform(add, (self.x, self.y, self.z))

    def __setTransform(self, operator, vector):
        tmp_vertices = []
        for vertex in zip(*[self.vtx_list.vertices[x::3] for x in range(3)]):
            tmp_vertices += [operator(*pair) for pair in zip(vertex, vector)]
        self.vtx_list.vertices = tmp_vertices

    def setOpacity(self, opacity):
        self.vtx_list.colors = (
                self.vtx_list.colors[:3] + [opacity]) * len(self.faces['main'])


class Box(StaticObj):

    def __init__(self, width, height, thickness, **kwargs):
        super(Box, self).__init__('box', width, height, thickness, **kwargs)


class GridObj(object):

    def translatePos(self, grid):
        if not isinstance(grid, Point):
            raise ValueError('grid parameter should be Point instance')
        self.alfa = self.conf.alfa
        self.beta = self.conf.beta
        self.unit = self.conf.unit
        pos = [x * self.unit for x in grid.getAxes()]
        self.grid = deepcopy(grid)
        return pos


class StaticObject(StaticObj, GridObj):

    def __init__(self, grid=Point(), **kwargs):
        super(StaticObject, self).__init__(kwargs.pop('model_name'), \
                                        kwargs.pop('scale'), \
                                        pos=self.translatePos(grid), **kwargs)


class MobileObject(DinamicObj, GridObj):

    pendingAction = None
    connections = None

    def __init__(self, vertices, grid=Point(), **kwargs):
        assert isinstance(vertices, dict)
        super(MobileObject, self).__init__(kwargs.pop('model_name'), \
                                        kwargs.pop('scale'), \
                                        pos=self.translatePos(grid), **kwargs)
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
            pos = getattr(self, axis)
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
            val = self.direction_speed[direction][1]
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
