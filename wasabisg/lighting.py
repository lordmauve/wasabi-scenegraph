from euclid import Point3, Vector3


class BaseLight(object):
    """Indicate that this is a light."""

    @property
    def colour(self):
        return self._colour

    @colour.setter
    def set_colour(self, c):
        self._colour = tuple(c) + (1.0,) * (4 - len(c))

    def update(self, dt):
        pass

    def is_transparent(self):
        return True

    def draw(self, *args):
        """Lights are invisible."""


class Light(BaseLight):
    """A point light.

    :param euclid.Point3 pos: The position of the light in the scene.
    :param colour: The colour of the light as an RGBA tuple. Typically the A
                   component should be 1.0.
    :param intensity: The intensity of the light. This can be arbitrarily high.
    :param falloff: The rate of falloff of the light. Bigger numbers mean faster
                    attenuation.

    """
    w = 1

    def __init__(self,
                 pos=Point3(0, 0, 0),
                 colour=(1, 1, 1, 1),
                 intensity=5,
                 falloff=2):
        self.pos = pos
        self._colour = colour
        self.intensity = intensity
        self.falloff = falloff

    @property
    def pos(self):
        return self._pos

    @pos.setter
    def pos(self, pos):
        self._pos = Point3(*pos[:3])


class Sunlight(BaseLight):
    """A sun light (ie. at infinite distance).

    :param euclid.Vector3 direction: The direction TO the sun FROM the scene.
    :param colour: The colour of the light as an RGBA tuple. Typically the A
                   component should be 1.0.
    :param intensity: The intensity of the light. This can be arbitrarily high.

    """
    falloff = 0
    w = 0

    def __init__(self,
                 direction=Vector3(0, 0, 0),
                 colour=(1, 1, 1, 1),
                 intensity=5):
        self.direction = direction
        self._colour = colour
        self.intensity = intensity

    @property
    def direction(self):
        return self._pos

    @direction.setter
    def direction(self, direction):
        self._pos = d = Vector3(*direction[:3])
        d.normalize()
