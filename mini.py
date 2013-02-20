#!/bin/python3
import sys
import os
from grid import *
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.QtOpenGL import *
from pyglet.gl import *
import pyglet

def vec(*args):
    return (GLfloat * len(args))(*args)


class MainWindow(QMainWindow):
    
    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent)
        self.pause = QPushButton('Pausar')
        self.pause.setCheckable(True)
        self.pause.clicked.connect(self.pauseToggle)
        self.fade = QPushButton('Decolorar')
        self.fade.setCheckable(True)
        self.fade.setChecked(True)
        self.fade.clicked.connect(self.fadeToggle)
        self.gl = GLWidget()
        gp = QGridLayout()
        gp.addWidget(self.pause, 1, 0)
        gp.addWidget(self.fade, 1, 1)
        gp.addWidget(self.gl, 0, 0, 1, 2)
        self.frame = QWidget()
        self.frame.setLayout(gp)
        self.setCentralWidget(self.frame)

    def pauseToggle(self):
        self.gl.pause = not self.gl.pause

    def fadeToggle(self):
        self.gl.fade = not self.gl.fade

class GLWidget(QGLWidget):

    def __init__(self, parent=None):
        QGLWidget.__init__(self, parent)
        self.timer = QTimer()
        self.timer.timeout.connect(self.updateGL)
        self.timer.start(333)
        self.deltaY = 0
        self.deltaX = 0
        self.posX = 0
        self.posY = 0
        self.changeX = True
        self.pause = False
        self.fade = True
        pyglet.font.add_file('data/fonts/whitrabt.ttf')
        self.font_size = 32
        self.label = pyglet.text.Label(
                font_name='White Rabbit', 
                font_size=self.font_size, 
                color=(0, 255, 255, 255))

    def move(self):
        if self.posX == 0 and self.posY == 0:
            if self.changeX:
                self.deltaX, self.deltaY  = 0, 10
                self.changeX = not self.changeX
            else:
                self.deltaX, self.deltaY  = 10, 0
                self.changeX = not self.changeX

        if self.posX == 100:
            self.deltaX = -10

        if self.posY == 100:
            self.deltaY = -10

        self.posX += self.deltaX
        self.posY += self.deltaY
        self.obj1.setAxes(Point(self.posX, self.posY, 0))

    def draw(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        self.setup3D(self.w, self.h)
        self.draw_3D()
        self.setup2D(self.w, self.h)
        self.draw_2D()
        glFlush();

    def initializeGL(self):
        glDisable(GL_TEXTURE_2D);
        glDisable(GL_DEPTH_TEST);
        glDisable(GL_COLOR_MATERIAL);
        glEnable(GL_BLEND);
        glEnable(GL_POLYGON_SMOOTH);
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
        glClearColor(1, 1, 1, 1);
        self.obj1 = DinamicObj('sphere', 20)
        # Materials
        glMaterialfv(GL_FRONT, GL_SPECULAR, vec(0.0, 0.0, 0.0, 1.0))
        glMaterialfv(GL_FRONT, GL_DIFFUSE, vec(1.0, 1.0, 1.0, 1.0))
        glMaterialfv(GL_FRONT, GL_SHININESS, vec(1.0));
        # Light zone
        glLightfv(GL_LIGHT0, GL_POSITION, vec(0.5, 0.5, 0, 0))
        glLightfv(GL_LIGHT0, GL_SPOT_DIRECTION, vec(0.5, 0.5, 0))
        glEnable(GL_LIGHT0)

    def resizeGL(self, w, h):
        glViewport(0, 0, w, h)
        self.w = w
        self.h = h
        self.label.y = h - self.font_size

    def setup3D(self, w, h):
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(40., w / float(h), 0.5, 500.0)
        gluLookAt(-100, -100, 100, 0, 0, 0, 0, 0, 1)
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
        if not self.pause:
            self.move()
        self.label.text = 'X:' + str(self.posX)
        self.glDraw()

    def paintGL(self):
        self.draw()
        pass

    def mouseMoveEvent(self, event) :
            print("{0}, {1}".format(event.x(), event.y()))

    def draw_2D(self):
        self.draw_triangle()
        self.label.draw()

    def draw_3D(self):
        self.draw_grid()
        if self.fade:
            glMaterialfv(GL_FRONT_AND_BACK, GL_DIFFUSE, vec(0.0, 0.4, 0.0, (self.posX + self.posY) / 100.0))
        else:
            glMaterialfv(GL_FRONT_AND_BACK, GL_DIFFUSE, vec(1.0, 8.0, 1.0, 1.0))
        self.obj1.draw_faces()

    def draw_triangle(self):
        glColor3f(1,0,0)
        glBegin(GL_POLYGON)
        glVertex2f(0,0)
        glVertex2f(10,50)
        glVertex2f(50,10)
        glEnd()

    def draw_grid(self):
        self.alfa = 10
        self.beta = 2
        self.gridSize = 10
        self.unit = self.beta + self.alfa
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

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    window.resize(600,600)
    app.exec_()

# vim: ts=4 et sw=4 st=4 list
