#!/bin/python3
import sys
import math
import cmath
from grid import *
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.QtOpenGL import *

from OpenGL.raw import GL


def vec(*args):
    return (GLfloat * len(args))(*args)


class MainWindow(QMainWindow):

    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent)
        self.gl = GLWidget()

        gp = QGridLayout()
        #gp.addWidget(self.pause, 1, 0)
        #gp.addWidget(self.fade, 1, 1)
        gp.addWidget(self.gl, 0, 0, 1, 2)
        self.frame = QWidget()
        self.frame.setLayout(gp)
        self.setCentralWidget(self.frame)

    def keyPressEvent(self, event):
        print event
        if event.key() == Qt.Key_X:
            self.gl.changeX = not self.gl.changeX
            print self.gl.changeX


class GLWidget(QGLWidget):

    def __init__(self, parent=None):
        QGLWidget.__init__(self, parent)
        self.timer = QTimer()
        self.timer.timeout.connect(self.updateGL)
        self.timer.start(33)
        self.x = -200
        self.y = -200
        self.z = 200
        self.mouseX = 0
        self.mouseY = 0
        self.dx = -45
        self.dy = 0
        self.changeX = True

    def draw(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        self.setup3D(self.w, self.h)
        self.draw_3D()
        self.setup2D(self.w, self.h)
        self.draw_2D()
        glFlush()

    def initializeGL(self):
        glDisable(GL_TEXTURE_2D)
        glDisable(GL_COLOR_MATERIAL)
        '''glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)'''
        glEnable(GL_DEPTH_TEST)
        glClearColor(0.2, 0.2, 0.2, 1)
        '''glEnable(GL_POLYGON_SMOOTH)
        glShadeModel(GL_SMOOTH)
        glHint(GL_LINE_SMOOTH_HINT, GL_DONT_CARE)'''
        # Load models
        self.model = StaticObject(model_name='monkeyMat', scale=30)
        self.model2 = StaticObject(model_name='book', grid=Point(2,2,2), scale=30)
        # Materials
        glMaterialfv(GL_FRONT, GL_SHININESS, vec(5.0))
        # Light zone
        glLightfv(GL_LIGHT0, GL_AMBIENT, vec(100.0, 10.0, 10.0, 10.0))
        glLightfv(GL_LIGHT0, GL_DIFFUSE, vec(10.0, 10.0, 10.0, 10.0))
        glLightfv(GL_LIGHT0, GL_POSITION, vec(-300, -300, 0.0, 0))
        glLightfv(GL_LIGHT0, GL_SPOT_DIRECTION, vec(0.5, 0.5, 0.0))
        glLightfv(GL_LIGHT0, GL_SPECULAR, vec(0.5, 0.5, 0.5, 1.0))
        glEnable(GL_LIGHT0)

    def resizeGL(self, w, h):
        glViewport(0, 0, w, h)
        self.w = w
        self.h = h

    def setup3D(self, w, h):
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45., w / float(h), 1.0, 1000.0)
        gluLookAt(self.x, self.y, self.z, 0, 0, 0, 0, 0, 1)
        '''vx = math.sin(math.radians(self.dx -45))
        vy = math.cos(math.radians(self.dx -45))
        glRotatef(self.dy, vx, vy, 0)
        print (vx,vy, self.dx, self.dy)
        glRotatef(self.dx, 0, 0, 1)'''
        glRotatef(self.dx, 0, 0, 1)
        vx = math.sin(math.radians(self.dx -45))
        vy = math.cos(math.radians(self.dx -45))
        glRotatef(self.dy, vx, vy, 0)
        print (vx,vy, self.dx, self.dy)

        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glEnable(GL_LIGHTING)

    def setup2D(self, w, h):
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluOrtho2D(0, w, 0, h)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glDisable(GL_LIGHTING)

    def updateGL(self):
        self.glDraw()

    def paintGL(self):
        self.draw()

    def mouseMoveEvent(self, event):
        dx = self.mouseX - event.x()
        dy = self.mouseY - event.y()
        self.mouseX = event.x()
        self.mouseY = event.y()
        if self.changeX:
            self.dx -= dx
        else:
            self.dy -= dy

    def mousePressEvent(self, event):
        self.mouseX = event.x()
        self.mouseY = event.y()

    def draw_2D(self):
        pass

    def draw_3D(self):
        self.model.draw_faces()
        self.model2.draw_faces()
        glMaterialfv(GL_FRONT, GL_DIFFUSE, vec(0.0, 0.1, 0.0, 1.0))
        pass

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    window.resize(400, 400)
    app.exec_()

# vim: ts=4 et sw=4 st=4 list
