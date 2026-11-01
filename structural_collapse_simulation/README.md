# Structural Collapse and Survival-Void Simulation

Blender 5.1 pipeline for the Sanjeevni demo shot: a 5-building street collapses floor by floor under an earthquake. A central stair core survives as the predicted survival void, and a 0.6 m scout rover (RIIS model) drives into the rubble. This is an illustrative simulation, not a structural-engineering prediction.

## Contents
| Path | Purpose |
|---|---|
| `sanjeevni.blend` | Final scene: 5 buildings, baked physics (frames 1-336), rover, dust, camera, lights |
| `blender/stage1_scene.py` | Night street, town, hero building with separate stair core (procedural PBR, no textures) |
| `blender/stage2_rig.py` | Voronoi fracture, rigid-body chunks, bottom-up breaking constraints, gravel |
| `blender/stage3_quake.py` | Quake envelope and camera shake |
| `blender/stage4_5_finish.py` | Dust volume, camera path, rover path, floodlights, red/blue strobes |
| `blender/add_town.py`, `add_rover.py` | Four extra hero-type buildings, RIIS rover import |
| `blender/build_final.py` | Headless full rebuild of everything |
| `blender/render.py` | Cycles/OptiX frame and still rendering |
| `assets/riis_rover_full_build.glb` | Rover model |

## Physics
- Blender Rigid Body World (Bullet), convex-hull chunks, concrete 2400 kg/m3, restitution 0, friction 0.85.
- Fixed constraints with per-floor breaking thresholds; failure timing is keyframed bottom-up (scheduled, not fully emergent).
- Ground does not shake in the physics (it broke the constraints); the quake is shown by camera shake and failure timing.

## Usage
```
blender -b --factory-startup -P blender/build_final.py
```
Open `sanjeevni.blend`, press Space on frame 1 in Solid or Material Preview. Re-bake via Physics > Rigid Body World > Bake if the cache is invalid. Full rebuild writes `sanjeevni_final.blend` and `sanjeevni.blend` into the parent folder; the 5-building bake takes roughly 20 minutes.

Known limits: glass panes in rubble render as bright squares; scripts assume Blender 5.1.
