#version 120

uniform sampler2D sceneTexture;
uniform float intensity;
uniform float threshold;

void main() {
    // Sample the color of the texture
    vec4 color = texture2D(sceneTexture, gl_TexCoord[0].st);

    // Extract bright colors by applying a threshold
    if (length(color.rgb) < threshold) {
        discard; // Discard dark parts that shouldn't contribute to the bloom effect
    }

    // Multiply bright colors by intensity to amplify the bloom effect
    gl_FragColor = color * intensity;
}
