import os.path
from OpenGL.GL import *
import pyglet.graphics
import pyglet.image

from .shader import MaterialGroup, mtllib


ANIMDIR = 'assets/mesh-animations/'
DEFAULT_FRAMERATE = 40


def load_texture(name):
    image = pyglet.image.load(name, pyglet.resource.file(name))
    return image.get_mipmapped_texture()


class Material(dict):
    def load_textures(self):
        for k in self.keys():
            if k.startswith('map_'):
                self.get_texture(k)

    def get_texture(self, groupname):
        k = 'tex_' + groupname
        try:
            return self[k]
        except KeyError:
            tex = load_texture(self[groupname])
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
        self.load_textures()

        return MaterialGroup(
            self['name'],
            parent=parent
        )


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

    def to_list(self, batch, group=None):
        g = self.material.create_group(parent=group)

        l = len(self.vertices) / 3

        data = [
            ('v3f', self.vertices),
        ]

        if self.normals:
            assert len(self.normals) == 3 * l, \
                "len(normals) != len(vertices)"
            data.append(('n3f', self.normals))

        if self.texcoords:
            assert len(self.texcoords) == 2 * l, \
                "len(texcoords) != len(vertices)"
            data.append(('t2f', self.texcoords))

        self.list = batch.add_indexed(
            l,
            self.mode,
            g,
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

        self.batch = pyglet.graphics.Batch()
        self.meshes = []
        self.materials = {}
        for mesh in meshes:
            self.add_mesh(mesh)

    def add_mesh(self, mesh):
        mtl = mesh.material
        if mtl:
            mtlid = mtl['name']
            try:
                mtl = self.materials[mtlid]
            except KeyError:
                self.materials[mtlid] = mtl
            else:
                mesh.material = mtl

        l = mesh.to_list(self.batch)
        # only keep the list, to save memory
        self.meshes.append((mesh.name, l, mtl))

    def copy(self):
        """Create a copy of the model that shares vertex data only.

        This allows eg. texture maps to be redefined.
        """
        m = Model()
        m.name = self.name
        m.group = self.group
        m.batch = self.batch
        m.meshes = [
            (mesh.name, l, mesh.material.copy())
            for mesh in self.meshes
        ]
        return m

    def update(self, dt):
        pass

    def to_batch(self):
        return self.batch

    def get_instance(self):
        return self

    def draw(self):
        with mtllib(self.materials):
            self.batch.draw()


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


class ModelLoader(object):
    def __init__(self):
        self.meshes = {}
        self.mtllibs = set()
        self.materials = {}

    def _read_mtl(self, filename):
        """Read material definitions from a mtl file."""
        mtl = None
        with open(filename, 'r') as f:
            for line in f:
                # skip comments
                if line.startswith('#'):
                    continue

                values = line.split()

                # skip empty lines
                if not values:
                    continue
                cmd = values.pop(0)
                if cmd == 'newmtl':
                    if mtl:
                        yield mtl
                    mtl = Material(name=values[0])
                elif mtl is None:
                    raise ValueError(
                        "mtl file doesn't start with newmtl stmt"
                    )
                elif cmd.startswith('map_'):
                    # map definition
                    mtl[cmd] = values[0]
                else:
                    mtl[cmd] = map(float, values)
        if mtl:
            yield mtl

    def load_materials(self, filename):
        """Load a material library as a dict."""
        if filename in self.mtllibs:
            return
        self.mtllibs.add(filename)

        for mtl in self._read_mtl(filename):
            name = mtl['name']
            mtl['relpath'] = os.path.dirname(filename)
            self.materials[name] = mtl

    def load_obj(self, filename, swapyz=False):
        """Loads a Wavefront OBJ file. """

        mode = GL_TRIANGLES

        # These list hold defined vectors
        vertices = []
        normals = []
        texcoords = []

        # This will hold indexes into the vectors above
        faces = []

        # (faces, material) tuples
        facegroups = []

        material = None
        name = None

        for line in open(filename, "r"):
            if line.startswith('#'):
                continue

            values = line.split()
            if not values:
                continue

            if values[0] == 'v':
                v = map(float, values[1:4])
                if swapyz:
                    v = v[0], v[2], v[1]
                vertices.append(v)
            elif values[0] == 'vn':
                v = map(float, values[1:4])
                if swapyz:
                    v = v[0], v[2], v[1]
                normals.append(v)
            elif values[0] == 'vt':
                texcoords.append(map(float, values[1:3]))
            elif values[0] in ('usemtl', 'usemat'):
                if faces and material:
                    facegroups.append((faces, material))
                    faces = []
                material = self.materials[values[1]]
            elif values[0] == 'mtllib':
                self.load_materials(
                    os.path.join(os.path.dirname(filename), values[1])
                )
            elif values[0] == 'f':
                vs = []
                uvs = []
                ns = []
                for v in values[1:]:
                    w = v.split('/')
                    vs.append(int(w[0]))
                    if len(w) >= 2 and len(w[1]) > 0:
                        uvs.append(int(w[1]))
                    else:
                        uvs.append(0)
                    if len(w) >= 3 and len(w[2]) > 0:
                        ns.append(int(w[2]))
                    else:
                        ns.append(0)
                if len(vs) == 4:
                    mode = GL_QUADS
                faces.append((vs, uvs, ns))
            elif values[0] == 'o':
                name = values[1]

        if faces and material:
            facegroups.append((faces, material))

        model = Model(name=filename)

        for faces, material in facegroups:
            count = 0
            outvs = []
            outns = []
            outuvs = []
            indices = []

            seen = {}

            for face in faces:
                vs, uvs, ns = face

                for v, n, uv in zip(vs, ns, uvs):
                    vdata = (v, n, uv)
                    try:
                        i = seen[vdata]
                    except KeyError:
                        i = count
                        count += 1
                        seen[vdata] = i
                        outvs.extend(vertices[v - 1])
                        if normals:
                            outns.extend(normals[n - 1])
                        if texcoords:
                            outuvs.extend(texcoords[uv - 1])
                    indices.append(i)

            model.add_mesh(Mesh(
                name=filename,
                mode=mode,
                vertices=outvs,
                normals=outns,
                texcoords=outuvs,
                indices=indices,
                material=material,
            ))

        return model

    def load_model(self, name):
        return self.load_obj(os.path.join(ANIMDIR, name + '.obj'))

    def _get_frames(self, basename):
        for f in os.listdir(ANIMDIR):
            if f.startswith(basename + '_') and f.endswith('.obj'):
                yield os.path.join(ANIMDIR, f)

    def load_animation(self, name, sequences={}, default=None, next={}, framerate=DEFAULT_FRAMERATE):
        frames = sorted(self._get_frames(name))
        if not frames:
            raise ValueError(
                "No .obj files found in '%s' matching %s_*.obj" % (
                    ANIMDIR, name
                )
            )
        models = [self.load_obj(f) for f in frames]
        return AnimatedModel(models,
            sequences=sequences,
            default=default,
            next=next,
            framerate=framerate
        )


