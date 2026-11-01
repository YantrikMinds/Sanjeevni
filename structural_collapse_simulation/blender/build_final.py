# Sanjeevni - full headless build: blender -b --factory-startup -P build_final.py   ->  sanjeevni_final.blend (stages 1-6, baked)
import bpy, pathlib, time
P = pathlib.Path(__file__).parent
t0 = time.time()

def run(name, g=None):
    exec(compile((P / name).read_text(encoding='utf-8'), name, 'exec'), g if g is not None else {'__name__': '__main__'})

run('stage1_scene.py')
for n in ('Cube', 'Light', 'Camera'):
    if n in bpy.data.objects:
        bpy.data.objects.remove(bpy.data.objects[n])
run('add_town.py', {'__name__': '__main__', '__file__': str(P / 'add_town.py'), 'SAVE': False})   # 4 more hero buildings; stage 2 rigs all of them
run('stage2_rig.py', {'__name__': '__main__', 'CHUNK': 1.6, 'N_DEBRIS': 200})   # 5 buildings: coarser chunks + less gravel keep the bake to minutes
g3 = {'__name__': '__main__'}
run('stage3_quake.py', g3)
sc = bpy.context.scene
sc.frame_set(1)
bpy.ops.ptcache.bake_all(bake=True)
print('baked', sc.rigidbody_world.point_cache.is_baked, round(time.time() - t0), 's')
run('stage4_5_finish.py', {'__name__': '__main__', 'env': g3['env'], 'mk': g3['mk']})
bpy.ops.wm.save_as_mainfile(filepath=str(P.parent / 'sanjeevni_final.blend'))
run('add_rover.py', {'__name__': '__main__', '__file__': str(P / 'add_rover.py')})   # RIIS rover on the keyframed path; saves sanjeevni.blend
print('SAVED', round(time.time() - t0), 's')
