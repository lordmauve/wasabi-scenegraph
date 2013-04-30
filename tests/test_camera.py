import math
from nose.tools import eq_
from scenegraph.scenegraph import Matrix4, v3, Camera


point = v3(2, 1, 0)


def project(point, camera):
    return camera.get_view_matrix() * point


def test_zaligned():
    """looking down the z axis in the -z direction"""
    camera = Camera(
        pos=v3(0, 0, 20)
    )
    eq_(project(point, camera), v3(2, 1, -20))


def test_xaligned():
    """looking down the x axis in the -x direction"""
    camera = Camera(
        pos=v3(20, 0, 0)
    )
    eq_(project(point, camera), v3(0, 1, -18))


def test_minusxaligned():
    """looking down the x axis in the +x direction"""
    camera = Camera(
        pos=v3(-20, 0, 0)
    )
    eq_(project(point, camera), v3(0, 1, -22))


def test_airborne():
    """looking down on the point, -z, -y direction"""
    root2 = math.sqrt(2)
    camera = Camera(
        pos=v3(2, 10 * root2, 10 * root2),
        look_at=v3(2, 0, 0)
    )
    eq_(project(point, camera), v3(0, 0.5 * root2, 0.5 * root2 - 20))

