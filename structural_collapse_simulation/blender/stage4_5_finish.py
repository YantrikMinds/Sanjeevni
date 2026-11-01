# Sanjeevni - Stages 4-6: rover (rides the BAKED rubble), dust/haze volume, camera, rescue lights, Cycles settings.
# Run AFTER stage 3 + rigid body bake. Needs env, mk from stage3_quake.py.
import bpy, bmesh, math
from mathutils import Vector as V, Matrix

sc = bpy.context.scene
END = sc.frame_end
bpy.context.preferences.edit.keyframe_new_interpolation_type = 'LINEAR'
col = sc.collection

def ss(a, b, x):
    t = min(1.0, max(0.0, (x - a) / (b - a)))
    return t * t * (3 - 2 * t)

def lerp(a, b, t):
    return a + (b - a) * t

def pbr(name, c, rough, metal=0.0, emit=0.0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    t = m.node_tree; t.nodes.clear()
    o, b = t.nodes.new('ShaderNodeOutputMaterial'), t.nodes.new('ShaderNodeBsdfPrincipled')
    b.inputs['Base Color'].default_value = (*c, 1); b.inputs['Roughness'].default_value = rough; b.inputs['Metallic'].default_value = metal
    if emit:
        b.inputs['Emission Color'].default_value = (*c, 1); b.inputs['Emission Strength'].default_value = emit
    t.links.new(b.outputs[0], o.inputs[0])
    return m

# ---------------------------------------------------------------- rover: height from the settled rubble at frame 200
sc.frame_set(200)
dg = bpy.context.evaluated_depsgraph_get()
def surf(x, y):
    hit, loc, *_ = sc.ray_cast(dg, V((x, y, 40)), V((0, 0, -1)))
    return loc.z if hit else 0.0

WP = [(-9, 0.5), (-5.5, -5.5), (-2.2, -9.6), (0.4, -11.8)]
pts, step = [], 0.1
for (ax, ay), (bx, by) in zip(WP, WP[1:]):
    n = max(1, int(math.hypot(bx - ax, by - ay) / step))
    pts += [(lerp(ax, bx, i / n), lerp(ay, by, i / n)) for i in range(n)]
pts.append(WP[-1])
def at(d):
    return pts[min(len(pts) - 1, max(0, int(d / step)))]
L = (len(pts) - 1) * step

bm = bmesh.new()
def box(c, s, mi):
    r = bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.Translation(c) @ Matrix.Diagonal((*s, 1)))
    for f in {f for v in r['verts'] for f in v.link_faces}:
        f.material_index = mi
box((0, 0, 0.30), (1.1, 0.62, 0.22), 0); box((-0.1, 0, 0.5), (0.6, 0.45, 0.14), 0); box((0.58, 0, 0.36), (0.1, 0.3, 0.1), 2)
for sx in (-0.38, 0.38):
    for sy in (-0.36, 0.36):
        r = bmesh.ops.create_cone(bm, cap_ends=True, segments=16, radius1=0.17, radius2=0.17, depth=0.14, matrix=Matrix.Translation((sx, sy, 0.17)) @ Matrix.Rotation(math.pi / 2, 4, 'X'))
        for f in {f for v in r['verts'] for f in v.link_faces}:
            f.material_index = 1
me = bpy.data.meshes.new('Rover'); bm.to_mesh(me); bm.free()
for m in (pbr('M_RoverBody', (0.9, 0.32, 0.02), 0.4), pbr('M_RoverWheel', (0.02, 0.02, 0.02), 0.9), pbr('M_RoverLens', (1, 0.9, 0.7), 0.2, 40)):
    me.materials.append(m)
rover = bpy.data.objects.new('Rover', me); col.objects.link(rover)
hl = bpy.data.lights.new('RoverHead', 'SPOT')
hl.energy, hl.spot_size, hl.spot_blend, hl.color, hl.shadow_soft_size = 800, math.radians(40), 0.4, (1, 0.95, 0.8), 0.05
ho = bpy.data.objects.new('RoverHead', hl); col.objects.link(ho)
ho.parent = rover; ho.location = (0.6, 0, 0.36); ho.rotation_euler = (0, -(math.pi / 2 - 0.15), 0)
R0, R1 = 150, END - 8
WB = 0.2   # half wheelbase of the 0.6 m scout rover (add_rover.py S=0.3)
pose, hd = [], 0.0
for f in list(range(1, R1 + 1, 3)) + [R1]:
    d = L * ss(R0, R1, f)
    (x, y), (x2, y2) = at(d), at(d + 0.8)
    hd = math.atan2(y2 - y, x2 - x) if d < L - 0.01 else hd
    pose.append([f, x, y, surf(x + WB * math.cos(hd), y + WB * math.sin(hd)), surf(x - WB * math.cos(hd), y - WB * math.sin(hd)), hd])
for k in (3, 4):   # moving average: gravel tops and chunk edges make the raw height jitter
    sm = [[sum(p[k] for p in pose[max(0, i - 3):i + 4]) / len(pose[max(0, i - 3):i + 4]) for i in range(len(pose))]]
    for p, z in zip(pose, sm[0]):
        p[k] = z
for f, x, y, zf, zr, hd in pose:
    rover.location = (x, y, (zf + zr) / 2)
    rover.rotation_euler = (0, -math.atan2(zf - zr, 2 * WB), hd)
    rover.keyframe_insert('location', frame=f); rover.keyframe_insert('rotation_euler', frame=f)
sc.frame_set(1)

# ---------------------------------------------------------------- dust + light haze: ONE procedural volume (no grids, ~no VRAM)
m = bpy.data.materials.new('M_Dust'); t = m.node_tree; t.nodes.clear()
N = lambda ty, **k: (lambda n: [setattr(n, a, b) for a, b in k.items()] and n or n)(t.nodes.new(ty))
out, pv = N('ShaderNodeOutputMaterial'), N('ShaderNodeVolumePrincipled')
tc, nz4 = N('ShaderNodeTexCoord'), N('ShaderNodeTexNoise', noise_dimensions='4D')
nz4.inputs['Scale'].default_value, nz4.inputs['Detail'].default_value, nz4.inputs['Roughness'].default_value = 0.35, 6, 0.6
nz4.inputs['W'].driver_add('default_value').driver.expression = 'frame / 24 * 0.8'
rm = N('ShaderNodeMapRange'); rm.inputs[1].default_value, rm.inputs[2].default_value = 0.35, 0.75
vsub = N('ShaderNodeVectorMath', operation='SUBTRACT'); vsub.inputs[1].default_value = (0, -3, -10)   # plume centre in cube-local metres (hero centre, ~2 m up)
sep, cmb = N('ShaderNodeSeparateXYZ'), N('ShaderNodeCombineXYZ')
zs = N('ShaderNodeMath', operation='MULTIPLY'); zs.inputs[1].default_value = 1.6    # squash plume vertically
ln = N('ShaderNodeVectorMath', operation='LENGTH')
rad = N('ShaderNodeValue'); rad.label = 'Radius'
dv = N('ShaderNodeMath', operation='DIVIDE')
inv = N('ShaderNodeMath', operation='SUBTRACT', use_clamp=True); inv.inputs[0].default_value = 1.0
sq = N('ShaderNodeMath', operation='MULTIPLY')
amt = N('ShaderNodeValue'); amt.label = 'Dust'
m1, m2 = N('ShaderNodeMath', operation='MULTIPLY'), N('ShaderNodeMath', operation='MULTIPLY')
fin = N('ShaderNodeMath', operation='ADD'); fin.inputs[1].default_value = 0.004   # background haze (1/m)
lk = t.links.new
lk(tc.outputs['Object'], vsub.inputs[0]); lk(tc.outputs['Object'], nz4.inputs['Vector']); lk(nz4.outputs['Fac'], rm.inputs[0])
lk(vsub.outputs[0], sep.inputs[0]); lk(sep.outputs[0], cmb.inputs[0]); lk(sep.outputs[1], cmb.inputs[1]); lk(sep.outputs[2], zs.inputs[0]); lk(zs.outputs[0], cmb.inputs[2])
lk(cmb.outputs[0], ln.inputs[0]); lk(ln.outputs['Value'], dv.inputs[0]); lk(rad.outputs[0], dv.inputs[1]); lk(dv.outputs[0], inv.inputs[1])
lk(inv.outputs[0], sq.inputs[0]); lk(inv.outputs[0], sq.inputs[1]); lk(sq.outputs[0], m1.inputs[0]); lk(rm.outputs[0], m1.inputs[1])
lk(m1.outputs[0], m2.inputs[0]); lk(amt.outputs[0], m2.inputs[1]); lk(m2.outputs[0], fin.inputs[0]); lk(fin.outputs[0], pv.inputs['Density'])
pv.inputs['Color'].default_value, pv.inputs['Anisotropy'].default_value = (0.55, 0.50, 0.45, 1), 0.35
lk(pv.outputs[0], out.inputs['Volume'])
for f, a, r in [(1, 0, 4), (36, 0, 4), (70, 0.55, 10), (110, 0.55, 18), (160, 0.30, 26), (230, 0.12, 32), (END, 0.05, 36)]:
    amt.outputs[0].default_value, rad.outputs[0].default_value = a, r
    amt.outputs[0].keyframe_insert('default_value', frame=f); rad.outputs[0].keyframe_insert('default_value', frame=f)
bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.Diagonal((80, 64, 26, 1)))
dme = bpy.data.meshes.new('DustVolume'); bm.to_mesh(dme); bm.free(); dme.materials.append(m)
dust = bpy.data.objects.new('DustVolume', dme); col.objects.link(dust); dust.location = (0, -12, 13)
dust.visible_shadow = False   # volume must not shadow the surfaces inside it
dust.display_type = 'WIRE'    # the 80x64x26 m domain cube would draw as a solid block through the street in the viewport
for x in (-51, -27, 27, 51):   # same plume over each town copy (linked mesh + material, centred in object space)
    dc = dust.copy(); dc.location.x = x; col.objects.link(dc)

# ---------------------------------------------------------------- camera: one continuous move (push-in -> low angle -> rising orbit), handheld + quake shake
cd = bpy.data.cameras.new('Cam_Main'); cd.sensor_width = 36; cd.dof.use_dof = True
cam = bpy.data.objects.new('Cam_Main', cd); col.objects.link(cam); sc.camera = cam
tgt = bpy.data.objects.new('Cam_Target', None); col.objects.link(tgt)
c = cam.constraints.new('TRACK_TO'); c.target, c.track_axis, c.up_axis = tgt, 'TRACK_NEGATIVE_Z', 'UP_Y'
hp, hq = [mk(s, (0.6, 1.1, 1.9, 3.1)) for s in (11, 12, 13)], [mk(s, (2.4, 3.7, 5.3, 6.1)) for s in (21, 22, 23)]
ha, qa = [mk(s, (0.5, 0.9, 1.7, 2.6)) for s in (31, 32, 33)], [mk(s, (2.1, 3.3, 4.9, 5.7)) for s in (41, 42, 43)]
A0, A1 = math.radians(60.5), math.radians(170)
for f in range(1, END + 1):
    e = env(f)
    t1, t2 = ss(1, 130, f), ss(130, END, f)
    if f <= 130:
        p = V((lerp(16, 8.5, t1), lerp(5, 0, t1), lerp(1.7, 0.9, t1)))
        aim = V((0, -15, lerp(5.5, 2.5, ss(30, 130, f))))
    else:
        a, r = lerp(A0, A1, t2), lerp(17.2, 27, t2)
        p = V((r * math.cos(a), -15 + r * math.sin(a), lerp(0.9, 21, t2 ** 1.4)))
        aim = V((0, -15, lerp(2.5, 2.0, t2)))
    dist = (p - aim).length
    ps = V([hp[i](f) * 0.02 + hq[i](f) * 0.12 * e for i in range(3)])
    aj = V([ha[i](f) * 0.05 + qa[i](f) * 0.55 * e for i in range(3)])
    cam.location, tgt.location = p + ps, aim + aj
    cam.keyframe_insert('location', frame=f); tgt.keyframe_insert('location', frame=f)
    cd.lens, cd.dof.aperture_fstop, cd.dof.focus_distance = lerp(24, 42, ss(125, 200, f)), lerp(8, 2.0, ss(120, 190, f)), dist
    for k in ('lens', 'dof.aperture_fstop', 'dof.focus_distance'):
        cd.keyframe_insert(k, frame=f)
sc.frame_set(1)

# ---------------------------------------------------------------- rescue floodlights + red/blue strobes (from frame 140/150)
ft = bpy.data.objects.new('Flood_Target', None); col.objects.link(ft); ft.location = (0, -14, 2)
for i, pos in enumerate(((-13, -2, 7), (13, -2, 7), (0, -1, 9))):
    d = bpy.data.lights.new(f'Flood_{i}', 'SPOT'); d.spot_size, d.spot_blend, d.color, d.shadow_soft_size = math.radians(38), 0.5, (1, 0.95, 0.85), 0.4
    o = bpy.data.objects.new(f'Flood_{i}', d); col.objects.link(o); o.location = pos
    k = o.constraints.new('TRACK_TO'); k.target, k.track_axis, k.up_axis = ft, 'TRACK_NEGATIVE_Z', 'UP_Y'
    for f, w in ((1, 0), (140, 0), (160, 7000)):
        d.energy = w; d.keyframe_insert('energy', frame=f)
bpy.context.preferences.edit.keyframe_new_interpolation_type = 'CONSTANT'
for nm, colr, pos, ph in (('Strobe_Red', (1, 0.04, 0.03), (-10, -3, 2.5), 0), ('Strobe_Blue', (0.05, 0.15, 1), (10, -3, 2.5), 1)):
    d = bpy.data.lights.new(nm, 'POINT'); d.color, d.shadow_soft_size = colr, 0.2
    o = bpy.data.objects.new(nm, d); col.objects.link(o); o.location = pos
    d.energy = 0; d.keyframe_insert('energy', frame=1)
    for f in range(150, END + 1, 4):
        d.energy = 2500 if ((f - 150) // 4) % 2 == ph else 0
        d.keyframe_insert('energy', frame=f)
bpy.context.preferences.edit.keyframe_new_interpolation_type = 'BEZIER'

# ---------------------------------------------------------------- Cycles (RTX 4060 8 GB): OptiX, adaptive, volumes capped
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage, sc.render.fps = 1920, 1080, 100, 24
cy = sc.cycles
cy.device, cy.samples, cy.use_adaptive_sampling, cy.adaptive_threshold, cy.adaptive_min_samples = 'GPU', 128, True, 0.02, 16
cy.use_denoising, cy.denoiser = True, 'OPTIX'
cy.max_bounces, cy.diffuse_bounces, cy.glossy_bounces, cy.transmission_bounces, cy.transparent_max_bounces, cy.volume_bounces = 8, 3, 4, 4, 8, 2
cy.sample_clamp_indirect = 10   # kills fireflies from the emissive windows / strobes
for k, v in (('volume_step_rate', 1.0), ('volume_max_steps', 512)):
    try:
        setattr(cy, k, v)
    except Exception as ex:
        print('skip', k, ex)
sc.render.use_motion_blur, sc.render.motion_blur_shutter = True, 0.5
sc.render.image_settings.file_format, sc.render.image_settings.color_mode = 'PNG', 'RGB'
print('Stage 4-6 done')
