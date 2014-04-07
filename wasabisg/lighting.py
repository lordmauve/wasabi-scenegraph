from euclid import Point3


class BaseLight(object):
    """Indicate that this is a light."""


class Light(BaseLight):
    """A point light.

    :param euclid.Point3 pos: The position of the light in the scene.
    :param colour: The colour of the light as an RGBA tuple. Typically the A
                   component should be 1.0.
    :param intensity: The intensity of the light. This can be arbitrarily high.
    :param falloff: The rate of falloff of the light.

    """
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
