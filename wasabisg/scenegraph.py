import itertools
import pyglet

from pyglet.graphics import Group
from OpenGL.GL import *
from OpenGL.GLU import *
from euclid import Matrix4, Point3, Vector3

from .renderer import LightingAccumulationRenderer
from .model import Model, Mesh


def v3(a, *args):
    """Helper for constructing a Point vector."""
    if not args:
        return Point3(*a)
    return Point3(a, *args)


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
        if group:
            self.draw = self.draw_with_group
        else:
            self.draw = self.draw_inner

    def update(self, dt):
        self.model_instance.update(dt)

    def is_transparent(self):
        return self.transparent

    def draw_with_group(self, camera):
        self.group.set_state_recursive()
        self.draw_inner(camera)
        self.group.unset_state_recursive()

    def draw_inner(self, camera):
        glPushMatrix()
        glTranslatef(*self.pos)
        glRotatef(*self.rotation)
        self.model_instance.draw()
        glPopMatrix()


class GroupNode(object):
    """Group a bunch of other nodes."""
    def __init__(self,
            nodes,
            pos=(0, 0, 0),
            rotation=(0, 0, 1, 0),
            group=None):
        self.nodes = nodes
        self.pos = pos
        self.rotation = rotation
        self.group = group
        if group:
            self.draw = self.draw_with_group
        else:
            self.draw = self.draw_inner

    def update(self, dt):
        for n in self.nodes:
            n.update(dt)

    def is_transparent(self):
        return False

    def draw_with_group(self, camera):
        self.group.set_state_recursive()
        self.draw_inner(camera)
        self.group.unset_state_recursive()

    def draw_inner(self, camera):
        glPushMatrix()
        glTranslatef(*self.pos)
        glRotatef(*self.rotation)
        for n in self.nodes:
            n.draw(camera)
        glPopMatrix()


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


class Scene(object):
    """A collection of scenegraph objects.

    At present this class does little more than render a list of objects; in
    future however it may support more sophisticated behaviour.

    """
    def __init__(
            self,
            ambient=(0, 0, 0, 1.0),
            renderer=LightingAccumulationRenderer):

        self.ambient = ambient
        self.objects = []
        self.models = {}

        if callable(renderer):
            self.renderer = renderer()
        else:
            self.renderer = renderer

    def prepare_model(self, model):
        return self.renderer.prepare_model(model)

    def prepare_modelnode(self, c):
        c.model_instance = self.prepare_model(c.model_instance)

    def prepare_group(self, group):
        for c in group.nodes:
            if isinstance(c, GroupNode):
                self.prepare_group(c)
            else:
                self.prepare_modelnode(c)

    def clear(self):
        """Remove all objects from the scene."""
        del self.objects[:]

    def add(self, obj):
        """Add obj to the scene.

        obj should be a scenegraph node, but currently adding a Mesh or Model
        directly is supported as a convenience.

        """
        if isinstance(obj, Mesh):
            model = Model(meshes=[obj])
            model = self.prepare_model(model)
            obj = ModelNode(model)
        elif isinstance(obj, Model):
            model = self.prepare_model(obj)
            obj = ModelNode(model)
        elif isinstance(obj, ModelNode):
            obj.model_instance = self.prepare_model(obj.model_instance)
        elif isinstance(obj, GroupNode):
            self.prepare_group(obj)
        if obj in self.objects:
            return
        self.objects.append(obj)

    def remove(self, obj):
        """Remove obj from the scene."""
        try:
            self.objects.remove(obj)
        except ValueError:
            pass

    def update(self, dt):
        """Update all objects in the scene with the given time step."""
        for o in self.objects:
            o.update(dt)

    def render(self, camera):
        """Render the scene with the given camera."""
        self.renderer.render(self, camera)


class Camera(object):
    """The camera class is a view onto a scene.

    This class offers the ability to set up the projection and modelview
    matrixes.

    :param fov: The field of view in the y direction.

    """
    def __init__(
            self,
            width=800,
            height=600,
            pos=v3((0, 15, 15)),
            look_at=v3((0, 0, 0)),
            fov=67.5,
            near=1.0,
            far=10000.0):
        self.viewport = width, height
        self.aspect = float(width) / height
        self.fov = fov
        self.pos = pos
        self.look_at = look_at
        self.near = near
        self.far = far

    def eye_vector(self):
        """Get the direction in which the camera is looking."""
        return self.look_at - self.pos

    def set_projection_matrix(self):
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(self.fov, self.aspect, self.near, self.far)

    def set_matrix(self):
        self.set_projection_matrix()
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
        """Get the view matrix as a euclid.Matrix4."""
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


class OrthographicCamera(Camera):
    """An orthographic camera.

    :param scale: the width of the viewport in world space.

    """
    def __init__(
            self,
            width=800,
            height=600,
            pos=v3((0, 15, 15)),
            look_at=v3((0, 0, 0)),
            scale=20.0,
            near=1.0,
            far=10000.0):
        self.viewport = width, height
        self.aspect = float(width) / height
        self.pos = pos
        self.look_at = look_at
        self.near = near
        self.far = far
        self.scale = scale

    def bounds(self):
        hs = 0.5 * self.scale
        vs = hs / self.aspect
        l = -hs
        r = hs
        b = -vs
        t = vs
        return l, r, b, t, self.near, self.far

    def set_projection_matrix(self):
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(*self.bounds())
