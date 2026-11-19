import { isLand } from "./landMask";

/**
 * Evenly spaced points on a unit sphere (Fibonacci spiral), keeping only those over land.
 * Longitude 0 faces +Z (toward the camera), latitude 90 is +Y.
 */
export function buildLandPoints(candidates: number): Float32Array {
  const positions: number[] = [];
  const golden = Math.PI * (3 - Math.sqrt(5));
  for (let i = 0; i < candidates; i++) {
    const y = 1 - (i / (candidates - 1)) * 2;
    const ring = Math.sqrt(1 - y * y);
    const theta = golden * i;
    const x = Math.cos(theta) * ring;
    const z = Math.sin(theta) * ring;
    const lat = (Math.asin(y) * 180) / Math.PI;
    const lon = (Math.atan2(x, z) * 180) / Math.PI;
    if (isLand(lon, lat)) positions.push(x, y, z);
  }
  return new Float32Array(positions);
}
