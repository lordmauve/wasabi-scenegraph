from .shader import Shader


specular_shader = Shader(
    vert="""

uniform vec4 light_pos;

varying vec3 light;
varying vec3 normal;

void main(void)
{
    vec4 a = gl_Vertex;
    gl_Position = gl_ModelViewProjectionMatrix * a;
    normal = gl_Normal.xyz;
    light = (gl_ModelViewProjectionMatrix * light_pos).xyz;
}
""",
    frag="""

varying vec3 light;
varying vec3 normal;

const float specular_exponent = 10.0;
const float specularity = 0.6;

float phong_weightCalc(in vec3 frag_normal) {
    return max( 0.0, dot(
        frag_normal, normalize(light)
    ));
}

float specular(in vec3 frag_normal) {
    vec3 rlight = reflect(normalize(light), frag_normal);
    vec3 eye = vec3(0.0, 0.0, -1.0);
    return clamp(pow(dot(eye, rlight), specular_exponent), 0.0, 1.0) * specularity;
}

void main (void) {
    vec3 n = normalize(normal);
    float spec = specular(n);
    gl_FragColor = vec4(0.0, 1.0, 0.0, 1.0) * phong_weightCalc(n) +
   vec4(spec, spec, spec, spec);
}
"""
)


textured_specular = Shader(
    vert="""

uniform vec4 light_pos;

varying vec3 light;
varying vec3 normal;
varying vec2 uv;
varying vec3 eye;

void main(void)
{
    vec3 pos = vec3(gl_ModelViewMatrix * gl_Vertex);
    gl_Position = gl_ModelViewProjectionMatrix * gl_Vertex;
    eye = pos;
    normal = (gl_NormalMatrix * gl_Normal).xyz;
    light = light_pos.xyz;
    uv = gl_MultiTexCoord0.st;
}
""",
    frag="""
varying vec3 light;
varying vec3 normal;
varying vec2 uv;
varying vec3 eye;

const float ambient = 0.2;

uniform vec3 specularity;
uniform float specular_exponent;
uniform vec3 colour;
uniform sampler2D diffuse;
uniform int illum;

float phong_weightCalc(in vec3 frag_normal) {
    return max(0.0, dot(
        frag_normal, normalize(light)
    ) + ambient);
}

vec4 specular_calc(in vec3 eye, in vec3 frag_normal) {
    vec3 rlight = reflect(normalize(light), frag_normal);
    float spec = pow(max(dot(eye, rlight), 0.0), specular_exponent);
    return vec4(specularity * spec, spec);
}

void main (void) {
    vec4 mapcolour = texture2D(diffuse, uv);

    if (illum == 0) {
        gl_FragColor = mapcolour;
    } else {
        vec3 n = normalize(normal);
        vec4 spec = specular_calc(normalize(eye), n);

        vec3 diff = mapcolour.rgb * phong_weightCalc(n) * colour;
        gl_FragColor = vec4(diff, mapcolour.a) + spec;
    }
}
"""
)
textured_specular.bind_material_to_uniformf('Kd', 'colour')
textured_specular.bind_material_to_uniformf('Ns', 'specular_exponent')
textured_specular.bind_material_to_uniformf('Ks', 'specularity')
textured_specular.bind_material_to_uniformi('illum', 'illum')
textured_specular.bind_material_to_texture('map_Kd', 'diffuse')
