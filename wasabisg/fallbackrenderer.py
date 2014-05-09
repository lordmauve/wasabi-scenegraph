from pyglet.graphics import Batch, Group
from OpenGL.GL import *
from .lighting import Light, Sunlight, BaseLight


def _pad_v4(*args):
    return tuple(args[:4]) + (1.0,) * max(0, 4 - len(args))


def _to_float(v):
    if isinstance(v, (int, float)):
        return v
    return v[0]


def clamp(v, low, high):
    return min(high, max(low, v))


class MaterialGroup(Group):
    def __init__(self, material, parent=None):
        self.material = material
        try:
            self.tex = material['tex_map_Kd']
        except KeyError:
            self.tex = None

        self.diffuse = _pad_v4(*material.get('Kd', (1.0, 1.0, 1.0)))
        self.specular = _pad_v4(*material.get('Ks', (0, 0, 0, 1)))
        self.specular_exponent = clamp(_to_float(material.get('Ns', 0.0)), 0, 128)
        self.illum = material.get('illum', 1)
        super(MaterialGroup, self).__init__(parent=parent)

    def set_state(self):
        super(MaterialGroup, self).set_state()
        if self.tex is not None:
            glActiveTexture(GL_TEXTURE0)
            glBindTexture(GL_TEXTURE_2D, self.tex.id)
        if not self.illum:
            glDisable(GL_LIGHTING)
            glColor4fv(self.diffuse)
        else:
            glMaterialfv(GL_FRONT, GL_AMBIENT_AND_DIFFUSE, self.diffuse)
            glMaterialfv(GL_FRONT, GL_SPECULAR, self.specular)
            glMaterialf(GL_FRONT, GL_SHININESS, self.specular_exponent)

    def unset_state(self):
        if self.tex:
            glActiveTexture(GL_TEXTURE0)
            glBindTexture(GL_TEXTURE_2D, 0)
        if not self.illum:
            glEnable(GL_LIGHTING)
            glColor4f(1, 1, 1, 1)
        super(MaterialGroup, self).unset_state()


class FallbackRenderer(object):
    lights_enabled = 0

    def __init__(self):
        self.textures = {}

    def render(self, scene, camera):
        glEnable(GL_TEXTURE_2D)
        glClearColor(1.0, 0, 0, 0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glDisable(GL_CULL_FACE)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        glEnable(GL_DEPTH_TEST)

        glEnable(GL_ALPHA_TEST)
        glAlphaFunc(GL_GREATER, 0.9)

        glEnable(GL_LIGHTING)
        glLightModeli(GL_LIGHT_MODEL_TWO_SIDE, 0)
        glDisable(GL_COLOR_MATERIAL)

        glLightModelfv(GL_LIGHT_MODEL_AMBIENT, scene.ambient)

        # Enable for Wireframe
        # glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)

        camera.set_matrix()
        self.render_scene(camera, scene.objects)

    def prepare_model(self, model):
        if hasattr(model, 'draw'):
            return model
        batch = Batch()
        for m in model.meshes:
            self.prepare_mesh(m, batch)
        model.batch = batch
        model.draw = batch.draw
        return model

    def prepare_mesh(self, mesh, batch):
        mat = mesh.material
        mat.load_textures()

        l = mesh.to_list(batch, group=MaterialGroup(mat))
        mesh.list = l

    def render_scene(self, camera, objects):
        lights = [o for o in objects if isinstance(o, BaseLight)]

        # Prioritise lights, since we can only use 8
        lights.sort(key=lambda l: (not isinstance(l, Sunlight), l.intensity / (l.falloff + 1)))
        lights = lights[:GL_MAX_LIGHTS]

        for i, l in enumerate(lights):
            target = GL_LIGHT0 + i
            intensity = float(l.intensity)
            colour = [c * intensity for c in l.colour]
            if isinstance(l, Sunlight):
                glLightfv(target, GL_POSITION, l.direction.xyz + (0.0,))
            else:
                glLightfv(target, GL_POSITION, l.pos.xyz + (1.0,))
                glLightf(target, GL_QUADRATIC_ATTENUATION, l.falloff)
            glLightfv(target, GL_DIFFUSE, colour)
            glLightfv(target, GL_SPECULAR, colour)
            glEnable(target)

        if len(lights) < self.lights_enabled:
            for i in range(0, self.lights_enabled - len(lights)):
                glDisable(GL_LIGHT0 + i)
        self.lights_enabled = len(lights)

        for o in objects:
            if not isinstance(o, Light):
                o.draw(camera)
