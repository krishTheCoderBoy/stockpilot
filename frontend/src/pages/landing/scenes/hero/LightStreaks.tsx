import { useFrame } from "@react-three/fiber";
import { useEffect, useMemo, useRef } from "react";
import * as THREE from "three";
import { clamp01, heroState } from "./heroState";

const SPAN = 16; // how far a streak travels before it loops

interface Streak {
  y: number;
  z: number;
  length: number;
  width: number;
  speed: number;
  phase: number;
  tilt: number;
  direction: 1 | -1;
  color: [number, number, number];
}

const WHITE: [number, number, number] = [1, 1, 1];
const RED: [number, number, number] = [0.898, 0.09, 0.122];

// A handful of fast, thin streaks. White and red only: the neon gradient belongs to the ring.
const STREAKS: Streak[] = [
  { y: 1.5, z: 0.6, length: 3.4, width: 0.011, speed: 0.11, phase: 0.1, tilt: -0.32, direction: 1, color: WHITE },
  { y: -1.0, z: 0.8, length: 2.5, width: 0.013, speed: 0.15, phase: 0.55, tilt: -0.27, direction: 1, color: RED },
  { y: 0.3, z: 0.2, length: 4.2, width: 0.008, speed: 0.08, phase: 0.8, tilt: 0.22, direction: -1, color: WHITE },
  { y: -1.9, z: 1.0, length: 2.1, width: 0.009, speed: 0.2, phase: 0.3, tilt: -0.4, direction: 1, color: WHITE },
  { y: 2.1, z: 0.0, length: 2.9, width: 0.008, speed: 0.13, phase: 0.9, tilt: 0.3, direction: -1, color: RED },
];

const VERTEX = /* glsl */ `
  varying vec2 vUv;
  void main() {
    vUv = uv;
    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
  }
`;

// Bright head at uv.x = 1, fading to nothing at the tail.
const FRAGMENT = /* glsl */ `
  varying vec2 vUv;
  uniform vec3 uColor;
  uniform float uOpacity;
  void main() {
    float body = pow(vUv.x, 3.0);
    float head = smoothstep(1.0, 0.985, vUv.x);
    float across = 1.0 - abs(vUv.y - 0.5) * 2.0;
    gl_FragColor = vec4(uColor, body * head * across * uOpacity);
  }
`;

export function LightStreaks() {
  const meshes = useRef<Array<THREE.Mesh | null>>([]);

  const materials = useMemo(
    () =>
      STREAKS.map(
        ({ color }) =>
          new THREE.ShaderMaterial({
            uniforms: { uColor: { value: new THREE.Color(...color) }, uOpacity: { value: 0.85 } },
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
    // streaks fade away as the globe closes in
    const fade = (1 - clamp01((heroState.progress - 0.35) / 0.3)) * THREE.MathUtils.smoothstep(heroState.morph, 0.6, 1);
    STREAKS.forEach((streak, i) => {
      const mesh = meshes.current[i];
      if (!mesh) return;
      const t = (state.clock.elapsedTime * streak.speed + streak.phase) % 1;
      mesh.position.x = streak.direction * (t * SPAN - SPAN / 2);
      materials[i].uniforms.uOpacity.value = 0.85 * fade;
    });
  });

  return (
    <>
      {STREAKS.map((streak, i) => (
        <group key={i} position={[0, streak.y, streak.z]} rotation={[0, 0, streak.tilt]}>
          <mesh
            ref={(node) => {
              meshes.current[i] = node;
            }}
            material={materials[i]}
            rotation={[0, streak.direction === 1 ? 0 : Math.PI, 0]}
          >
            <planeGeometry args={[streak.length, streak.width * 6]} />
          </mesh>
        </group>
      ))}
    </>
  );
}
