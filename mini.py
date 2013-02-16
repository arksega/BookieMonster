#!/bin/python3
import sys
import os
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.QtOpenGL import *
from pyglet.gl import *

class MainWindow(QMainWindow):
    
    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent)
        self.pause = QPushButton('Pausar')
        self.gl = GLWidget()
        gp = QGridLayout()
        gp.addWidget(self.pause, 1, 0)
        gp.addWidget(self.gl, 0, 0)
        self.frame = QWidget()
        self.frame.setLayout(gp)
        self.setCentralWidget(self.frame)

class GLWidget(QGLWidget):

    def __init__(self, parent=None):
        QGLWidget.__init__(self, parent)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    window.resize(600,600)
    app.exec_()

# vim: ts=4 et sw=4 st=4
