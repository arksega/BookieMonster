from copy import copy, deepcopy
from event import Event


class Point(object):

    axes = ['x', 'y', 'z']

    def __init__(self, x=0, y=0, z=0):
        self.x = x
        self.y = y
        self.z = z

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y and self.z == other.z

    def __ne__(self, other):
        if isinstance(other, Point):
            return not self.__eq__(other)
        return True

    def __str__(self):
        return 'Point' + repr((self.x, self.y, self.z))

    def __repr__(self):
        return 'Point' + repr((self.x, self.y, self.z))

    def __hash__(self):
        return self.x * 100 + self.y * 10 + self.z

    def __sub__(self, other):
        tot = 0
        for axis in self.axes:
            tot += abs(getattr(self, axis) - getattr(other, axis))
        return tot

    def __iter__(self):
        return iter([self])

    def isAligned(self, other):
        return len(self.getCommonAxes(other)) == 2

    def getOrientation(self, other):
        assert isinstance(other, Point)
        axes = self.getDifferentAxes(other)
        if len(axes) == 1:
            return self.getDifferentAxes(other)[0]
        raise ValueError('Points not aligned', self, other)

    def _difference(self, other):
        axis = self.getOrientation(other)
        minVal, maxVal = sorted([getattr(self, axis), getattr(other, axis)])
        return axis, minVal, maxVal

    def isBetween(self, other1, other2):
        axis, minVal, maxVal = other1._difference(other2)
        selfVal = self.__getattribute__(axis)
        return minVal <= selfVal and maxVal >= selfVal

    def getCommonAxes(self, other):
        axes = []
        for axis in self.axes:
            if getattr(self, axis) == getattr(other, axis):
                axes.append(axis)
        return axes

    def getDifferentAxes(self, other):
        common = self.getCommonAxes(other)
        return self.getComplementaryAxes(common)

    def getComplementaryAxes(self, axesList):
        return list(set(self.axes).difference(set(axesList)))

    def mask(self, axis, val):
        p = deepcopy(self)
        setattr(p, axis, val)
        return p

    def getAxes(self):
        return [self.x, self.y, self.z]

    def setAxes(self, other):
        for axis in self.axes:
            setattr(self, axis, getattr(other, axis))

    def range(self, other):
        axis, minVal, maxVal = self._difference(other)
        points = []
        for val in range(minVal, maxVal + 1):
            points.append(self.mask(axis, val))
        return points

    def distance(self, other):
        distance = 0
        for axis in self.axes:
            distance += abs(getattr(self,axis) - getattr(other,axis))
        return distance


class Vertex(Point):

    axis_limits = {
        'x': 'ew',
        'y': 'ns',
        'z': 'ud',
    }

    direction_speed = {
        'n': ('y',  1),
        's': ('y', -1),
        'e': ('x',  1),
        'w': ('x', -1),
        'u': ('z',  1),
        'd': ('z', -1),
    }

    directions = ['e', 'w', 'n', 's', 'u', 'd']

    def __repr__(self):
        return 'Vertex' + repr((self.x, self.y, self.z, self.food))

    def __str__(self):
        return self.__repr__()

    def __init__(self, x=0, y=0, z=0):
        super(Vertex, self).__init__(x, y, z)
        self.n, self.s, self.e, self.w, self.u, self.d = [True] * 6
        self.plane = Point(None, None, None)
        self.food = True

    def disableLimits(self, axis):
        for limit in self.axis_limits[axis]:
            setattr(self, limit, False)

    def upLimits(self, limits=directions):
        for limit in limits:
            setattr(self, limit, True)

    def downLimits(self, limits=directions):
        for limit in limits:
            setattr(self, limit, False)

    def syncLimits(self, other):
        axis = self.getOrientation(other)
        vmin, vmax = self, other
        if getattr(self, axis) > getattr(other, axis):
            vmin, vmax = vmax, vmin
        for vertex, limit in zip((vmin, vmax), self.axis_limits[axis]):
            setattr(vertex, limit, False)

    def getValidDirections(self):
        valid = []
        for direction in self.directions:
            if not getattr(self, direction):
                valid.append(direction)
        return valid

    def range(self, other):
        points = Point.range(self, other)
        axis = self.getOrientation(other)
        [point.upLimits() for point in points]
        points[0].syncLimits(points[-1])
        for point in points[1:-1]:
            point.disableLimits(axis)
        return points

    def shift(self, direction):
        axis, shift = self.direction_speed[direction]
        return self.mask(axis, getattr(self, axis) + shift)


class Speed(Point):

    speed_direction = {
        ('y',  1): 'n',
        ('y', -1): 's',
        ('x',  1): 'e',
        ('x', -1): 'w',
        ('z',  1): 'u',
        ('z', -1): 'd',
    }

    def __init__(self, x=0, y=0, z=0):
        super(Speed, self).__init__(x, y, z)
        self.axis = None
        self.onChange = Event()

    def __repr__(self):
        return 'Speed' + repr((self.x, self.y, self.z))

    def set(self, axis, val):
        self.axis = axis
        p = Point()
        setattr(p, axis, val)
        self.setAxes(p)
        self.onChange()

    def getDirection(self):
        if self.axis != None:
            return self.speed_direction[(self.axis, getattr(self, self.axis))]
        return None

    direction = property(getDirection)
