from pyglet.graphics import Batch
from OpenGL.GL import *

from .shader import Shader, MaterialGroup
from .lighting import Light, Sunlight, BaseLight


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


lighting_shader = Shader(
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

uniform int num_lights;
uniform vec4 colours[8];
uniform vec4 positions[8];
uniform float intensities[8];
uniform float falloffs[8];
uniform sampler2D diffuse_tex;
uniform vec3 diffuse_colour;
uniform vec4 specular;
uniform vec4 ambient;
uniform float dissolve;
uniform float specular_exponent;
uniform float transmit;
uniform int illum;

vec3 calc_light(in vec3 frag_normal, in int lnum, in vec3 diffuse) {
    vec4 light = positions[lnum];
    float intensity = intensities[lnum];
    vec3 light_colour = colours[lnum].rgb;

    vec3 lightvec;

    if (light.w > 0.0) {
        lightvec = light.xyz - pos;

        // Use quadratic attenuation
        float lengthsq = dot(lightvec, lightvec);
        intensity /= 1.0 + lengthsq * falloffs[lnum];

        lightvec = normalize(lightvec);
    } else {
        lightvec = light.xyz;
    }

    float diffuse_component = dot(
        frag_normal, lightvec
    );
    diffuse_component = max(0.0, diffuse_component) - transmit * min(0.0, diffuse_component);

    float specular_component = 0.0;
    if (diffuse_component > 0.0) {
        vec3 rlight = reflect(lightvec, frag_normal);
        vec3 eye = normalize(pos);
        specular_component = pow(max(0.0, dot(eye, rlight)), specular_exponent);
    }

    return intensity * light_colour * (
        diffuse_component * diffuse +
        specular_component * specular.rgb
    );
}

void main (void) {
    int i;
    float weight;
    vec3 n = normalize(normal);
    vec3 colour = vec3(0, 0, 0);
    vec4 mapcolour = texture2D(diffuse_tex, uv);
    vec3 basecolour = mapcolour.rgb * diffuse_colour;

    if (illum == 0) {
        colour = basecolour;
    } else {
        colour += basecolour * ambient.rgb;

        for (i = 0; i < num_lights; i++) {
            colour += calc_light(n, i, basecolour);
        }
    }
    gl_FragColor = vec4(colour.xyz, mapcolour.a * dissolve);
}
"""
)
lighting_shader.bind_material_to_texture('map_Kd', 'diffuse_tex')
lighting_shader.bind_material_to_uniformf('Kd', 'diffuse_colour')
lighting_shader.bind_material_to_uniformf('Ks', 'specular')
lighting_shader.bind_material_to_uniformf('Ns', 'specular_exponent')
lighting_shader.bind_material_to_uniformf('d', 'dissolve')
lighting_shader.bind_material_to_uniformf('transmit', 'transmit')
lighting_shader.bind_material_to_uniformi('illum', 'illum')


class LightingPass(object):
    def __init__(self, ambient=(0, 0, 0, 1)):
        self.ambient = ambient
        self.currentviewport = None
        self.fbo = None
        self.lightbuf = self.depthbuf = None

    def get_fbo(self, viewport):
        if viewport == self.currentviewport:
            return self.fbo
        self.currentviewport = viewport

        width, height = viewport

        if not self.fbo:
            self.fbo = glGenFramebuffers(1)
            self.lightbuf = glGenTextures(1)
            self.depthbuf = glGenRenderbuffers(1)

        glBindFramebuffer(GL_FRAMEBUFFER, self.fbo)
        glBindTexture(GL_TEXTURE_2D, self.lightbuf)
        #glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        #glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
        #glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        #glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexImage2D(
            GL_TEXTURE_2D, 0, GL_RGBA32F,
            width, height,
            0,
            GL_RGBA, GL_FLOAT,
            None
        )
        glFramebufferTexture2D(
            GL_FRAMEBUFFER,
            GL_COLOR_ATTACHMENT0,
            GL_TEXTURE_2D,
            self.lightbuf,
            0
        )
        glBindRenderbuffer(GL_RENDERBUFFER, self.depthbuf)
        glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH_COMPONENT16, width, height)
        glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_RENDERBUFFER, self.depthbuf)
        assert glCheckFramebufferStatus(GL_FRAMEBUFFER) == GL_FRAMEBUFFER_COMPLETE, \
            "Framebuffer is not complete!"
        return self.fbo

    def render(self, camera, objects):
        lights = [o for o in objects if isinstance(o, BaseLight)]
        glPushAttrib(GL_ALL_ATTRIB_BITS)
        glClear(GL_DEPTH_BUFFER_BIT)

        standard_objects = []
        shader_objects = []
        for o in objects:
            if o.is_transparent():
                continue
            if hasattr(o, 'shader'):
                shader_objects.append(o)
            else:
                standard_objects.append(o)
        self.render_objects(camera, lights, standard_objects, shader=lighting_shader)

        for o in shader_objects:
            self.render_objects(camera, lights, [o], shader=o.shader)

        glPopAttrib()

        glEnable(GL_DEPTH_TEST)
        glDepthFunc(GL_LEQUAL)

    def render_objects(self, camera, lights, objects, shader=lighting_shader):
        lights = lights[:]
        glEnable(GL_DEPTH_TEST)
        glDepthFunc(GL_LEQUAL)
        glBlendFunc(GL_SRC_ALPHA, GL_ZERO)

        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)

        # First pass writes depth, so write it with an offset
        glEnable(GL_POLYGON_OFFSET_FILL)
        glPolygonOffset(0.01, 1)
        glDepthMask(GL_TRUE)

        #glBindFramebuffer(GL_FRAMEBUFFER, fbo)
        if not lights:
            return

        shader.bind()
        shader.uniformf('ambient', *self.ambient)
        view_matrix = camera.get_view_matrix()

        while lights:
            ls = lights[:8]
            lights = lights[8:]

            light_pos = []
            for l in ls:
                x, y, z = view_matrix * l._pos
                light_pos.append((x, y, z, l.w))

            shader.uniform4fv('colours', [l.colour for l in ls])
            shader.uniform4fv('positions', light_pos)
            shader.uniform1fv(
                'intensities', [l.intensity for l in ls])
            shader.uniform1fv(
                'falloffs', [l.falloff for l in ls])
            shader.uniformi('num_lights', len(ls))
            for o in objects:
                o.draw(camera)

            if not lights:
                break

            # Subsequent passes are drawn without writing to the z-buffer
            glDisable(GL_POLYGON_OFFSET_FILL)
            glDepthMask(GL_FALSE)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE)
            shader.uniformf('ambient', 0, 0, 0, 0)

        shader.unbind()
        glDepthMask(GL_TRUE)
        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    def __del__(self):
        if self.fbo:
            glDeleteTextures([self.lightbuf, self.depthbuf])
            glDeleteFramebuffers([self.fbo])
            self.fbo = None


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
    vec4 mapcolour = vec4(colour, 1.0);

    if (illum == 0) {
        gl_FragColor = mapcolour * texture2D(diffuse, uv);
    } else {
        vec4 lighting = texture2DProj(lighting, proj * projuv);
        gl_FragColor = lighting;
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
        composite_shader.bind()

        composite_shader.bind_texture(
            'lighting', 0, self.lightingpass.lightbuf
        )

        for o in objects:
            if self.filter(o):
                o.draw(camera)

        composite_shader.unbind()


class LightingAccumulationRenderer(object):
    def __init__(self):
        self.lighting = LightingPass()
#        self.composite = CompositePass(self.lighting)
        self.passes = [
            self.lighting,
            #self.composite,
            RenderPass(
                transparency=True
            )
        ]

    def prepare_model(self, model):
        if hasattr(model, 'draw'):
            return model
        batch = Batch()
        for m in model.meshes:
            if not hasattr(m, 'list'):
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

        flags = GL_ALL_ATTRIB_BITS
        glPushAttrib(flags)

        glEnable(GL_TEXTURE_2D)
        glClear(GL_DEPTH_BUFFER_BIT)
        glEnable(GL_CULL_FACE)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        camera.set_matrix()
        for p in self.passes:
            p.render(camera, scene.objects)
        glPopAttrib()
