import os.path

from ..model import Model, Mesh, AnimatedModel, DEFAULT_FRAMERATE, Material

from OpenGL.GL import GL_TRIANGLES, GL_QUADS


ANIMDIR = 'assets/mesh-animations/'


def optimise_model(model):
    """Combine meshes with identical materials.

    This significantly improves drawing performance.

    """
    from array import array
    materials = {}
    meshes_by_mat = {}
    for m in model.meshes:
        matid = id(m.material)
        mode = m.mode
        materials[matid] = m.material
        meshes_by_mat.setdefault((mode, matid), []).append(m)

    out = []
    for (mode, matid), meshes in meshes_by_mat.items():
        vs = array('f')
        ns = array('f')
        uvs = array('f')
        indices = array('L')
        for m in meshes:
            offset = len(vs) // 3
            vs.extend(m.vertices)
            ns.extend(m.normals)
            uvs.extend(m.texcoords)
            indices.extend(i + offset for i in m.indices)
        out.append(Mesh(
            mode=mode,
            vertices=vs,
            normals=ns,
            texcoords=uvs,
            indices=indices,
            material=materials[matid]
        ))
    model.meshes = out


class ObjFileLoader(object):
    """Load models from Wavefront .obj files."""
    def __init__(self):
        self.mtl_loader = MtlFileLoader()

    def load_obj(self, filename, swapyz=False):
        """Load a Wavefront OBJ file and return a Model."""

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
                    facegroups.append((faces, material, name))
                    faces = []
                material = self.mtl_loader.get_material(values[1])
            elif values[0] == 'mtllib':
                self.mtl_loader.load_materials(
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
            facegroups.append((faces, material, name))

        meshes = []

        for faces, material, name in facegroups:
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

            meshes.append(Mesh(
                name=name,
                mode=mode,
                vertices=outvs,
                normals=outns,
                texcoords=outuvs,
                indices=indices,
                material=material,
            ))

        model = Model(name=filename, meshes=meshes)
        optimise_model(model)
        return model

    def load_model(self, name):
        return self.load_obj(os.path.join(ANIMDIR, name + '.obj'))

    def _get_frames(self, basename):
        for f in os.listdir(ANIMDIR):
            if f.startswith(basename + '_') and f.endswith('.obj'):
                yield os.path.join(ANIMDIR, f)

    def load_animation(self, name,
                       sequences={},
                       default=None,
                       next={},
                       framerate=DEFAULT_FRAMERATE):
        frames = sorted(self._get_frames(name))
        if not frames:
            raise ValueError(
                "No .obj files found in '%s' matching %s_*.obj" % (
                    ANIMDIR, name
                )
            )
        models = [self.load_obj(f) for f in frames]
        return AnimatedModel(
            models,
            sequences=sequences,
            default=default,
            next=next,
            framerate=framerate
        )


class MtlFileLoader(object):
    def __init__(self):
        self.mtllibs = set()
        self.materials = {}

    def get_material(self, name):
        """Get a loaded material."""
        return self.materials[name]

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
