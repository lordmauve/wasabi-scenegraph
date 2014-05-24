import math
from .model import Mesh, Material
from OpenGL.GL import GL_TRIANGLES


class Sphere(Mesh):
    """Construct a Mesh that is a 3D UV sphere.

    If `inside` is given then the normals and vertex winding will be reversed
    such that the camera will render the inside of the sphere rather than the
    outside. This is useful for skydomes etc.

    """

    def __init__(
            self,
            radius=1,
            inside=False,
            latitude_divisions=20,
            longitude_divisions=40,
            material=None):

        material = material or Material(name='sphere_material')
        self.radius = radius
        self.latitude_divisions = latitude_divisions
        self.longitude_divisions = longitude_divisions

        vs = []
        ns = []
        uvs = []
        tangents = []

        for lat in xrange(latitude_divisions + 1):
            # angle of latitude, where 0 is the north pole and pi is south
            theta = lat * math.pi / latitude_divisions
            sintheta = math.sin(theta)
            costheta = math.cos(theta)

            for lng in xrange(longitude_divisions + 1):
                phi = lng * 2 * math.pi / longitude_divisions
                sinphi = math.sin(phi)
                cosphi = math.cos(phi)

                x = cosphi * sintheta
                y = costheta
                z = sinphi * sintheta

                u = 1 - (float(lng) / longitude_divisions)
                v = 1 - (float(lat) / latitude_divisions)

                ns.extend([x, y, z])
                uvs.extend([u, v])
                vs.extend([x * radius, y * radius, z * radius])
                tangents.extend([-sinphi, 0, cosphi])

        indexes = []
        for lat in xrange(latitude_divisions):
            for lng in xrange(longitude_divisions):
                i = lat * (longitude_divisions + 1) + lng
                j = i + longitude_divisions + 1

                indexes.extend([
                    i + 1,
                    j,
                    i,
                    i + 1,
                    j + 1,
                    j,
                ])

        super(Sphere, self).__init__(
            GL_TRIANGLES,
            vertices=vs,
            normals=ns,
            texcoords=uvs,
            indices=indexes,
            material=material,
            name=repr(self)
        )

        if inside:
            flipped = self.inside_out()
            self.normals = flipped.normals
            self.indices = flipped.indices

    def __repr__(self):
        return (
            'Sphere('
            '%(radius)r, '
            '%(latitude_divisions)r, '
            '%(longitude_divisions)r)' % self.__dict__
        )


# Create an alias in case users want to differentiate from other ways of
# tesselating a sphere
UVSphere = Sphere
