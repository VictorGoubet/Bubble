#version 330 core

uniform sampler1D circles;
uniform vec2 u_resolution;
uniform int num_circles;
uniform float maxSpeed;
uniform float u_time;

out vec4 fragColor;

float circle(vec2 px, vec3 cp) {
    vec2 dist = px - cp.xy;
    float norm = sqrt(dist.x * dist.x + dist.y * dist.y);
    return norm < cp.z ? 0.0 : 1.0;
}

void main() {
    float px_type = 1.0;
    float speed_color = 1;
    vec2 px = gl_FragCoord.xy / u_resolution.xy;
    float inv_num_circles = 1.0 / float(num_circles);

    for(int i = 0; i < num_circles; i++) {
        vec4 c = texture(circles, (float(i) + 0.5) * inv_num_circles);
        px_type *= circle(px, c.xyz);
        if(px_type == 0.0) {
            speed_color = c[3];
            break;
        }
    }

    // speed gradient for bubble
    float factor = clamp(speed_color / maxSpeed, 0.0, 1.0);
    vec3 slow_color = vec3(0.47, 0.12, 0.94);
    vec3 fast_color = vec3(0.91, 0.38, 0.0);

    vec3 back_ground_color1 = vec3(0.75, 0.46, 0.91);
    vec3 back_ground2_color2 = vec3(0.89, 0.64, 0.84);

    // oscillate background color
    float blend_factor = sin(u_time) * 0.5 + 0.5;
    vec3 color = mix(back_ground_color1, back_ground2_color2, blend_factor);

    if(px_type == 0.0) {
        color = mix(slow_color, fast_color, factor);
    }

    fragColor = vec4(color, 1.0);
}
