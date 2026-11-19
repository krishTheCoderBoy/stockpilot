# Landing page assets

The vehicles and containers are photographs cut into layers; everything else is drawn in code (SVG, CSS, shaders).

| What | Where | Notes |
| --- | --- | --- |
| Reach stacker, side | `reach-body`, `reach-cylinder`, `reach-boom`, `reach-spreader` `.webp` | Four 1400 x 880 layers cut from one photo; the rig swings the boom, re-aims the cylinder and moves the spreader. Scene 2. |
| Reach stacker, front | `front-body`, `front-spreader` `.webp` | The beam and boom head are a separate layer so they can rise; a strip of the body is stretched to make the mast reach them. Scenes 2 and 3. |
| Containers | `container-red/teal/orange/green/grey.webp` | One straight-on photo, recoloured. |
| Trucks | `truck-flatbed.webp` (side), `truck-topdown.webp` (above) | Scenes 3 and 4. |
| Cargo plane | `plane-cargo-top.webp` | Green screen keyed out, nose to the right. Scene 6. |
| Measurements | `src/pages/landing/scenes/art/dims.ts` | Pivot, pins, deck height and scales measured on the layers; the rigs are in `scenes/warehouse/warehouseRig.ts` and `scenes/truck/truckRig.ts`. |
| Ship and its wake | `ship-topdown.svg`, `ship-wake.svg` | Flat vector. Scene 5. |
| Hero globe stand-in | `hero-globe-fallback.svg` | Mobile and reduced motion. |
| Water | `scenes/ocean/OceanCanvas.tsx` (shader) and `--lp-sea` in `landing.css` | Procedural. A looping WebM can replace it: see `scenes/ocean/oceanSlot.ts`. |
| Clouds | `cloud-1.webp` to `cloud-4.webp` | Procedural placeholders; swap in cloud cut-outs if you like. |
