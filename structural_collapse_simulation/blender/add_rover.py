# Swap the box Rover for the RIIS rover GLB (rides the existing keyframed 'Rover'). Usage: blender -b sanjeevni_final.blend -P add_rover.py
# The GLB is Z-up but Blender's importer treats it as Y-up, so the model is rotated -90 deg about X to stand upright.
import bpy, math, pathlib
GLB = str(pathlib.Path(__file__).resolve().parent.parent / 'assets' / 'riis_rover_full_build.glb')
OUT = pathlib.Path(bpy.data.filepath).parent / 'sanjeevni_town.blend'
S = 0.3   # model is 2.0 x 1.2 x 1.5 m at S=1: 0.3 -> 0.6 x 0.36 x 0.45 m, small enough for the gaps between slabs
rover = bpy.data.objects['Rover']
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=GLB)
new = [o for o in bpy.data.objects if o not in before]
drop = [o for o in new if o.name.startswith('COLLISION_')]
new = [o for o in new if o not in drop]
for o in drop:
    bpy.data.objects.remove(o)
holder = bpy.data.objects.new('RoverModel', None)
rover.users_collection[0].objects.link(holder)
holder.parent = rover
holder.rotation_euler = (-math.pi / 2, 0, 0)
holder.scale = (S, S, S)
for o in new:
    if o.parent is None:
        o.parent = holder
rover.data = bpy.data.meshes.new('RoverEmpty')
bpy.data.objects['RoverHead'].location = (1.25 * S, 0, 0.4 * S)   # front LED housing
bpy.ops.wm.save_as_mainfile(filepath=str(OUT))
print('SAVED', OUT, len(new), 'objects')
