from objloader import Mesh, Material

from OpenGL.GL import GL_QUADS
from euclid import Point3, Vector3


class Quad(Mesh):
    """A single quad.

    points should be a list of 4 euclid.Point3.

    normals should be a list of 4 euclid.Vector3. If omitted or None, then
    these will be computed such that the quad appears planar.

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


class Plane(Quad):
    """Construct a single large quad."""

    def __init__(
            self,
            center=Point3(0, 0, 0),
            normal=Vector3(0, 1, 0),
            size=1000.0,
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

        sx = x * size
        sy = y * size

        super(Plane, self).__init__(
            points=[
                center - sx - sy,
                center - sx + sy,
                center + sx + sy,
                center + sx - sy,
            ],
            material=material
        )
