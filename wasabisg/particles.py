from OpenGL.GL import *
import pyglet.graphics

from lepton import ParticleGroup
from lepton.system import ParticleSystem
from lepton.renderer import BillboardRenderer
from lepton.texturizer import SpriteTexturizer

from .shader import Shader


class ParticleSystemNode(object):
    """Maintain a group of particles in the system default particle system."""
    def __init__(self, group=None):
        """Create a particle system with the given pyglet Group."""
        self.system = ParticleSystem()
        self.group = group or ParticleDisplayGroup()
        self.textures = set()

    def update(self, dt):
        self.system.update(dt)

    def is_transparent(self):
        return True

    def create_group(self, controllers, texture):
        particlegroup = ParticleGroup(controllers=controllers, system=self.system)
        texturizer = SpriteTexturizer(texture.id)
        particlegroup.renderer = BillboardRenderer(texturizer)
        self.textures.add(texture)  # hold a reference to this, otherwise it will get deleted
        return particlegroup

    def draw(self, camera):
        if self.group:
            self.group.set_state_recursive()
        self.system.draw()
        if self.group:
            self.group.unset_state_recursive()


particle_shader = Shader(
    vert="""

varying vec2 uv;
varying vec4 colour;

void main(void)
{
    vec4 a = gl_Vertex;
    gl_Position = gl_ModelViewProjectionMatrix * a;
    uv = gl_MultiTexCoord0.st;
    colour = gl_Color;
}
""",
    frag="""

uniform sampler2D diffuse;

varying vec2 uv;
varying vec4 colour;

void main (void) {
    vec4 mapcolour = texture2D(diffuse, uv);
    gl_FragColor = mapcolour * colour;
}
"""
)


class ParticleDisplayGroup(pyglet.graphics.Group):
    def set_state(self):
        glDepthMask(GL_FALSE)
        particle_shader.bind()
        glActiveTexture(GL_TEXTURE0)
        particle_shader.uniformi('diffuse', 0)

    def unset_state(self):
        particle_shader.unbind()
        glDepthMask(GL_TRUE)
