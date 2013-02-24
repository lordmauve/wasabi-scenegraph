from __future__ import division

import pyglet
from pyglet import gl
from pyglet.window import key
from pyglet.graphics import TextureGroup

from sphere import Sphere
from shaderlib import specular_shader, textured_specular

from scenegraph import ModelNode, Scene, Camera, ShaderGroup, v3


FPS = 60
WIDTH = 800
HEIGHT = 600


pyglet.resource.path = ['textures']


def load_texture(name):
    image = pyglet.image.load('textures/' + name)
    return image.get_mipmapped_texture()


earthtex = load_texture('earth.png')
startex = load_texture('stars.png')


# Create spheres with the correct relative radii
earth = Sphere()
moon = Sphere(radius=1734.4 / 6378.1)

stars = Sphere(radius=5000)


scene = Scene()



def load():
    global earthmodel
    group = ShaderGroup(textured_specular)
    group.uniformf('light_pos', -100, 50, -30, 0)

    batch = pyglet.graphics.Batch()
    earth.to_list(batch, TextureGroup(earthtex, parent=group))

    earthmodel = ModelNode(batch)
    scene.add(earthmodel)

    batch = pyglet.graphics.Batch()
    stars.to_list(batch, TextureGroup(startex))

    starmodel = ModelNode(batch)
    scene.add(starmodel)




zpos = 10
rx, ry = 0, 0
tx, ty = 0, 2


def update(dt):
    global zpos, rx, ry
    rx += 10 * dt
    zpos *= 0.5 ** dt
    col = (88 / 255, 156 / 255, 163 / 255, 1)
    gl.glClearColor(*col)
    gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)

    earthmodel.rotation = (rx, 0, 1, 0)
    c.pos = v3((0, 0.5, -zpos - 3))

c = Camera(pos=v3((0, 0, -20)))


def on_draw():
    gl.glEnable(gl.GL_TEXTURE_2D)
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
