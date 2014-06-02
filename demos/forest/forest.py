from __future__ import division

import math
import pyglet
import random
from pyglet import gl
from pyglet.window import key

from wasabisg.sphere import Sphere
from wasabisg.plane import Plane
from wasabisg.scenegraph import Camera, Scene, v3, ModelNode
from wasabisg.loaders.objloader import ObjFileLoader
from wasabisg.model import Material
from wasabisg.lighting import Light, Sunlight
from wasabisg.fallbackrenderer import FallbackRenderer


FPS = 60
WIDTH = 800
HEIGHT = 600


scene = None
tree_model = None


def load():
    global scene, tree_model
    loader = ObjFileLoader()
    tree_model = loader.load_obj('tree.obj')

    # Scene
    scene = Scene(
        ambient=(0.05, 0.05, 0.05, 1.0),
        #renderer=FallbackRenderer()
    )


def init_scene():
    """Set up the scene and place objects into it."""

    # Add some sun
    scene.add(Sunlight(
        direction=(1, 0.5, 1),
        colour=(1.0, 0.8, 0.5, 1.0),
        intensity=0.3,
    ))

    # Add a magical purple point light
    scene.add(Light(
        pos=(0, 1, 0),
        colour=(1.0, 0.0, 1.0, 1.0),
        intensity=1.5,
        falloff=0.01
    ))

    # Sky dome
    scene.add(
        Sphere(
            radius=500,
            inside=True,
            material=Material(
                name='sky',
                Kd=(0.2, 0.2, 0.8),
                illum=0
            )
        )
    )

    # Ground
    scene.add(
        Plane(
            divisions=30,
            size=100,
            material=Material(
                name='ground',
                Kd=(0.2, 0.5, 0.2),
                illum=1
            )
        )
    )

    rng = random.Random(1)
    for i in range(20):
        x, y = (rng.uniform(-20.0, 20.0) for _ in range(2))
        tree = ModelNode(tree_model, pos=(x, 0, y))
        scene.add(tree)


zpos = 10

camera_rot = 0

tau = 2 * math.pi


def update(dt):
    global camera_rot
    camera_rot += 0.1 * dt
    c.pos = v3((math.cos(camera_rot) * 15, 5, math.sin(camera_rot) * 15))


c = Camera(
    pos=v3((0, 0, -20)),
    width=WIDTH,
    height=HEIGHT
)


def on_draw():
    scene.render(c)


if __name__ == '__main__':
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option(
        '-s', '--screenshot',
        metavar='FILE',
        help='Write screenshot to FILE'
    )
    options, _ = parser.parse_args()

    window = pyglet.window.Window(
        width=WIDTH,
        height=HEIGHT
    )

    load()
    init_scene()

    if options.screenshot:
        update(0)
        on_draw()
        image = pyglet.image.ColorBufferImage(
            0, 0, window.width, window.height
        )
        image.save(options.screenshot)
    else:
        window.event(on_draw)
        pyglet.clock.schedule_interval(update, 1.0 / FPS)
        pyglet.app.run()
