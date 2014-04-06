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
from wasabisg.lighting import Light


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
        ambient=(0.05, 0.05, 0.05, 1.0)
    )


def init_scene():
    """Set up the scene and place objects into it."""
    # Set up objects in the scene
    sunlight = Light(
        pos=(10, 1, 10),
        colour=(1.0, 1.0, 1.0, 1.0),
        intensity=5,
        falloff=0.5
    )

    scene.add(sunlight)

    # Sky dome
    scene.add(
        Sphere(
            radius=500,
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
            divisions=2,
            size=100,
            material=Material(
                name='ground',
                Kd=(0.1, 0.5, 0.1),
                illum=1
            )
        )
    )

    for i in range(20):
        x, y = (random.uniform(-20.0, 20.0) for _ in range(2))
        tree = ModelNode(tree_model, pos=(x, 0, y))
        scene.add(tree)


zpos = 10

camera_rot = 0

tau = 2 * math.pi


def update(dt):
    global camera_rot
    camera_rot += 0.1 * dt
    c.pos = v3((math.cos(camera_rot) * 15, 5, math.sin(camera_rot) * 15))


c = Camera(pos=v3((0, 0, -20)))


def on_draw():
    scene.render(c)


if __name__ == '__main__':
    window = pyglet.window.Window(
        width=WIDTH,
        height=HEIGHT
    )

    load()
    init_scene()

    window.event(on_draw)
    pyglet.clock.schedule_interval(update, 1.0 / FPS)
    pyglet.app.run()
