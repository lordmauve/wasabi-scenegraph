import math
import itertools
import pyglet

from pyglet.graphics import Group
from pyglet.gl import *
from euclid import Matrix4, Point3, Vector3


def v3(*args):
    if len(args) == 1:
        return Point3(*args[0])
    return Point3(*args)


#class v3(tuple):
#    def __add__(self, ano):
#        return v3(a + b for a, b in zip(self, ano))
#
#    def __sub__(self, ano):
#        return v3(a - b for a, b in zip(self, ano))
#
#    def __mul__(self, scalar):
#        return v3(a * scalar for a in self)
#
#    def normalized(self):
#        return self * (1.0 / self.length())
#
#    def length(self):
#        return math.sqrt(self.length2())
#
#    def length2(self):
#        return sum(a * a for a in self)


class GLStateGroup(Group):
    def __init__(self, enable=[], disable=[], cull_face=None, depth_mask=None, parent=None):
        super(GLStateGroup, self).__init__(parent)
        self.enable = enable
        self.disable = disable
        self.cull_face = cull_face
        if cull_face:
            enable.append(GL_CULL_FACE)
        self.depth_mask = depth_mask

    def set_state(self):
        for e in self.enable:
            glEnable(e)
        for e in self.disable:
            glDisable(e)
        if self.cull_face:
            glCullFace(self.cull_face)
        if self.depth_mask is not None:
            glDepthMask(GL_TRUE if self.depth_mask else GL_FALSE)

    def unset_state(self):
        for e in self.enable:
            glDisable(e)
        for e in self.disable:
            glEnable(e)
        if self.depth_mask is not None:
            glDepthMask(GL_TRUE)


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
        ShaderGroup.currentshader = self.shader

    def uniformf(self, name, *args):
        """Set a named uniform value.

        This will be set when the shader is bound."""
        self.uniforms[name] = args

    def unset_state(self):
        self.shader.unbind()
        ShaderGroup.currentshader = None


class ModelNode(object):
    """Draw a model at a point in space, with a rotation."""
    def __init__(self,
            model,
            pos=(0, 0, 0),
            rotation=(0, 0, 1, 0),
            group=None,
            transparent=False):
        self.model_instance = model.get_instance()
        self.pos = pos
        self.rotation = rotation
        self.group = group
        self.transparent = transparent

    def update(self, dt):
        self.model_instance.update(dt)

    def is_transparent(self):
        return self.transparent

    def draw(self, camera):
        if self.group:
            self.group.set_state_recursive()
        glPushMatrix()
        glTranslatef(*self.pos)
        glRotatef(*self.rotation)
        self.model_instance.draw()
        glPopMatrix()
        if self.group:
            self.group.unset_state_recursive()


class RayNode(object):
    """A ray, drawn as a billboard towards the camera."""
    ta = (0, 0)
    tb = (0, 1)
    tc = (1, 1)
    td = (1, 0)
    uvs = list(itertools.chain(ta, tb, tc, td))

    def __init__(self, p1, p2, width, transparent=False, group=None):
        self.p1 = p1
        self.p2 = p2
        self.width = width
        self.transparent = transparent
        self.group = group

    def update(self, dt):
        pass

    def is_transparent(self):
        return self.transparent

    def draw(self, camera):
        p1, p2 = self.p1, self.p2
        along = (p2 - p1).normalize()
        across = along.cross(camera.eye_vector()).normalize()
        across *= 0.5 * self.width

        va = p1 - across
        vb = p2 - across
        vc = p2 + across
        vd = p1 + across
        vs = list(itertools.chain(va, vb, vc, vd))

        if self.group:
            self.group.set_state_recursive()
        pyglet.graphics.draw(4, GL_QUADS,
            ('v3f', vs),
            ('t2f', self.uvs),
        )
        if self.group:
            self.group.unset_state_recursive()


class RenderPass(object):
    """Base class for a render pass."""
    def __init__(self, transparency=False, group=None):
        self.transparency = transparency
        self.group = group

    def filter(self, node):
        return self.transparency == node.is_transparent()

    def render(self, camera, objects):
        if self.group:
            self.group.set_state_recursive()
        for o in objects:
            if self.filter(o):
                o.draw(camera)
        if self.group:
            self.group.unset_state_recursive()


class Scene(object):
    """A collection of scenegraph objects.

    At present this class does little more than render a list of objects; in
    future however it may support more sophisticated behaviour.

    """
    def __init__(self, passes=[RenderPass()]):
        self.objects = []
        self.passes = passes

    def clear(self):
        self.objects[:] = []

    def add(self, obj):
        if obj in self.objects:
            return
        self.objects.append(obj)

    def remove(self, obj):
        try:
            self.objects.remove(obj)
        except ValueError:
            pass

    def update(self, dt):
        for o in self.objects:
            o.update(dt)

    def render(self, camera):
        for p in self.passes:
            camera.set_matrix()
            p.render(camera, self.objects)


class Camera(object):
    """The camera class is a view onto a scene.

    This class offers the ability to set up the projection and modelview
    matrixes.

    """
    def __init__(self,
            width=800,
            height=600,
            pos=v3((0, 15, 15)),
            look_at=v3((0, 0, 0)),
            aspect=1.3333333333,
            fov=90.0 / 1.333333):
        self.viewport = width, height
        self.aspect = aspect
        self.fov = fov
        self.pos = pos
        self.look_at = look_at

    def eye_vector(self):
        return self.look_at - self.pos

    def set_matrix(self):
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(self.fov, self.aspect, 1.0, 10000.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        gluLookAt(*itertools.chain(
            self.pos,
            self.look_at,
            (0, 1, 0)
        ))

    def get_view_matrix_gl(self):
        from ctypes import c_double
        mat = (c_double * 16)()
        glGetDoublev(GL_MODELVIEW_MATRIX, mat)
        return Matrix4.new(*mat)

    def get_view_matrix(self):
        f = (v3(self.look_at) - v3(self.pos)).normalized()
        #print "f=", f
        up = Vector3(0, 1, 0)
        s = f.cross(up).normalize()
        #print abs(f), abs(up), abs(s)
        #print "s=", s
        u = s.cross(f)
        m = Matrix4.new(*itertools.chain(
            s, [0],
            u, [0],
            -f, [0],
            [0, 0, 0, 1]
        ))
        #print m
        xlate = Matrix4.new_translate(*(-self.pos))
        #print xlate
        mat = m.inverse() * xlate
        #print mat
        return mat
