from __future__ import division

import pyglet
from pyglet import gl
from pyglet.window import key

from objloader import Mesh
from oldobjloader import OBJ
from shader import Shader


FPS = 60
WIDTH = 800
HEIGHT = 600


#plain_shader = Shader(
#    vert="""
#void main(void)
#{
#    vec4 a = gl_Vertex;
#    gl_Position = gl_ModelViewProjectionMatrix * a;
#}
#""",
#    frag="""
#void main (void)
#{
#   gl_FragColor = vec4(0.0, 1.0, 0.0, 1.0);
#}
#"""
#)

mesh = None
batch = None


def load():
    global mesh, batch, obj
    mesh = Mesh.load_obj('car.obj')
    batch = pyglet.graphics.Batch()
    mesh.to_list(batch)

    obj = OBJ('car.obj', False)



zpos = 10
rx, ry = 0, 0
tx, ty = 0, 2


def update(dt):
    global zpos, rx, ry
    rx += 10 * dt
    #zpos += 0.1 * dt
    c = (88 / 255, 156 / 255, 163 / 255, 1)
    gl.glClearColor(*c)
    gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)

    gl.glMatrixMode(gl.GL_PROJECTION)
    gl.glLoadIdentity()
    gl.gluPerspective(90.0, WIDTH / float(HEIGHT), 1, 1000.0)
    gl.glMatrixMode(gl.GL_MODELVIEW)
    gl.glLoadIdentity()

    def vec(*args):
        return (gl.GLfloat * len(args))(*args)

    gl.glEnable(gl.GL_LIGHTING)
    gl.glLightfv(gl.GL_LIGHT0, gl.GL_POSITION, vec(-100, 50, -30, 0.0))
    gl.glLightfv(gl.GL_LIGHT0, gl.GL_AMBIENT, vec(0.2, 0.2, 0.2, 1.0))
    gl.glLightfv(gl.GL_LIGHT0, gl.GL_DIFFUSE, vec(1.0, 1.0, 1.0, 1.0))
    gl.glEnable(gl.GL_LIGHT0)
    gl.glEnable(gl.GL_COLOR_MATERIAL)
    gl.glEnable(gl.GL_DEPTH_TEST)
    gl.glShadeModel(gl.GL_SMOOTH)

    gl.glTranslatef(-tx, -ty, -zpos)
    gl.glRotatef(ry, 1, 0, 0)
    gl.glRotatef(rx, 0, 1, 0)

    gl.glColor3f(1.0, 0, 0)
    #plain_shader.bind()
    batch.draw()
    #plain_shader.unbind()

    #gl.glCallList(obj.gl_list)


if __name__ == '__main__':
    window = pyglet.window.Window(
        width=WIDTH,
        height=HEIGHT
    )
    load()

    pyglet.clock.schedule_interval(update, 1.0 / FPS)
    pyglet.app.run()
