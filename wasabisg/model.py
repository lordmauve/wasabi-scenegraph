"""Representations of collections of geometry, with associated materials.

A model consists of one or more meshes.

A mesh consists of some geometry and an associated material.

A material is a dictionary of parameters, some of which may be textures.

"""
from weakref import WeakValueDictionary
from OpenGL.GL import GL_QUADS, GL_TRIANGLES
import pyglet
import pyglet.graphics
import pyglet.image
import pyglet.resource


DEFAULT_FRAMERATE = 40


class Mesh(object):
    """A bunch of geometry, with linked materials.

    """
    def __init__(self, mode, vertices, normals, texcoords, indices, material, name=None):
        self.name = name
        self.mode = mode
        self.vertices = vertices
        self.normals = normals
        self.texcoords = texcoords
        self.material = material
        self.indices = indices

    def inside_out(self):
        """Return a copy of this mesh that is inside out.

        Normals will be flipped and vertex winding order reversed.

        """
        # Flip normals
        norms = [-c for c in self.normals]

        if self.mode == GL_QUADS:
            batch = 4
        elif self.mode == GL_TRIANGLES:
            batch = 3
        else:
            raise ValueError(
                "Cannot invert mesh with drawing mode %s" % self.mode
            )

        idxs = []
        for b in zip(*[iter(self.indices)] * batch):
            idxs.extend(reversed(b))
        return Mesh(
            mode=self.mode,
            vertices=self.vertices,
            normals=norms,
            texcoords=self.texcoords,
            indices=idxs,
            material=self.material,
            name=self.name
        )

    def to_list(self, batch, group=None):
        l = len(self.vertices) / 3

        data = [
            ('v3f/static', self.vertices),
        ]

        if self.normals:
            assert len(self.normals) == 3 * l, \
                "len(normals) != len(vertices)"
            data.append(('n3f/static', self.normals))

        if self.texcoords:
            assert len(self.texcoords) == 2 * l, \
                "len(texcoords) != len(vertices)"
            data.append(('t2f/static', self.texcoords))

        self.list = batch.add_indexed(
            l,
            self.mode,
            group,
            self.indices,
            *data
        )

        return self.list

    def __repr__(self):
        return '<Mesh %s>' % self.name


class Model(object):
    def __init__(self, meshes=[], name=None):
        self.name = name
        self.group = None

        self.meshes = []
        self.materials = {}
        self.meshes = meshes

    def copy(self):
        """Create a copy of the model that shares vertex data only.

        This allows eg. texture maps to be redefined.
        """
        # Some parts of this are renderer-specific
        m = Model()
        m.name = self.name
        m.group = self.group
        m.batch = self.batch
        m.meshes = [
            (name, l, mtl.copy())
            for name, l, mtl in self.meshes
        ]
        return m

    def update(self, dt):
        pass

    def to_batch(self):
        # This is renderer-specific and belongs elsewhere
        return self.batch

    def get_instance(self):
        return self

#    def draw(self):
#        # This is renderer-specific and belongs elsewhere
#        with mtllib(self.materials):
#            self.batch.draw()


class AnimatedModelInstance(object):
    """Track the current frame for an animated model."""
    def __init__(self, model):
        self.model = model
        if self.model.default:
            self.play(self.model.default)
        else:
            self.play_all()

    def play_all(self):
        self.anim = range(len(self.model.frames))
        self.playing = 'all'
        self.currentframe = 0
        self.t = 0.0
        self.end = len(self.anim)

    def play(self, name):
        self.anim = self.model.sequences[name]
        self.playing = name
        self.currentframe = self.anim[0]
        self.t = 0.0

    def next_animation(self):
        """cue to the next animation, or restart the current one."""
        try:
            next = self.model.next[self.playing]
        except KeyError:
            self.t = 0
        else:
            self.play(next)

    def update(self, dt):
        """calculate correct frame to show"""
        self.t += dt * self.model.framerate
        if self.t >= len(self.anim):
            self.next_animation()
        else:
            self.currentframe = self.anim[int(self.t)]

    def draw(self):
        self.model.frames[self.currentframe].draw()


class AnimatedModel(object):
    """A sequence of models."""
    def __init__(self, frames, sequences={}, default=None, next={}, framerate=DEFAULT_FRAMERATE):
        self.frames = frames
        # TODO: read mtllib for model into materials attribute

        self.sequences = sequences
        self.default = default
        self.next = next
        self.framerate = float(framerate)

    def copy(self):
        """Create a copy of the model that shares vertex data only.

        Each material will be stored only once.
        """
        materials = {}
        fs = []
        for f in self.frames:
            m = Model()
            m.name = f.name
            m.group = f.group
            m.batch = f.batch
            for name, l, material in f.meshes:
                mtlid = material['name']
                try:
                    mtl = materials[mtlid]
                except KeyError:
                    mtl = material.copy()
                    materials[mtlid] = mtl

                m.meshes.append(
                    (name, l, mtl)
                )
            m.materials = materials
            fs.append(m)

        a = AnimatedModel(
            fs,
            sequences=self.sequences,
            default=self.default,
            next=self.next,
            framerate=self.framerate
        )
        a.materials = materials
        return a

    def get_instance(self):
        return AnimatedModelInstance(self)


class TextureLoader(object):
    def __init__(self):
        self.cache = WeakValueDictionary()

    def load_texture(self, name):
        try:
            return self.cache[name]
        except KeyError:
            image = pyglet.image.load(name, pyglet.resource.file(name))
            self.cache[name] = image
            return image.get_mipmapped_texture()


class Material(dict):
    """A bunch of attributes relating to display of a Mesh."""
    loader = TextureLoader()

    def load_textures(self):
        for k in self.keys():
            if k.startswith('map_'):
                self.get_texture(k)

    def get_texture(self, groupname):
        k = 'tex_' + groupname
        try:
            return self[k]
        except KeyError:
            tex = self.loader.load_texture(self[groupname])
            self[k] = tex
            return tex

    def __setitem__(self, key, value):
        dict.__setitem__(self, key, value)
        if key.startswith('map_'):
            tk = 'tex_' + key
            if tk in self:
                del(self[tk])
                self.get_texture(key)

    def copy(self):
        m = Material()
        m.update(self)
        return m

    def create_group(self, parent=None):
        # FIXME: this is renderer-specific and belongs in prepare_model
        from .shader import MaterialGroup
        self.load_textures()

        return MaterialGroup(
            self['name'],
            parent=parent
        )
