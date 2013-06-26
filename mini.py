#!/bin/python3
import sys
from bm import *
from grid import *
from PyQt4.QtGui import *
from PyQt4.QtCore import *
from PyQt4.QtOpenGL import *
from math import cos, sin, radians


def vec(*args):
    return (GLfloat * len(args))(*args)


class MainWindow(QMainWindow):

    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent)
        self.gl = GLWidget()

        gp = QGridLayout()
        gp.addWidget(self.gl, 0, 0, 1, 2)
        self.frame = QWidget()
        self.frame.setLayout(gp)
        self.setCentralWidget(self.frame)
        toolBar = self.addToolBar('Principal')
        toolBar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        autoicon = QIcon(
            '/usr/share/icons/oxygen/48x48/actions/media-playback-start.png')
        autoicon.addFile(
            '/usr/share/icons/oxygen/48x48/actions/media-playback-pause.png',
            mode=2, state=0)

        auto = QAction(autoicon, 'AutoPlay', self)
        auto.setCheckable(True)
        auto.triggered.connect(self.autoToggle)
        toolBar.addAction(auto)

        easy = QAction('Facil', self)
        easy.triggered.connect(self.changerDificult('easy'))
        easy.setCheckable(True)
        easy.setChecked(True)
        normal = QAction('Normal', self)
        normal.triggered.connect(self.changerDificult('normal'))
        normal.setCheckable(True)
        hard = QAction('Dificil', self)
        hard.triggered.connect(self.changerDificult('hard'))
        hard.setCheckable(True)

        group = QActionGroup(self)
        easy.setActionGroup(group)
        normal.setActionGroup(group)
        hard.setActionGroup(group)

        toolBar.addAction(easy)
        toolBar.addAction(normal)
        toolBar.addAction(hard)

        # Help dialog
        self.helpDialog = QDialog(self)
        helpLay = QGridLayout(self.helpDialog)
        image = QLabel()
        image.setPixmap(QPixmap('data/images/instructions.png'))
        helpLay.addWidget(image)

    def changerDificult(self, level):
        def setDificult():
            self.gl.board.level = level
        return setDificult

    def autoToggle(self):
        self.gl.board.autoMoveToggle()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_R:
            self.gl.board.reloadMap()
        elif event.key() == Qt.Key_T:
            self.gl.track = not self.gl.track
            if self.gl.track:
                self.gl.distance = -50
            else:
                self.gl.distance = -300
        elif self.gl.board.autoPlaying:
            pass
        elif event.key() == Qt.Key_V:
            self.gl.resetView()
        elif event.key() == Qt.Key_P:
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
        elif event.key() == Qt.Key_F1:
            self.helpDialog.show()
            self.gl.board.label.text = 'Move you to resume'
            self.gl.board.pause = True


class GLWidget(QGLWidget):

    def __init__(self, parent=None):
        QGLWidget.__init__(self, parent)
        self.timer = QTimer()
        self.timer.timeout.connect(self.updateGL)
        self.timer.start(33)
        self.resetView()
        self.track = False

    def resetView(self):
        self.distance = -300
        self.dx = -45
        self.dy = -45

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
        glEnable(GL_DEPTH_TEST)
        glClearColor(1, 1, 1, 1)
        # Load models
        self.board = Board()
        # Materials
        glMaterialfv(GL_FRONT, GL_SHININESS, vec(1.0))
        # Light zone
        glLightfv(GL_LIGHT0, GL_DIFFUSE, vec(10.0, 10.0, 10.0, 0))
        glLightfv(GL_LIGHT0, GL_POSITION, vec(-100, -100, 50.0, 0))
        glLightfv(GL_LIGHT0, GL_SPOT_DIRECTION, vec(0.5, 0.5, 0.0))
        glEnable(GL_LIGHT0)
        glLightfv(GL_LIGHT1, GL_DIFFUSE, vec(10.0, 10.0, 10.0, 0))
        glLightfv(GL_LIGHT1, GL_POSITION, vec(100, 100, -50.0, 0))
        glLightfv(GL_LIGHT1, GL_SPOT_DIRECTION, vec(-0.5, -0.5, 0.0))
        glEnable(GL_LIGHT1)

    def resizeGL(self, w, h):
        glViewport(0, 0, w, h)
        self.w = w
        self.h = h
        self.board.label.y = h - 32

    def setup3D(self, w, h):
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45., w / float(h), 1.0, 1000.0)
        gluLookAt(self.distance, 0, 0, 0, 0, 0, 0, 0, 1)
        glRotatef(self.dx, 0, 0, 1)
        vx = sin(radians(self.dx))
        vy = cos(radians(self.dx))
        glRotatef(self.dy, vx, vy, 0)
        data = [-1 * getattr(self.board.monster, axis) for axis in Point.axes]
        if self.track:
            glTranslatef(*data)

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

    def mouseMoveEvent(self, event):
        dx = self.mouseX - event.x()
        dy = self.mouseY - event.y()
        self.mouseX = event.x()
        self.mouseY = event.y()
        self.dx -= dx
        self.dy += dy

    def mousePressEvent(self, event):
        self.mouseX = event.x()
        self.mouseY = event.y()

    def wheelEvent(self, event):
        scroll = event.delta() / 33
        if self.distance + scroll < -30:
            self.distance += scroll

    def draw_2D(self):
        self.board.draw_2D()

    def draw_3D(self):
        self.board.draw_3D()
        glMaterialfv(GL_FRONT, GL_DIFFUSE, vec(0.0, 0.1, 0.0, 1.0))

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setApplicationName('Mini')
    window = MainWindow()
    window.show()
    window.resize(800, 800)
    app.exec_()

# vim: ts=4 et sw=4 st=4 list
