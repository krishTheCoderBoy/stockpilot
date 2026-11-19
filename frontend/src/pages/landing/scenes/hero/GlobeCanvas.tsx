import { Canvas, useFrame } from "@react-three/fiber";
import { useEffect, useRef } from "react";
import * as THREE from "three";
import { Globe } from "./Globe";
import { LightStreaks } from "./LightStreaks";
import { NeonRing } from "./NeonRing";
import { clamp01, easeInOutCubic, heroState } from "./heroState";

// Camera starts back so the whole globe is framed, and dollies in until it fills the screen.
const CAMERA_START_Z = 5.6;
const CAMERA_END_Z = 2.3;

// The intro: a flat map of the world, then it curls up into the globe.
const MORPH_DELAY = 0.7; // seconds the flat map is shown on its own
const MORPH_TIME = 2.8;

function World() {
  const world = useRef<THREE.Group>(null);

  // every time the canvas mounts, play the intro from the flat map
  useEffect(() => {
    heroState.morph = 0;
    return () => {
      heroState.morph = 1;
    };
  }, []);

  useFrame((state) => {
    heroState.morph = easeInOutCubic(clamp01((state.clock.elapsedTime - MORPH_DELAY) / MORPH_TIME));
    const eased = easeInOutCubic(clamp01(heroState.progress));
    const aspect = state.size.width / state.size.height;
    // Offset right of centre to leave room for the headline; settle to centre as it closes in.
    const restX = aspect > 1.5 ? 1.4 : aspect > 1.1 ? 0.9 : 0;
    state.camera.position.z = THREE.MathUtils.lerp(CAMERA_START_Z, CAMERA_END_Z, eased);
    if (world.current) {
      // centred while it is a flat map, then it slides right to make room for the headline
      world.current.position.x = THREE.MathUtils.lerp(restX, 0, eased) * heroState.morph;
      world.current.position.y = THREE.MathUtils.lerp(0.1, 0, eased);
    }
  });

  return (
    <group ref={world}>
      <Globe />
      <NeonRing />
    </group>
  );
}

interface GlobeCanvasProps {
  /** Rendering pauses while the hero is off screen. */
  active: boolean;
  onReady?: () => void;
}

// Default export so Scene1Hero can load this (and three.js) lazily.
export default function GlobeCanvas({ active, onReady }: GlobeCanvasProps) {
  return (
    <Canvas
      dpr={[1, 1.75]}
      camera={{ position: [0, 0, CAMERA_START_Z], fov: 38, near: 0.1, far: 60 }}
      gl={{ antialias: true, alpha: true, powerPreference: "high-performance" }}
      frameloop={active ? "always" : "never"}
      style={{ position: "absolute", inset: 0 }}
      onCreated={({ gl }) => {
        gl.setClearColor(0x000000, 0);
        onReady?.();
      }}
    >
      <World />
      <LightStreaks />
    </Canvas>
  );
}
