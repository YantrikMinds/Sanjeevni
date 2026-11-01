# Add 4 intact copies of the hero building (windows, balconies, AC, stair core) along the south side of the street.
# Usage: blender -b sanjeevni_rover.blend -P add_town.py   ->  sanjeevni.blend (source file untouched). Also run by build_final.py before stage 2.
import bpy, pathlib, random
P = pathlib.Path(__file__).parent
OUT = P.parent / 'sanjeevni.blend'
XS = (-51, -27, 27, 51)   # hero is x -9..9; the old Town_6/Town_7 boxes sit on these spots and are removed

src = (P / 'stage1_scene.py').read_text(encoding='utf-8').split("if RUN['scene']")[0]   # definitions only, don't rebuild the scene
ns = {'__name__': '__main__'}
exec(compile(src, 'stage1_scene.py', 'exec'), ns)

# stage 2 rewrote Hero_Concrete for the fracture rig: give copies a fresh one, reuse the other existing materials
orig_conc = ns['m_concrete']
ns['m_concrete'] = lambda name, *a, **k: orig_conc('Town_Hero_Concrete', *a, **k) if name == 'Hero_Concrete' else bpy.data.materials[name]
ns['m_simple'] = lambda name, *a, **k: bpy.data.materials[name]
ns['m_glass'] = lambda: bpy.data.materials['Hero_Glass']
ns['m_interior'] = lambda: bpy.data.materials['Hero_Interior']

for n in ('Town_6_Body', 'Town_6_Windows', 'Town_7_Body', 'Town_7_Windows'):
    if n in bpy.data.objects:
        bpy.data.objects.remove(bpy.data.objects[n])
for k, x in enumerate(XS):
    ns['HERO_C'] = ns['V']((x, -15, 0))
    ns['rng'] = random.Random(500 + k)   # different lit-window pattern per copy
    ns['hero'](ns['coll'](f'Town_Hero_{k}'))
if globals().get('SAVE', True):   # build_final.py passes SAVE=False and rigs the copies in stage 2 first
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT))
print('Town copies', {c.name: len(c.objects) for c in bpy.data.collections if c.name.startswith('Town_Hero')})
