from shader import Shader

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

