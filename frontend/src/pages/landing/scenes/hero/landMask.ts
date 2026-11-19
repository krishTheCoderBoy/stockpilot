import { LAND_POLYGONS, WATER_POLYGONS, type Polygon } from "./landPolygons";

// Equirectangular land mask, 1 degree per cell, built once from the outlines in
// landPolygons.ts. Row 0 is latitude +90, column 0 is longitude -180.
export const MASK_WIDTH = 360;
export const MASK_HEIGHT = 180;

interface Prepared {
  polygon: Polygon;
  minLon: number;
  maxLon: number;
  minLat: number;
  maxLat: number;
}

function prepare(polygons: ReadonlyArray<Polygon>): Prepared[] {
  return polygons.map((polygon) => {
    const lons = polygon.map(([lon]) => lon);
    const lats = polygon.map(([, lat]) => lat);
    return {
      polygon,
      minLon: Math.min(...lons),
      maxLon: Math.max(...lons),
      minLat: Math.min(...lats),
      maxLat: Math.max(...lats),
    };
  });
}

// Standard ray casting; the outlines never cross the antimeridian.
function contains({ polygon, minLon, maxLon, minLat, maxLat }: Prepared, lon: number, lat: number): boolean {
  if (lon < minLon || lon > maxLon || lat < minLat || lat > maxLat) return false;
  let inside = false;
  for (let i = 0, j = polygon.length - 1; i < polygon.length; j = i++) {
    const [xi, yi] = polygon[i];
    const [xj, yj] = polygon[j];
    if (yi > lat !== yj > lat && lon < ((xj - xi) * (lat - yi)) / (yj - yi) + xi) inside = !inside;
  }
  return inside;
}

let mask: Uint8Array | null = null;

export function getLandMask(): Uint8Array {
  if (mask) return mask;
  const land = prepare(LAND_POLYGONS);
  const water = prepare(WATER_POLYGONS);
  const built = new Uint8Array(MASK_WIDTH * MASK_HEIGHT);
  for (let row = 0; row < MASK_HEIGHT; row++) {
    const lat = 90 - ((row + 0.5) * 180) / MASK_HEIGHT;
    for (let col = 0; col < MASK_WIDTH; col++) {
      const lon = -180 + ((col + 0.5) * 360) / MASK_WIDTH;
      if (water.some((w) => contains(w, lon, lat))) continue;
      if (land.some((l) => contains(l, lon, lat))) built[row * MASK_WIDTH + col] = 1;
    }
  }
  mask = built;
  return built;
}

export function isLand(lonDeg: number, latDeg: number): boolean {
  const m = getLandMask();
  const col = Math.min(MASK_WIDTH - 1, Math.max(0, Math.floor(((lonDeg + 180) / 360) * MASK_WIDTH)));
  const row = Math.min(MASK_HEIGHT - 1, Math.max(0, Math.floor(((90 - latDeg) / 180) * MASK_HEIGHT)));
  return m[row * MASK_WIDTH + col] === 1;
}
