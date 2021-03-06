import math
from wasabisg.scenegraph import Matrix4, v3, Camera


def vec_eq(a, b):
    """Return True if vectors a and b are approximately equal."""
    return (a - b).magnitude_squared() < 1e-6


point = v3(2, 1, 0)


def project(point, camera):
    return camera.get_view_matrix() * point


def test_zaligned():
    """looking down the z axis in the -z direction"""
    camera = Camera(
        pos=v3(0, 0, 20)
    )
    vec_eq(project(point, camera), v3(2, 1, -20))


def test_xaligned():
    """looking down the x axis in the -x direction"""
    camera = Camera(
        pos=v3(20, 0, 0)
    )
    vec_eq(project(point, camera), v3(0, 1, -18))


def test_minusxaligned():
    """looking down the x axis in the +x direction"""
    camera = Camera(
        pos=v3(-20, 0, 0)
    )
    vec_eq(project(point, camera), v3(0, 1, -22))


def test_airborne():
    """looking down on the point, -z, -y direction"""
    root2 = math.sqrt(2)
    camera = Camera(
        pos=v3(2, 10 * root2, 10 * root2),
        look_at=v3(2, 0, 0)
    )
    vec_eq(project(point, camera), v3(0, 0.5 * root2, 0.5 * root2 - 20))

