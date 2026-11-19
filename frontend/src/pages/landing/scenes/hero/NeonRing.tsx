import { useFrame } from "@react-three/fiber";
import { useEffect, useMemo, useRef } from "react";
import * as THREE from "three";
import { clamp01, easeInOutCubic, heroState } from "./heroState";

const RING_RADIUS = 1.62;
const ARC = Math.PI * 1.7; // an open arc, not a full ring

const VERTEX = /* glsl */ `
  varying vec2 vUv;
  void main() {
    vUv = uv;
    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
  }
`;

// Red to magenta to blue along the arc; this gradient is reserved for the hero ring.
const FRAGMENT = /* glsl */ `
  varying vec2 vUv;
  uniform float uAlpha;
  uniform float uBoost;
  uniform float uTime;
  vec3 neon(float t) {
    vec3 red = vec3(0.898, 0.090, 0.122);
    vec3 magenta = vec3(0.84, 0.09, 0.62);
    vec3 blue = vec3(0.18, 0.36, 1.0);
    return t < 0.5 ? mix(red, magenta, t * 2.0) : mix(magenta, blue, (t - 0.5) * 2.0);
  }
  void main() {
    float t = clamp(vUv.x, 0.0, 1.0);
    float taper = smoothstep(0.0, 0.12, t) * (1.0 - smoothstep(0.86, 1.0, t));
    float pulse = 0.88 + 0.12 * sin(t * 16.0 - uTime * 1.5);
    gl_FragColor = vec4(neon(t) * uBoost * pulse, uAlpha * taper);
  }
`;

// A hot core plus progressively wider, fainter shells. Additively blended they read as a
// glow without a post-processing pass (cheaper, and one less dependency).
const LAYERS = [
  { tube: 0.03, alpha: 1.0, boost: 1.7 },
  { tube: 0.058, alpha: 0.46, boost: 1.25 },
  { tube: 0.1, alpha: 0.22, boost: 1.1 },
  { tube: 0.17, alpha: 0.1, boost: 1.0 },
  { tube: 0.28, alpha: 0.05, boost: 1.0 },
];

export function NeonRing() {
  const outer = useRef<THREE.Group>(null);
  const inner = useRef<THREE.Group>(null);

  const materials = useMemo(
    () =>
      LAYERS.map(
        ({ alpha, boost }) =>
          new THREE.ShaderMaterial({
            uniforms: { uAlpha: { value: alpha }, uBoost: { value: boost }, uTime: { value: 0 } },
            vertexShader: VERTEX,
            fragmentShader: FRAGMENT,
            transparent: true,
            blending: THREE.AdditiveBlending,
            depthWrite: false,
            side: THREE.DoubleSide,
          })
      ),
    []
  );

  useEffect(() => () => materials.forEach((m) => m.dispose()), [materials]);

  useFrame((state) => {
    const p = clamp01(heroState.progress);
    const eased = easeInOutCubic(p);
    materials.forEach((m) => {
      m.uniforms.uTime.value = state.clock.elapsedTime;
    });
    if (inner.current) {
      // idle drift, then a full sweep around the globe as the page scrolls
      inner.current.rotation.z = 0.7 + state.clock.elapsedTime * 0.1 + p * Math.PI * 1.15;
    }
    if (outer.current) {
      // the ring only appears once the globe has formed
      const ringIn = THREE.MathUtils.smoothstep(heroState.morph, 0.6, 1);
      outer.current.scale.setScalar(THREE.MathUtils.lerp(1, 1.5, eased) * Math.max(0.0001, ringIn));
    }
  });

  return (
    <group ref={outer} rotation={[1.18, -0.3, -0.42]}>
      <group ref={inner}>
        {LAYERS.map((layer, i) => (
          <mesh key={layer.tube} material={materials[i]}>
            <torusGeometry args={[RING_RADIUS, layer.tube, 18, 260, ARC]} />
          </mesh>
        ))}
      </group>
    </group>
  );
}
