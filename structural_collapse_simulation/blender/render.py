# Render from the baked sanjeevni_final.blend. Usage:
#   blender -b <blend> -P render.py -- <out_dir> <pct> <samples> <f1,f2,...>      (specific frames)
#   blender -b <blend> -P render.py -- <out_dir> <pct> <samples> <start>-<end>    (range; skips frames already on disk = resumable)
import bpy, sys, time, pathlib
out, pct, spp, fr = sys.argv[sys.argv.index('--') + 1:][:4]
sc = bpy.context.scene
sc.render.resolution_percentage, sc.cycles.samples = int(pct), int(spp)
p = bpy.context.preferences.addons['cycles'].preferences
p.compute_device_type = 'OPTIX'; p.get_devices()
for d in p.devices:
    d.use = d.type == 'OPTIX'
sc.cycles.device = 'GPU'
frames = range(int(fr.split('-')[0]), int(fr.split('-')[1]) + 1) if '-' in fr else [int(x) for x in fr.split(',')]
pathlib.Path(out).mkdir(parents=True, exist_ok=True)
for f in frames:
    fp = pathlib.Path(out) / f'f_{f:04d}.png'
    if fp.exists():
        continue
    sc.frame_set(f); sc.render.filepath = str(fp)
    t = time.time(); bpy.ops.render.render(write_still=True)
    print(f'FRAME {f} {time.time() - t:.1f}s', flush=True)
