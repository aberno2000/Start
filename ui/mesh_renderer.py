import numpy as np
from PyQt5.QtWidgets import QApplication, QOpenGLWidget
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QVector3D, QMatrix4x4
from OpenGL.GL import *


class MeshRenderer(QOpenGLWidget):
    def __init__(self, mesh_data):
        super().__init__()
        self.mesh_data = mesh_data
        self.min_count, self.max_count = self.get_counter_bounds()
        self.last_pos = QPoint()

        # Camera settings
        self.zoom = 45
        self.cameraPos = QVector3D(0, 0, 3)
        self.cameraFront = QVector3D(0, 0, -1)
        self.cameraUp = QVector3D(0, 1, 0)
        self.yaw = 0.0  # Initial view is along X axis
        self.pitch = 0.0
        self.lastPos = QPoint()

    def calculateViewMatrix(self):
        view = QMatrix4x4()
        view.lookAt(self.cameraPos, self.cameraPos + self.cameraFront, self.cameraUp)
        return view

    def calculateProjectionMatrix(self):
        projection = QMatrix4x4()
        projection.perspective(self.zoom, self.width() / self.height(), 0.1, 100.0)
        return projection

    def wheelEvent(self, event):
        zoom_sensitivity = 100
        self.zoom -= event.angleDelta().y() / zoom_sensitivity
        self.update()

    def mousePressEvent(self, event):
        self.lastPos = event.pos()

    def mouseMoveEvent(self, event):
        if not self.lastPos.isNull():
            sensitivity = 0.1
            dx = (event.x() - self.lastPos.x()) * sensitivity
            dy = (self.lastPos.y() - event.y()) * sensitivity

            self.yaw += dx
            self.pitch += dy

            # Constrain pitch
            self.pitch = max(-89.0, min(89.0, self.pitch))

            # Update camera direction
            direction = QVector3D()
            direction.setX(
                np.cos(np.radians(self.yaw)) * np.cos(np.radians(self.pitch))
            )
            direction.setY(np.sin(np.radians(self.pitch)))
            direction.setZ(
                np.sin(np.radians(self.yaw)) * np.cos(np.radians(self.pitch))
            )
            self.cameraFront = direction.normalized()

        self.lastPos = event.pos()
        self.update()

    def get_counter_bounds(self):
        counters = [triangle[5] for triangle in self.mesh_data]
        return min(counters), max(counters)

    def normalize_counter(self, counter):
        return (counter - self.min_count) / (self.max_count - self.min_count)

    def initializeGL(self):
        glEnable(GL_DEPTH_TEST)

    def resizeGL(self, width, height):
        glViewport(0, 0, width, height)

    def get_color(self, counter):
        normalized = self.normalize_counter(counter)
        return (normalized, 0, 1 - normalized)

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        # Apply projection transformation
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        projection = self.calculateProjectionMatrix()
        glMultMatrixf(projection.data())

        # Apply view transformation
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        view = self.calculateViewMatrix()
        glMultMatrixf(view.data())

        # Render the mesh
        glBegin(GL_TRIANGLES)
        for triangle in self.mesh_data:
            counter = triangle[5]
            color = self.get_color(counter)
            glColor3fv(color)

            for vertex in triangle[1:4]:
                glVertex3fv(vertex)
        glEnd()
