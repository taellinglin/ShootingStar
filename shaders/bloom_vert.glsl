#version 120

uniform sampler2D sceneTexture;
uniform float intensity;

void main() {
    vec4 color = texture2D(sceneTexture, gl_TexCoord[0].st);
    gl_FragColor = color * intensity;  // Simple bloom effect with intensity
}
