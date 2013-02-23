import math
import itertools
import pyglet

from pyglet.graphics import Group
from pyglet.gl import *


class v3(tuple):
    def __add__(self, ano):
        return v3(a + b for a, b in zip(self, ano))

    def __sub__(self, ano):
        return v3(a - b for a, b in zip(self, ano))

    def __mul__(self, scalar):
        return v3(a * scalar for a in self)

    def length(self):
        return math.sqrt(self.length2())

    def length2(self):
        return sum(a * a for a in self)


class ShaderGroup(Group):
    """A group that activates a Shader.

    Lists created with this group will be the rendered with the shader enabled;
    uniform variables can also be configured that will be applied whenever the
    shader is bound.

    """
    def __init__(self, shader, parent=None):
        super(ShaderGroup, self).__init__(parent)
        self.shader = shader
        self.uniforms = {}

    def set_state(self):
        self.shader.bind()
        for name, args in self.uniforms.iteritems():
            self.shader.uniformf(name, *args)

    def uniformf(self, name, *args):
        """Set a named uniform value.

        This will be set when the shader is bound."""
        self.uniforms[name] = args

    def unset_state(self):
        self.shader.unbind()


class ModelNode(object):
    """Draw a model at a point in space, with a rotation."""
    def __init__(self, batch, pos=(0, 0, 0), rotation=(0, 0, 1, 0)):
        self.batch = batch
        self.pos = pos
        self.rotation = rotation

    def draw(self):
        glPushMatrix()
        glTranslatef(*self.pos)
        glRotatef(*self.rotation)
        self.batch.draw()
        glPopMatrix()


class Scene(object):
    """A collection of scenegraph objects.

    At present this class does little more than render a list of objects; in
    future however it may support more sophisticated behaviour.

    """
    def __init__(self):
        self.objects = []

    def add(self, obj):
        self.objects.append(obj)

    def render(self, camera):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        camera.set_matrix()

        for o in self.objects:
            o.draw()


class Camera(object):
    """The camera class is a view onto a scene.

    This class offers the ability to set up the projection and modelview
    matrixes.

    """
    def __init__(self, pos=v3((0, 15, 15)), look_at=v3((0, 0, 0)), aspect=1.3333333333, fov=90.0):
        self.aspect = aspect
        self.fov = fov
        self.pos = pos
        self.look_at = look_at

    def set_matrix(self):
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(self.fov, self.aspect, 1.0, 10000.0)
        glEnable(GL_DEPTH_TEST)
        glMatrixMode(GL_MODELVIEW)
        gluLookAt(*itertools.chain(
            self.pos,
            self.look_at,
            (0, 1, 0)
        ))
