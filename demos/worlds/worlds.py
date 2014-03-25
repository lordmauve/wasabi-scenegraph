from __future__ import division

import math
import pyglet
from pyglet import gl
from pyglet.window import key
from pyglet.graphics import TextureGroup

from wasabisg.sphere import Sphere
from wasabisg.scenegraph import Camera, Scene, v3, GLStateGroup, ModelNode
from wasabisg.objloader import ModelLoader, Model, Material
from wasabisg.lighting import Light


FPS = 60
WIDTH = 800
HEIGHT = 600

# Distance from the earth to the sim. Not to scale!
SUN_DISTANCE = 100

# Distance from the earth to the moon. Not to scale!
MOON_DISTANCE = 5

# Models
earth_model = None
moon_model = None
stars_model = None

# Scene
scene = None

# Scene nodes
earth = None
moon = None
sun = None
sunlight = None


def load():
    """Create models programmatically"""
    global earth_model, moon_model, stars_model

    pyglet.resource.path = ['textures']
    pyglet.resource.reindex()

    earth_model = Model(
        meshes=[Sphere(
            material=Material(
                name='earth',
                map_Kd='earth.png',
                illum=2,
                Kd=(1, 1, 1),
            )
        )]
    )
    moon_model = Model(
        meshes=[Sphere(
            radius=1734.4 / 6378.1,
            material=Material(
                name='moon',
                map_Kd='moon.png',
                Kd=(1, 1, 1),
                illum=2,
            )
        )]
    )
    stars_model = Model(
        meshes=[Sphere(
            radius=500,
            material=Material(
                name='stars',
                map_Kd='stars.png',
                Kd=(1, 1, 1),
                illum=0
            )
        )]
    )


def init_scene():
    """Set up the scene and place objects into it."""
    global scene, earth, moon, sunlight
    # Create a scene
    scene = Scene(
        ambient=(0.05, 0.05, 0.05, 1.0)
    )

    # Set up objects in the scene
    sunlight = Light(
        pos=(100, 0, 100),
        colour=(1.0, 1.0, 1.0, 1.0),
        intensity=0.4,
        falloff=0
    )

    scene.add(sunlight)
    scene.add(ModelNode(stars_model))

    earth = ModelNode(earth_model)
    scene.add(earth)

    moon = ModelNode(moon_model, pos=(MOON_DISTANCE, 0, 0))
    scene.add(moon)


zpos = 10

earth_rot = math.pi * 0.25
earth_orbit = 0
moon_orbit = 0  # moon is tidally locked, doesn't need a separate rot var

tau = 2 * math.pi


def update(dt):
    global zpos, earth_rot, earth_orbit, moon_orbit
    zpos *= 0.5 ** dt

    # Update the solar system
    earth_rot += tau * dt
    moon_orbit += tau * dt / 28.0
    earth_orbit += tau * dt / 365.25

    # Apply the positions to the scene
    earth.rotation = (math.degrees(earth_rot), 0, 1, 0)
    moon.rotation = (math.degrees(moon_orbit) - 90, 0, 1, 0)

    mx = MOON_DISTANCE * math.cos(-moon_orbit)
    mz = MOON_DISTANCE * math.sin(-moon_orbit)
    moon.pos = mx, 0, mz

    sx = SUN_DISTANCE * math.cos(earth_orbit)
    sz = SUN_DISTANCE * math.sin(earth_orbit)
    sunlight.pos = sx, 0, sz, 0

    c.pos = v3((0, 3, zpos + 10))


c = Camera(pos=v3((0, 0, -20)))


def on_draw():
    gl.glEnable(gl.GL_TEXTURE_2D)
    gl.glClearColor(1.0, 0, 0, 0)
    gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
    gl.glDisable(gl.GL_CULL_FACE)
    gl.glEnable(gl.GL_BLEND)
    gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
    gl.glEnable(gl.GL_ALPHA_TEST)
    gl.glAlphaFunc(gl.GL_GREATER, 0.9)
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
