import bpy, pathlib
blend = pathlib.Path(__file__).parent / "sanjeevni_full.blend"
bpy.ops.wm.open_mainfile(filepath=str(blend))
scene = bpy.context.scene
# Ensure OptiX GPU
try:
    prefs = bpy.context.preferences.addons['cycles'].preferences
    prefs.compute_device_type='OPTIX'
    prefs.get_devices()
    for d in prefs.devices: d.use = (d.type=='OPTIX')
    scene.cycles.device='GPU'
except: pass

outdir = pathlib.Path(__file__).parent.parent / "out"
outdir.mkdir(parents=True, exist_ok=True)

# Preview settings already 960x540 32 samples, keep
scene.cycles.samples = 64  # a bit higher for stills
scene.cycles.adaptive_threshold = 0.03
scene.render.resolution_percentage = 100 if "--final" in __import__("sys").argv else 100  # we want 1080p for stills
scene.render.resolution_x=1920
scene.render.resolution_y=1080
scene.render.resolution_percentage=60  # 1152x648 fast but still HD-ish, toggle 100 for final

for frame, name in [(1,"intact_1080p.png"), (90,"rubble_core_1080p.png")]:
    scene.frame_set(frame)
    scene.render.filepath = str(outdir / name)
    scene.render.image_settings.file_format='PNG'
    scene.render.image_settings.color_mode='RGB'
    scene.render.image_settings.color_depth='16'
    scene.render.image_settings.compression=15
    print(f"RENDER {name} frame {frame} res {scene.render.resolution_x*scene.render.resolution_percentage//100}x{scene.render.resolution_y*scene.render.resolution_percentage//100} samples {scene.cycles.samples}")
    bpy.ops.render.render(write_still=True)
    print(f"DONE {name}")

print("Stills done")
