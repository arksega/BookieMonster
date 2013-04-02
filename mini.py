#!/bin/python3
import sys
from grid import *
from bm import *
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.QtOpenGL import *
#import pyglet
pyglet.options['debug_gl'] = False
from pyglet.gl import *


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
        #gp.addWidget(self.pause, 1, 0)
        #gp.addWidget(self.fade, 1, 1)
        gp.addWidget(self.gl, 0, 0, 1, 2)
        self.frame = QWidget()
        self.frame.setLayout(gp)
        self.setCentralWidget(self.frame)
        toolBar = self.addToolBar('Principal')
        toolBar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        autoicon = QIcon('/usr/share/icons/oxygen/48x48/actions/media-playback-start.png')
        autoicon.addFile('/usr/share/icons/oxygen/48x48/actions/media-playback-stop.png',mode=2,state=0)
        auto = QAction(autoicon,'AutoPlay', self)
        auto.triggered.connect(self.autoToggle)
        auto.setCheckable(True)
        toolBar.addAction(auto)

    def pauseToggle(self):
        self.gl.pause = not self.gl.pause

    def fadeToggle(self):
        self.gl.fade = not self.gl.fade

    def autoToggle(self):
        self.gl.board.autoMove()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_P:
            self.gl.board.label.text = 'Move you to resume'
            self.gl.board.pause = True
        elif event.key() in [Qt.Key_Right, Qt.Key_L, Qt.Key_F]:
            self.gl.board.pause = False
            self.gl.board.monster.setDirection('e')
        elif event.key() in [Qt.Key_Left, Qt.Key_J, Qt.Key_S]:
            self.gl.board.pause = False
            self.gl.board.monster.setDirection('w')
        elif event.key() in [Qt.Key_Up, Qt.Key_I]:
            self.gl.board.pause = False
            self.gl.board.monster.setDirection('n')
        elif event.key() in [Qt.Key_Down, Qt.Key_K]:
            self.gl.board.pause = False
            self.gl.board.monster.setDirection('s')
        elif event.key() == Qt.Key_E:
            self.gl.board.pause = False
            self.gl.board.monster.setDirection('u')
        elif event.key() == Qt.Key_D:
            self.gl.board.pause = False
            self.gl.board.monster.setDirection('d')
        elif event.key() == Qt.Key_X:
            self.gl.board.monster.toggleDrivenMode()


class GLWidget(QGLWidget):

    def __init__(self, parent=None):
        QGLWidget.__init__(self, parent)
        self.timer = QTimer()
        self.timer.timeout.connect(self.updateGL)
        self.timer.start(33)

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
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_DEPTH_TEST)
        glClearColor(1, 1, 1, 1)
        glEnable(GL_POLYGON_SMOOTH)
        glShadeModel(GL_SMOOTH)
        glHint(GL_LINE_SMOOTH_HINT, GL_DONT_CARE)
        # Load models
        self.board = Board()
        # Materials
        glMaterialfv(GL_FRONT, GL_SHININESS, vec(1.0))
        # Light zone
        glLightfv(GL_LIGHT0, GL_AMBIENT, vec(1.0, 1.0, 1.0, 0))
        glLightfv(GL_LIGHT0, GL_DIFFUSE, vec(10.0, 10.0, 10.0, 0))
        glLightfv(GL_LIGHT0, GL_POSITION, vec(-100, -100, 50.0, 0))
        glLightfv(GL_LIGHT0, GL_SPOT_DIRECTION, vec(0.5, 0.5, 0.0))
        glLightfv(GL_LIGHT0, GL_SPECULAR, vec(0.5, 0.5, 0.5, 0.5))
        glEnable(GL_LIGHT0)

    def resizeGL(self, w, h):
        glViewport(0, 0, w, h)
        self.w = w
        self.h = h
        self.board.label.y = h - 32

    def setup3D(self, w, h):
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45., w / float(h), 1.0, 1000.0)
        gluLookAt(-200, -200, 200, 0, 0, 0, 0, 0, 1)
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
        self.board.update()
        self.glDraw()

    def paintGL(self):
        self.draw()
        pass

    def keyPressEvent(self, event):
        print (event)

    def mouseMoveEvent(self, event):
            print(("{0}, {1}".format(event.x(), event.y())))

    def draw_2D(self):
        self.board.draw_2D()

    def draw_3D(self):
        self.board.draw_3D()
        glMaterialfv(GL_FRONT, GL_DIFFUSE, vec(0.0, 0.1, 0.0, 1.0))
        pass

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    window.resize(800, 800)
    app.exec_()

# vim: ts=4 et sw=4 st=4 list
