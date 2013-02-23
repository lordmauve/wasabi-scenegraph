from __future__ import division

import pyglet
from pyglet import gl
from pyglet.window import key

from objloader import Mesh
from shaderlib import specular_shader

from scenegraph import ModelNode, Scene, Camera, ShaderGroup, v3


FPS = 60
WIDTH = 800
HEIGHT = 600



mesh = None
scene = Scene()
car = None


def load():
    global mesh, car
    group = ShaderGroup(specular_shader)
    group.uniformf('light_pos', -100, 50, -30, 0)

    mesh = Mesh.load_obj('car.obj')
    batch = pyglet.graphics.Batch()
    mesh.to_list(batch, group)

    car = ModelNode(batch)
    scene.add(car)


zpos = 20
rx, ry = 0, 0
tx, ty = 0, 2


def update(dt):
    global zpos, rx, ry
    rx += 10 * dt
    zpos *= 0.8 ** dt
    col = (88 / 255, 156 / 255, 163 / 255, 1)
    gl.glClearColor(*col)
    gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)

    car.rotation = (rx, 0, 1, 0)
    c.pos = v3((0, 2, -zpos - 8))

c = Camera(pos=v3((0, 0, -20)))


def on_draw():
    scene.render(c)


if __name__ == '__main__':
    window = pyglet.window.Window(
        width=WIDTH,
        height=HEIGHT
    )
    load()

    window.event(on_draw)
    pyglet.clock.schedule_interval(update, 1.0 / FPS)
    pyglet.app.run()
