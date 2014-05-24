
from OpenGL.GL import GL_QUADS, GL_QUAD_STRIP, GL_TRIANGLE_STRIP
from euclid import Point3, Vector3

from .model import Mesh, Material


class Quad(Mesh):
    """A single quad.

    points should be a list of 4 coplanar euclid.Point3 that represent the
    vertices of the quad.

    normals should be a list of 4 euclid.Vector3. If omitted or None, then
    these will be computed such that the quad is shaded as flat.

    """
    def __init__(
            self,
            points=[
                Point3(-1, 0, -1),
                Point3(-1, 0, 1),
                Point3(1, 0, 1),
                Point3(1, 0, -0)
            ],
            normals=None,
            material=None):
        assert len(points) == 4

        material = material or Material(name='plane_material')

        if normals is None:
            ns = []
            for i, p in enumerate(points):
                pprev = points[(i - 1) % 4]
                pnext = points[(i + 1) % 4]
                normal = (pnext - p).cross(pprev - p).normalized()
                ns.extend(normal)
        else:
            ns = [c for n in normals for c in n]

        uvs = [
            0, 0,
            0, 1,
            1, 1,
            1, 0
        ]
        vs = [c for v in points for c in v]
        super(Quad, self).__init__(
            GL_QUADS,
            vertices=vs,
            normals=ns,
            texcoords=uvs,
            indices=[0, 1, 2, 3],
            material=material,
            name=repr(self)
        )

    def __repr__(self):
        return '<%s at 0x%x>' % (self.__class__.__name__, id(self))


class Plane(Mesh):
    """Construct a single square mesh.

    If divisions == 1, then this will be a single quad, otherwise the quad
    will be subdivided that number of times in each direction. For example, if
    divisions == 4 then the Plane mesh will consist of 16 squares.

    """

    def __init__(
            self,
            center=Point3(0, 0, 0),
            normal=Vector3(0, 1, 0),
            size=1000.0,
            divisions=1,
            material=None):

        material = material or Material(name='plane_material')

        normal = normal.normalized()
        up = Vector3(0, 1, 0)
        x = up.cross(normal)
        if x.magnitude_squared() < 1e-3:
            up = Vector3(0, 0, 1)
            x = up.cross(normal)

        x = x.normalized()
        y = x.cross(normal)

        sx = x * float(size) / divisions
        sy = y * float(size) / divisions

        ns = []
        uvs = []
        vs = []

        y = -sy * divisions * 0.5
        for j in xrange(divisions + 1):
            x = -sx * divisions * 0.5
            v = j / float(divisions)
            for i in xrange(divisions + 1):
                vs.extend(center + x + y)
                ns.extend(normal)
                u = i / float(divisions)
                uvs.extend((u, v))
                x += sx
            y += sy

        indices = []

        def idx(i, j):
            indices.append(j * (divisions + 1) + i)

        # TODO: Use quad strips and save some index memory
        for j in xrange(divisions):
            for i in xrange(divisions):
                idx(i, j + 1)
                idx(i + 1, j + 1)
                idx(i + 1, j)
                idx(i, j)

        super(Plane, self).__init__(
            GL_QUADS,
            vertices=vs,
            normals=ns,
            texcoords=uvs,
            indices=indices,
            material=material,
            name=repr(self)
        )

    def __repr__(self):
        return '<%s at 0x%x>' % (self.__class__.__name__, id(self))
