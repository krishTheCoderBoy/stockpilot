import { Canvas, useFrame } from "@react-three/fiber";
import { useMemo, useRef } from "react";
import * as THREE from "three";
import { oceanState } from "./oceanState";

const VERTEX = /* glsl */ `
  varying vec2 vUv;
  void main() {
    vUv = uv;
    gl_Position = vec4(position.xy, 0.0, 1.0);
  }
`;

// Open water drawn entirely in the shader: two layers of drifting, warped noise give the swell and
// the bright, thin caustic lines that run across it, with a few sun glints on the crests.
const FRAGMENT = /* glsl */ `
  uniform float uTime;
  uniform float uOffset;
  uniform vec2 uRes;
  varying vec2 vUv;

  float hash(vec2 p) {
    p = fract(p * vec2(123.34, 456.21));
    p += dot(p, p + 45.32);
    return fract(p.x * p.y);
  }

  float noise(vec2 p) {
    vec2 i = floor(p);
    vec2 f = fract(p);
    f = f * f * (3.0 - 2.0 * f);
    float a = hash(i);
    float b = hash(i + vec2(1.0, 0.0));
    float c = hash(i + vec2(0.0, 1.0));
    float d = hash(i + vec2(1.0, 1.0));
    return mix(mix(a, b, f.x), mix(c, d, f.x), f.y);
  }

  float fbm(vec2 p) {
    float v = 0.0;
    float a = 0.5;
    for (int i = 0; i < 5; i++) {
      v += a * noise(p);
      p = p * 2.03 + vec2(17.1, 9.2);
      a *= 0.5;
    }
    return v;
  }

  void main() {
    float aspect = uRes.x / uRes.y;
    vec2 p = vec2((vUv.x - 0.5) * aspect, vUv.y - 0.5);
    p.y += uOffset * 0.9; // the camera follows the ship, so the water slides past
    float t = uTime * 0.06;

    // slow swell
    vec2 q = p * 1.6 + vec2(t, -t * 0.7);
    float swell = fbm(q + fbm(q * 1.3 + t));

    // caustic-like bright lines: ridges of a second, finer noise
    vec2 r = p * 5.0 + vec2(-t * 1.6, t * 1.1) + swell * 1.4;
    float ridge = 1.0 - abs(fbm(r) * 2.0 - 1.0);
    float lines = pow(ridge, 3.2);

    vec3 deep = vec3(0.04, 0.42, 0.48);
    vec3 mid = vec3(0.07, 0.58, 0.63);
    vec3 shallow = vec3(0.22, 0.74, 0.74);
    vec3 col = mix(deep, mid, smoothstep(0.25, 0.75, swell));
    col = mix(col, shallow, smoothstep(0.6, 0.95, swell) * 0.55);
    col += vec3(0.62, 0.95, 0.93) * lines * 0.12;
    col += vec3(1.0) * smoothstep(0.985, 1.0, ridge * swell * 1.25) * 0.28;

    float vig = smoothstep(1.25, 0.35, length((vUv - 0.5) * vec2(aspect, 1.0)));
    col *= mix(0.78, 1.0, vig);
    gl_FragColor = vec4(col, 1.0);
  }
`;

function Water() {
  const uniforms = useMemo(
    () => ({ uTime: { value: 0 }, uOffset: { value: 0 }, uRes: { value: new THREE.Vector2(1, 1) } }),
    []
  );
  const material = useRef<THREE.ShaderMaterial>(null);

  useFrame((state) => {
    const m = material.current;
    if (!m) return;
    // wall-clock time: scene 5's and scene 6's canvases show the same ripple at the same moment
    m.uniforms.uTime.value = (performance.now() / 1000) % 3600;
    m.uniforms.uOffset.value = oceanState.offset;
    m.uniforms.uRes.value.set(state.size.width, state.size.height);
  });

  return (
    <mesh frustumCulled={false}>
      <planeGeometry args={[2, 2]} />
      <shaderMaterial
        ref={material}
        uniforms={uniforms}
        vertexShader={VERTEX}
        fragmentShader={FRAGMENT}
        depthTest={false}
        depthWrite={false}
      />
    </mesh>
  );
}

// Default export so the scenes can load this (and three.js) lazily.
export default function OceanCanvas({ active, onReady }: { active: boolean; onReady?: () => void }) {
  return (
    <Canvas
      dpr={[1, 1.25]}
      gl={{ antialias: false, alpha: false, powerPreference: "high-performance" }}
      frameloop={active ? "always" : "never"}
      style={{ position: "absolute", inset: 0 }}
      onCreated={() => onReady?.()}
    >
      <Water />
    </Canvas>
  );
}
