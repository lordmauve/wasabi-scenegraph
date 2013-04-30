import pyglet
from gletools import (
    Projection, Framebuffer, Texture, Depthbuffer,
    interval, quad, Group, Matrix,
)
from gletools.gl import *

from euclid import Point3
from .scenegraph import RenderPass, ShaderGroup
from .shader import Shader


class Light(object):
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


depth_shader = Shader(
    vert="""
varying vec2 uv;

void main(void)
{
    vec4 a = gl_Vertex;
    gl_Position = gl_ModelViewProjectionMatrix * a;
    uv = gl_MultiTexCoord0.st;
}
""",
    frag="""

varying vec2 uv;
uniform sampler2D diffuse;

void main (void) {
    gl_FragColor = vec4(0.0, 0.0, 0.0, texture2D(diffuse, uv).a);
}
"""
)
depth_shader.bind_material_to_texture('map_Kd', 'diffuse')


diffuse_lighting = Shader(
    vert="""

varying vec3 normal;
varying vec3 pos; // position of the fragment in world space
varying vec2 uv;

//uniform mat4 inv_view;

void main(void)
{
    vec4 a = gl_Vertex;
    gl_Position = gl_ModelViewProjectionMatrix * a;
    normal = (gl_NormalMatrix * gl_Normal).xyz;
    pos = (gl_ModelViewMatrix * a).xyz;
    uv = gl_MultiTexCoord0.st;
}
""",
    frag="""

varying vec3 normal;
varying vec3 pos;
varying vec2 uv;

uniform vec4 ambient;
uniform int num_lights;
uniform vec4 colours[8];
uniform vec4 positions[8];
uniform float intensities[8];
uniform float falloffs[8];
uniform sampler2D diffuse;


float phong_weightCalc(in vec3 frag_normal, in int lnum) {
    vec3 light = positions[lnum].xyz - pos;
    float intensity = intensities[lnum];

    float diffuse = max(0.0, dot(
        frag_normal, normalize(light)
    ));

    float dist = intensity / pow(1.0 + length(light), falloffs[lnum]);
    return diffuse * dist;
}

void main (void) {
    int i;
    float weight;
    vec3 n = normalize(normal);
    vec4 colour = ambient;
    vec4 mapcolour = texture2D(diffuse, uv);

    for (i = 0; i < num_lights; i++) {
        weight = phong_weightCalc(n, i);
        colour += colours[i] * weight;
    }
    gl_FragColor = vec4(colour.xyz, mapcolour.a);
}
"""
)
diffuse_lighting.bind_material_to_texture('map_Kd', 'diffuse')


class DepthOnlyPass(object):
    def __init__(self):
        self.currentviewport = None
        self.fbo = None
        self.texture = None

    def filter(self, node):
        return not node.is_transparent()

    def get_projected_texture(self, viewport):
        if viewport == self.currentviewport:
            return self.fbo

        width, height = viewport

        if self.texture:
            self.texture.delete()
        self.fbo = Framebuffer(self.texture)
        return self.fbo

    def render(self, camera, objects):
        lights = [o for o in objects if isinstance(o, Light)]
        if not lights:
            return

        gl.glEnable(gl.GL_ALPHA_TEST)
        gl.glAlphaFunc(gl.GL_GREATER, 0.9)
        gl.glBlendFunc(gl.GL_ZERO, gl.GL_ONE)
        gl.glEnable(gl.GL_POLYGON_OFFSET_FILL)
        gl.glPolygonOffset(0.01, 1)

        depth_shader.bind()

        for o in objects:
            if self.filter(o):
                o.draw(camera)

        depth_shader.unbind()

        gl.glDisable(gl.GL_POLYGON_OFFSET_FILL)


class LightingPass(object):
    def __init__(self, ambient=(0, 0, 0, 1)):
        self.ambient = ambient
        self.currentviewport = None
        self.fbo = None
        self.texture = None

    def filter(self, node):
        return not node.is_transparent()

    def get_fbo(self, viewport):
        if viewport == self.currentviewport:
            return self.fbo
        self.currentviewport = viewport

        width, height = viewport

        if self.texture:
            self.texture.delete()
            # FIDME: delete self.depth
        self.texture = Texture(width, height, format=GL_RGBA32F)
        self.fbo = Framebuffer(self.texture)
        self.depth = Depthbuffer(width, height)
        self.fbo.depth = self.depth
        return self.fbo

    def transform_lights(self, camera, positions):
        out = []
        view_matrix = camera.get_view_matrix()
        for vec in positions:
            x, y, z = view_matrix * vec
            out.append((x, y, z, 0))
        return out

    def render(self, camera, objects):
        lights = [o for o in objects if isinstance(o, Light)]

        fbo = self.get_fbo(camera.viewport)

        gl.glEnable(GL_DEPTH_TEST)
        gl.glDepthFunc(gl.GL_LEQUAL)
        gl.glAlphaFunc(gl.GL_GREATER, 0.9)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ZERO)

        # First pass writes depth, so write it with an offset
        gl.glEnable(gl.GL_POLYGON_OFFSET_FILL)
        gl.glPolygonOffset(0.01, 1)
        gl.glDepthMask(gl.GL_TRUE)

        with fbo:
            gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
            if not lights:
                return
            diffuse_lighting.bind()
            diffuse_lighting.uniformf('ambient', *self.ambient)

#            diffuse_lighting.uniform_matrixf('inv_view', camera.get_view_matrix().inverse())

            while lights:
                ls = lights[:8]
                lights = lights[8:]

                diffuse_lighting.uniform4fv('colours', [l.colour for l in ls])
#                diffuse_lighting.uniform4fv('positions', [l.pos for l in ls])
                diffuse_lighting.uniform4fv('positions',
                    self.transform_lights(camera, (l.pos for l in ls))
                )
                diffuse_lighting.uniform1fv(
                    'intensities', [l.intensity for l in ls])
                diffuse_lighting.uniform1fv(
                    'falloffs', [l.falloff for l in ls])
                diffuse_lighting.uniformi('num_lights', len(ls))
                for o in objects:
                    if self.filter(o):
                        o.draw(camera)

                # Subsequent passes are drawn without writing to the z-buffer
                gl.glDisable(gl.GL_POLYGON_OFFSET_FILL)
                gl.glDepthMask(gl.GL_FALSE)
                gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE)

            diffuse_lighting.unbind()
            gl.glDepthMask(gl.GL_TRUE)

    def __del__(self):
        if self.texture:
            self.texture.delete()


composite_shader = Shader(
    vert="""
varying vec2 uv;
varying vec4 projuv;

void main(void)
{
    vec3 pos = vec3(gl_ModelViewMatrix * gl_Vertex);
    vec4 transformed = gl_ModelViewProjectionMatrix * gl_Vertex;
    gl_Position = transformed;
    uv = gl_MultiTexCoord0.st;
    projuv = transformed;
}
""",
    frag="""
varying vec2 uv;
varying vec4 projuv;

uniform vec3 colour;
uniform sampler2D diffuse;
uniform sampler2D lighting;
uniform int illum;

const mat4 proj = mat4(
    0.5, 0.0, 0.0, 0.0,
    0.0, 0.5, 0.0, 0.0,
    0.0, 0.0, 0.0, 0.0,
    0.5, 0.5, 0.0, 1.0
);

void main (void) {
    vec4 mapcolour = texture2D(diffuse, uv);
    vec4 diffuse = vec4(1.0, 1.0, 1.0, 1.0);

    vec4 lighting = texture2DProj(lighting, proj * projuv);

    if (illum == 0) {
        gl_FragColor = mapcolour;
    } else {
        gl_FragColor = mapcolour * lighting * vec4(colour, 1.0);
    }
}
""",
    reserved_textures=1
)
composite_shader.bind_material_to_uniformf('Kd', 'colour')
composite_shader.bind_material_to_uniformi('illum', 'illum')
composite_shader.bind_material_to_texture('map_Kd', 'diffuse')


class CompositePass(object):
    def __init__(self, lightingpass):
        self.lightingpass = lightingpass

    def filter(self, node):
        return not node.is_transparent()

    def render(self, camera, objects):
        gl.glEnable(GL_DEPTH_TEST)
        gl.glDepthFunc(gl.GL_LEQUAL)
        gl.glEnable(gl.GL_ALPHA_TEST)
        gl.glAlphaFunc(gl.GL_GREATER, 0.9)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
        composite_shader.bind()

        composite_shader.bind_texture(
            'lighting', 0, self.lightingpass.texture.id
        )

        for o in objects:
            if self.filter(o):
                o.draw(camera)

        composite_shader.unbind()
