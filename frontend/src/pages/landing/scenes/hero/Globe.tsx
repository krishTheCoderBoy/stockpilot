import { useFrame } from "@react-three/fiber";
import { useMemo, useRef } from "react";
import * as THREE from "three";
import { buildLandPoints } from "./globePoints";
import { heroState } from "./heroState";

// Candidate points on the sphere; roughly a third land on land, giving ~1.5 degree spacing.
const CANDIDATES = 16000;
const GLOBE_RADIUS = 1;

const DOT_VERTEX = /* glsl */ `
  uniform float uScale; // pixels per world unit at distance 1
  uniform float uSize;  // dot diameter in world units
  uniform float uMorph; // 0 = flat world map, 1 = globe
  attribute vec3 aFlat; // where this dot sits on the flat map
  varying float vFacing;
  varying float vHide;
  void main() {
    // Antarctica would be a long dotted stripe along the bottom of the flat map, so it only shows on the globe
    vHide = step(aFlat.y, -1.08) * (1.0 - uMorph);
    vec3 local = mix(aFlat, position, uMorph);
    vec4 world = modelMatrix * vec4(local, 1.0);
    // the surface normal: straight out of a flat map, outward from the centre on the globe
    vec3 normalLocal = normalize(mix(vec3(0.0, 0.0, 1.0), position, uMorph));
    vec3 normalWorld = normalize(mat3(modelMatrix) * normalLocal);
    vFacing = dot(normalWorld, normalize(cameraPosition - world.xyz));
    vec4 view = viewMatrix * world;
    gl_PointSize = max(1.5, uSize * uScale / -view.z);
    gl_Position = projectionMatrix * view;
  }
`;

const DOT_FRAGMENT = /* glsl */ `
  uniform vec3 uColor;
  varying float vFacing;
  varying float vHide;
  void main() {
    float d = length(gl_PointCoord - 0.5);
    if (d > 0.5) discard;
    float edge = smoothstep(0.5, 0.3, d);
    // dots face-on are strongest, dots near the limb recede
    float alpha = edge * (0.45 + 0.55 * clamp(vFacing * 1.5, 0.0, 1.0)) * (1.0 - vHide);
    gl_FragColor = vec4(uColor, alpha);
  }
`;

const ATMOSPHERE_VERTEX = /* glsl */ `
  varying vec3 vNormal;
  varying vec3 vView;
  void main() {
    vNormal = normalize(normalMatrix * normal);
    vView = normalize(-(modelViewMatrix * vec4(position, 1.0)).xyz);
    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
  }
`;

const ATMOSPHERE_FRAGMENT = /* glsl */ `
  varying vec3 vNormal;
  varying vec3 vView;
  void main() {
    float rim = pow(clamp(1.0 - abs(dot(vNormal, vView)), 0.0, 1.0), 2.6);
    gl_FragColor = vec4(vec3(0.78, 0.84, 1.0), rim * 0.4);
  }
`;

export function Globe() {
  const tilt = useRef<THREE.Group>(null);
  const spin = useRef<THREE.Group>(null);
  const dots = useRef<THREE.ShaderMaterial>(null);
  const body = useRef<THREE.Mesh>(null);
  const atmosphere = useRef<THREE.Mesh>(null);

  const positions = useMemo(() => buildLandPoints(CANDIDATES), []);
  // The same dots laid out as an equirectangular map (longitude across, latitude up), so the globe can unroll to it.
  const flat = useMemo(() => {
    const out = new Float32Array(positions.length);
    for (let i = 0; i < positions.length; i += 3) {
      const x = positions[i];
      const y = positions[i + 1];
      const z = positions[i + 2];
      out[i] = Math.atan2(x, z);
      out[i + 1] = Math.asin(y);
      out[i + 2] = 0;
    }
    return out;
  }, [positions]);
  const dotUniforms = useMemo(
    () => ({
      uMorph: { value: 1 },
      uScale: { value: 600 },
      uSize: { value: 0.017 },
      uColor: { value: new THREE.Color("#ffffff") },
    }),
    []
  );

  useFrame((state) => {
    const m = heroState.morph;
    if (tilt.current) {
      // the map faces the camera square-on; the globe takes its tilt as it forms
      tilt.current.rotation.x = 0.38 * m;
      tilt.current.rotation.z = 0.1 * m;
    }
    if (spin.current) {
      // slow constant rotation, plus extra spin as the page scrolls
      spin.current.rotation.y = (0.55 + state.clock.elapsedTime * 0.07 + heroState.progress * 1.1) * m;
    }
    // the dark body and the atmosphere grow with the globe, so a flat map has no far side showing through
    body.current?.scale.setScalar(Math.max(0.001, m));
    if (atmosphere.current) {
      atmosphere.current.scale.setScalar(Math.max(0.001, m));
      atmosphere.current.visible = m > 0.05;
    }
    if (dots.current) {
      dots.current.uniforms.uMorph.value = m;
      const camera = state.camera as THREE.PerspectiveCamera;
      const pixelHeight = state.size.height * state.gl.getPixelRatio();
      dots.current.uniforms.uScale.value = pixelHeight / (2 * Math.tan(THREE.MathUtils.degToRad(camera.fov) / 2));
    }
  });

  return (
    <group ref={tilt}>
      <group ref={spin}>
        {/* solid body: hides the far side so only the near continents show */}
        <mesh ref={body}>
          <sphereGeometry args={[GLOBE_RADIUS * 0.985, 64, 48]} />
          <meshBasicMaterial color="#070f2b" />
        </mesh>
        <points>
          <bufferGeometry>
            <bufferAttribute attach="attributes-position" args={[positions, 3]} />
            <bufferAttribute attach="attributes-aFlat" args={[flat, 3]} />
          </bufferGeometry>
          <shaderMaterial
            ref={dots}
            uniforms={dotUniforms}
            vertexShader={DOT_VERTEX}
            fragmentShader={DOT_FRAGMENT}
            transparent
            depthWrite={false}
          />
        </points>
      </group>
      <mesh ref={atmosphere}>
        <sphereGeometry args={[GLOBE_RADIUS * 1.045, 64, 48]} />
        <shaderMaterial
          vertexShader={ATMOSPHERE_VERTEX}
          fragmentShader={ATMOSPHERE_FRAGMENT}
          transparent
          blending={THREE.AdditiveBlending}
          side={THREE.BackSide}
          depthWrite={false}
        />
      </mesh>
    </group>
  );
}
