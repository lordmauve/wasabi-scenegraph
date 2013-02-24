from collections import namedtuple
from pyglet.gl import *


class Material(object):
    def __init__(self, contents):
        self.contents = contents

    def load_textures(self):
        import pygame
        surf = pygame.image.load(mtl['filename'])
        image = pygame.image.tostring(surf, 'RGBA', 1)
        ix, iy = surf.get_rect().size
        texid = mtl['texture_Kd'] = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, texid)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER,
            GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER,
            GL_LINEAR)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, ix, iy, 0, GL_RGBA,
            GL_UNSIGNED_BYTE, image)

    @classmethod
    def load(cls, filename):
        contents = {}
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
                    mtl = contents[values[1]] = {}
                elif mtl is None:
                    raise ValueError, "mtl file doesn't start with newmtl stmt"
                elif cmd.startswith('map_'):
                    # map definition
                    mtl[cmd] = values[1]
                else:
                    mtl[cmd] = map(float, values[1:])
        return cls(contents)


FaceGroup = namedtuple('FaceGroup', 'indices material')


class Mesh(object):
    def __init__(self, mode, vertices, normals, texcoords, indices, material, name=None):
        self.name = name
        self.mode = mode
        self.material = material
        self.vertices = vertices
        self.normals = normals
        self.texcoords = texcoords
        self.indices = indices

    def to_list(self, batch, group=None):
        l = len(self.vertices) / 3

        data = [
            ('v3f', self.vertices),
        ]

        if self.normals:
            data.append(('n3f', self.normals))

        if self.texcoords:
            data.append(('t2f', self.texcoords))

        self.list = batch.add_indexed(
            l,
            self.mode,
            group,
            self.indices,
            *data
        )

    def __repr__(self):
        return '<Mesh %s>' % self.name

    @classmethod
    def load_obj(cls, filename, swapyz=False):
        """Loads a Wavefront OBJ file. """

        mode = GL_TRIANGLES

        # These list hold defined vectors
        vertices = []
        normals = []
        texcoords = []

        # This will hold indexes into the vectors above
        faces = []

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
                material = values[1]
            elif values[0] == 'mtllib':
                mtl = Material.load(values[1])
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
                faces.append((vs, uvs, ns, material))
            elif values[0] == 'o':
                name = values[1]

        count = 0
        outvs = []
        outns = []
        outuvs = []
        indices = []

        seen = {}

        for face in faces:
            vs, uvs, ns, material = face

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
        return Mesh(
            name=name,
            mode=mode,
            material=material,
            indices=indices,
            vertices=outvs,
            normals=outns,
            texcoords=outuvs
        )
