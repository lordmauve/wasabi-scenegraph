import math
import pyglet
from itertools import product

from euclid import Point3
from wasabisg.loaders.objloader import ObjFileLoader
from wasabisg.model import Model, Material
from wasabisg.lighting import Light
from wasabisg.scenegraph import Scene, Camera, v3, ModelNode


FPS = 60
WIDTH = 800
HEIGHT = 600

# Models
robot_model = None

# Scene
scene = None

# Scene nodes
robots = []

materials = [
    None,
    Material(
        Ka=(0.2, 0.2, 0.2),
        Kd=(0.6, 0.1, 0.1),
        Ks=(0.8, 0.8, 0.8),
        Ns=30.0,
        illum=1,
    ),
    None,
    None
]


def load():
    """Create models programmatically"""
    global scene, robot_model
    loader = ObjFileLoader()
    robot_model = loader.load_obj('robot.obj')


def init_scene():
    """Set up the scene and place objects into it."""
    global scene
    # Create a scene
    scene = Scene(
        ambient=(0.05, 0.05, 0.05, 1.0),
    )

    light = Light(
        pos=(50, 10, -50),
        colour=(1.0, 1.0, 1.0, 1.0),
        intensity=0.6,
        falloff=0
    )

    scene.add(light)

    for (x, y), mat in zip(product((-6, 6), (-6, 6)), materials):
        if mat:
            model = robot_model.copy()
            model.meshes[1].material = mat
        else:
            model = robot_model

        robot = ModelNode(
            model,
            pos=Point3(x, y, 0)
        )
        scene.add(robot)
        robots.append(robot)


angle = 180
tau = 2 * math.pi


def update(dt):
    global angle
    angle += 90.0 * dt

    for r in robots:
        r.rotation = (angle, 0, 1, 0)


c = Camera(
    pos=v3((0, 5, -20)),
    look_at=Point3(0, 5, 0),
    width=WIDTH,
    height=HEIGHT
)


def on_draw():
    window.clear()
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
