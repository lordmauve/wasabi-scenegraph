from pyglet.graphics import Batch
from OpenGL.GL import *
from gletools import (
    Projection, Framebuffer, Texture, Depthbuffer,
    interval, quad, Matrix,
)

from .shader import Shader, ShaderGroup, MaterialGroup
from .lighting import Light


class Renderer(object):
    """Abstract class for rendering a scene."""
    def render(self, scene, camera):
        pass


class RenderPass(object):
    """Base class for a render pass."""
    def __init__(self, transparency=False, group=None):
        self.transparency = transparency
        self.group = group

    def filter(self, node):
        return self.transparency == node.is_transparent()

    def render(self, camera, objects):
        if self.group:
            self.group.set_state_recursive()
        for o in objects:
            if self.filter(o):
                o.draw(camera)
        if self.group:
            self.group.unset_state_recursive()


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
varying vec3 pos; // position of the fragment in screen space
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

        glEnable(GL_ALPHA_TEST)
        glAlphaFunc(GL_GREATER, 0.9)
        glBlendFunc(GL_ZERO, GL_ONE)
        glEnable(GL_POLYGON_OFFSET_FILL)
        glPolygonOffset(0.01, 1)

        depth_shader.bind()

        for o in objects:
            if self.filter(o):
                o.draw(camera)

        depth_shader.unbind()

        glDisable(GL_POLYGON_OFFSET_FILL)


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

        glEnable(GL_DEPTH_TEST)
        glDepthFunc(GL_LEQUAL)
        glAlphaFunc(GL_GREATER, 0.9)
        glBlendFunc(GL_SRC_ALPHA, GL_ZERO)

        # First pass writes depth, so write it with an offset
        glEnable(GL_POLYGON_OFFSET_FILL)
        glPolygonOffset(0.01, 1)
        glDepthMask(GL_TRUE)

        with fbo:
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
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
                glDisable(GL_POLYGON_OFFSET_FILL)
                glDepthMask(GL_FALSE)
                glBlendFunc(GL_SRC_ALPHA, GL_ONE)

            diffuse_lighting.unbind()
            glDepthMask(GL_TRUE)

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
    vec4 mapcolour = texture2D(diffuse, uv) * vec4(colour, 1.0);
    vec4 diffuse = vec4(1.0, 1.0, 1.0, 1.0);

    if (illum == 0) {
        gl_FragColor = mapcolour;
    } else {
        vec4 lighting = texture2DProj(lighting, proj * projuv);
        gl_FragColor = mapcolour * lighting;
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
        glEnable(GL_DEPTH_TEST)
        glDepthFunc(GL_LEQUAL)
        glEnable(GL_ALPHA_TEST)
        glAlphaFunc(GL_GREATER, 0.9)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        composite_shader.bind()

        composite_shader.bind_texture(
            'lighting', 0, self.lightingpass.texture.id
        )

        for o in objects:
            if self.filter(o):
                o.draw(camera)

        composite_shader.unbind()


class LightingAccumulationRenderer(object):
    def __init__(self):
        self.lighting = LightingPass()
        self.passes = [
            self.lighting,
            CompositePass(self.lighting),
            RenderPass(
                transparency=True
            )
        ]

    def prepare_model(self, model):
        if hasattr(model, 'draw'):
            return model
        batch = Batch()
        for m in model.meshes:
            self.prepare_mesh(m, batch)
        model.batch = batch
        model.draw = batch.draw
        return model

    def prepare_mesh(self, mesh, batch):
        mat = mesh.material
        mat.load_textures()

        l = mesh.to_list(batch, group=MaterialGroup(mat))
        mesh.list = l

    def render(self, scene, camera):
        self.lighting.ambient = scene.ambient
        glEnable(GL_TEXTURE_2D)
        glClearColor(1.0, 0, 0, 0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glDisable(GL_CULL_FACE)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_ALPHA_TEST)
        glAlphaFunc(GL_GREATER, 0.9)
        for p in self.passes:
            camera.set_matrix()
            p.render(camera, scene.objects)
