# Sanjeevni - Stage 1: night street, background town, hero building. Blender 5.1.1, metric, 1 BU = 1 m.
# Street runs along X, hero building on the south side (y<0), camera side = street. Re-runnable: wipes its own collections.
# Toggle sections below. Hero is built per storey (Hero_S{i}_Concrete) so stage 2 can fracture/constrain per floor.
import bpy, bmesh, math, random
from mathutils import Vector, Matrix

SEED = 1337
RUN = dict(scene=True, street=True, town=True, hero=True)
HERO_C = Vector((0, -15, 0))
HERO_W, HERO_D = 18.0, 12.0          # footprint (x, y)
STOREYS, SH, WALL = 4, 3.0, 0.3
CORE_HX, CORE_HY = 2.0, 2.5          # stairwell core half extents (4 x 5 m)
FAC = [((0, -1, 0), (1, 0, 0)), ((0, 1, 0), (-1, 0, 0)), ((1, 0, 0), (0, 1, 0)), ((-1, 0, 0), (0, -1, 0))]  # (outward normal, along-dir); dir x Z == normal
rng = random.Random(SEED)
V = Vector

# ---------------------------------------------------------------- helpers
def coll(name):
    c = bpy.data.collections.get(name)
    if c:
        for o in list(c.objects):
            bpy.data.objects.remove(o)
    else:
        c = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(c)
    return c

def obj(name, data, c):
    o = bpy.data.objects.new(name, data)
    c.objects.link(o)
    return o

def mat(name):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.node_tree.nodes.clear()  # 5.x: materials always have a node tree
    return m, m.node_tree

def nd(t, kind, ins=None, **props):
    n = t.nodes.new(kind)
    for k, v in props.items():
        setattr(n, k, v)
    for k, v in (ins or {}).items():
        n.inputs[k].default_value = v
    return n

def lk(t, a, ao, b, bi):
    t.links.new(a.outputs[ao], b.inputs[bi])

def ramp(t, stops, src=None, so='Fac'):
    r = nd(t, 'ShaderNodeValToRGB')
    e = r.color_ramp.elements
    e[0].position, e[1].position = stops[0][0], stops[-1][0]
    for p, _ in stops[1:-1]:
        e.new(p)
    for el, (_, c) in zip(e, stops):
        el.color = c
    if src:
        lk(t, src, so, r, 'Fac')
    return r

def noise(t, P, scale, det=6, rough=0.55):
    n = nd(t, 'ShaderNodeTexNoise', ins={'Scale': scale, 'Detail': det, 'Roughness': rough})
    lk(t, P, 'Position', n, 'Vector')
    return n

def math_(t, op, a=None, b=None, c=None):
    n = nd(t, 'ShaderNodeMath', operation=op)
    for i, x in enumerate((a, b, c)):
        if x is None:
            continue
        if isinstance(x, (int, float)):
            n.inputs[i].default_value = x
        else:
            lk(t, x, 0 if x.bl_idname == 'ShaderNodeMath' else x.outputs[0].name, n, i)
    return n

def mix_mul(t, a, b, fac=1.0):  # RGBA multiply of two nodes' first outputs
    n = nd(t, 'ShaderNodeMix', data_type='RGBA', blend_type='MULTIPLY')
    n.inputs[0].default_value = fac
    t.links.new(a.outputs[0], n.inputs[6])
    t.links.new(b.outputs[0], n.inputs[7])
    return n

def principled(t, **ins):
    out = nd(t, 'ShaderNodeOutputMaterial')
    bs = nd(t, 'ShaderNodeBsdfPrincipled', ins=ins)
    lk(t, bs, 0, out, 'Surface')
    return bs, out

def bump(t, bs, height, strength, dist):
    b = nd(t, 'ShaderNodeBump', ins={'Strength': strength, 'Distance': dist})
    t.links.new(height.outputs[0], b.inputs['Height'])
    lk(t, b, 'Normal', bs, 'Normal')

# ---------------------------------------------------------------- materials
def m_asphalt():
    m, t = mat('Asphalt_Wet')
    P = nd(t, 'ShaderNodeNewGeometry'); bs, _ = principled(t)
    base = ramp(t, [(0.3, (0.02, 0.02, 0.022, 1)), (0.7, (0.075, 0.075, 0.08, 1))], noise(t, P, 1.3, 8))
    lk(t, base, 'Color', bs, 'Base Color')
    pud = ramp(t, [(0.52, (0, 0, 0, 1)), (0.62, (1, 1, 1, 1))], noise(t, P, 0.3, 2))   # puddle mask
    rmap = nd(t, 'ShaderNodeMapRange', ins={'To Min': 0.85, 'To Max': 0.25})
    lk(t, pud, 'Color', rmap, 'Value')
    sep = nd(t, 'ShaderNodeSeparateXYZ'); lk(t, P, 'Position', sep, 'Vector')
    y = math_(t, 'ABSOLUTE'); lk(t, sep, 'Y', y, 0)
    d1 = math_(t, 'ABSOLUTE', math_(t, 'SUBTRACT', y, 2.5))
    d2 = math_(t, 'ABSOLUTE', math_(t, 'SUBTRACT', d1, 0.8))            # tire tracks: |y| = 2.5 +- 0.8
    trk = ramp(t, [(0.0, (1, 1, 1, 1)), (0.4, (0, 0, 0, 1))], d2, 'Value')
    patch = ramp(t, [(0.35, (0, 0, 0, 1)), (0.6, (1, 1, 1, 1))], noise(t, P, 2.0, 4))
    trk_m = nd(t, 'ShaderNodeMath', operation='MULTIPLY')
    t.links.new(trk.outputs[0], trk_m.inputs[0]); t.links.new(patch.outputs[0], trk_m.inputs[1])
    rough = math_(t, 'MULTIPLY_ADD', trk_m, -0.12)
    t.links.new(rmap.outputs[0], rough.inputs[2])
    lk(t, rough, 'Value', bs, 'Roughness')
    vor = nd(t, 'ShaderNodeTexVoronoi', feature='DISTANCE_TO_EDGE', ins={'Scale': 0.7}); lk(t, P, 'Position', vor, 'Vector')
    crack = ramp(t, [(0.0, (1, 1, 1, 1)), (0.04, (0, 0, 0, 1))], vor, 'Distance')
    gate = ramp(t, [(0.45, (0, 0, 0, 1)), (0.6, (1, 1, 1, 1))], noise(t, P, 0.5, 2))  # cracks only in patches
    crack_m = nd(t, 'ShaderNodeMath', operation='MULTIPLY')
    t.links.new(crack.outputs[0], crack_m.inputs[0]); t.links.new(gate.outputs[0], crack_m.inputs[1])
    h = nd(t, 'ShaderNodeMath', operation='MULTIPLY_ADD'); h.inputs[1].default_value = -1.0
    t.links.new(crack_m.outputs[0], h.inputs[0]); t.links.new(noise(t, P, 90, 2).outputs['Fac'], h.inputs[2])
    bump(t, bs, h, 0.35, 0.03)
    return m

def m_concrete(name, grey=0.35, streaks=True):
    m, t = mat(name)
    P = nd(t, 'ShaderNodeNewGeometry'); bs, _ = principled(t)
    g = grey
    col = ramp(t, [(0.3, (g * 0.65, g * 0.65, g * 0.63, 1)), (0.7, (g * 1.2, g * 1.2, g * 1.15, 1))], noise(t, P, 2.5, 8))
    if streaks:  # vertical rain streaks: noise squashed in Z
        mp = nd(t, 'ShaderNodeMapping', ins={'Scale': (1.0, 1.0, 0.12)}); lk(t, P, 'Position', mp, 'Vector')
        sn = nd(t, 'ShaderNodeTexNoise', ins={'Scale': 5.0, 'Detail': 5}); lk(t, mp, 'Vector', sn, 'Vector')
        st = ramp(t, [(0.4, (0.5, 0.5, 0.48, 1)), (0.7, (1, 1, 1, 1))], sn)
        col = mix_mul(t, col, st)
    t.links.new(col.outputs[2 if col.bl_idname == 'ShaderNodeMix' else 0], bs.inputs['Base Color'])
    rm = nd(t, 'ShaderNodeMapRange', ins={'To Min': 0.7, 'To Max': 0.92}); lk(t, noise(t, P, 3, 4), 'Fac', rm, 'Value')
    lk(t, rm, 'Result', bs, 'Roughness')
    bump(t, bs, noise(t, P, 30, 6), 0.5, 0.02)
    return m

def m_town_wall():
    m, t = mat('Town_Wall')
    P = nd(t, 'ShaderNodeNewGeometry'); bs, _ = principled(t, Roughness=0.85)
    oi = nd(t, 'ShaderNodeObjectInfo')
    tones = [(0.18, 0.16, 0.14), (0.25, 0.2, 0.15), (0.12, 0.13, 0.15), (0.3, 0.28, 0.25), (0.2, 0.12, 0.1)]
    col = ramp(t, [(i / 4, c + (1,)) for i, c in enumerate(tones)], oi, 'Random')
    col.color_ramp.interpolation = 'CONSTANT'
    grime = ramp(t, [(0.3, (0.6, 0.6, 0.6, 1)), (0.7, (1, 1, 1, 1))], noise(t, P, 1.5, 8))
    mm = mix_mul(t, col, grime)
    t.links.new(mm.outputs[2], bs.inputs['Base Color'])
    bump(t, bs, noise(t, P, 40, 4), 0.3, 0.02)
    return m

WARM = [(0.0, (1.0, 0.60, 0.30, 1)), (1.0, (1.0, 0.72, 0.48, 1))]   # ~2700K -> ~3500K, driven by per-window 'tint'

def window_driver(t):  # returns (warm colour node, lit node, tint node)
    lit = nd(t, 'ShaderNodeAttribute', attribute_name='lit'); tint = nd(t, 'ShaderNodeAttribute', attribute_name='tint')
    return ramp(t, WARM, tint), lit, tint

def m_town_window():
    m, t = mat('Town_Window')
    bs, _ = principled(t, **{'Base Color': (0.01, 0.012, 0.015, 1), 'Roughness': 0.05})
    col, lit, tint = window_driver(t)
    lk(t, col, 'Color', bs, 'Emission Color')
    s = math_(t, 'MULTIPLY_ADD', None, 3.0, 1.5); t.links.new(tint.outputs['Fac'], s.inputs[0])
    s2 = nd(t, 'ShaderNodeMath', operation='MULTIPLY'); t.links.new(s.outputs[0], s2.inputs[0]); t.links.new(lit.outputs['Fac'], s2.inputs[1])
    lk(t, s2, 0, bs, 'Emission Strength')
    return m

def m_interior():  # emissive plane behind hero glass: strength 3-8, off where lit == 0
    m, t = mat('Hero_Interior')
    col, lit, tint = window_driver(t)
    em = nd(t, 'ShaderNodeEmission'); out = nd(t, 'ShaderNodeOutputMaterial')
    lk(t, col, 'Color', em, 'Color')
    s = nd(t, 'ShaderNodeMath', operation='MULTIPLY_ADD'); s.inputs[1].default_value = 5.0; s.inputs[2].default_value = 3.0
    t.links.new(tint.outputs['Fac'], s.inputs[0])
    s2 = nd(t, 'ShaderNodeMath', operation='MULTIPLY'); t.links.new(s.outputs[0], s2.inputs[0]); t.links.new(lit.outputs['Fac'], s2.inputs[1])
    lk(t, s2, 0, em, 'Strength'); lk(t, em, 0, out, 'Surface')
    return m

def m_glass():  # transparent to shadow rays: avoids caustic fireflies and keeps interior light cheap
    m, t = mat('Hero_Glass')
    out = nd(t, 'ShaderNodeOutputMaterial'); mx = nd(t, 'ShaderNodeMixShader'); lp = nd(t, 'ShaderNodeLightPath')
    g = nd(t, 'ShaderNodeBsdfPrincipled', ins={'Base Color': (0.85, 0.92, 0.92, 1), 'Roughness': 0.02, 'IOR': 1.45, 'Transmission Weight': 1.0})
    tr = nd(t, 'ShaderNodeBsdfTransparent')
    lk(t, lp, 'Is Shadow Ray', mx, 'Fac'); lk(t, g, 0, mx, 1); lk(t, tr, 0, mx, 2); lk(t, mx, 0, out, 'Surface')
    return m

def m_simple(name, color, rough=0.5, metal=0.0, **extra):
    m, t = mat(name)
    principled(t, **{'Base Color': color + (1,), 'Roughness': rough, 'Metallic': metal}, **extra)
    return m

def m_emit(name, color, strength):
    m, t = mat(name)
    em = nd(t, 'ShaderNodeEmission', ins={'Color': color + (1,), 'Strength': strength}); out = nd(t, 'ShaderNodeOutputMaterial')
    lk(t, em, 0, out, 'Surface')
    return m

def m_car_paint():
    m, t = mat('Car_Paint')
    bs, _ = principled(t, **{'Roughness': 0.25, 'Metallic': 0.35, 'Coat Weight': 1.0, 'Coat Roughness': 0.03})
    oi = nd(t, 'ShaderNodeObjectInfo')
    cols = [(0.02, 0.02, 0.025), (0.5, 0.5, 0.52), (0.4, 0.02, 0.02), (0.03, 0.08, 0.2), (0.12, 0.14, 0.12)]
    c = ramp(t, [(i / 4, x + (1,)) for i, x in enumerate(cols)], oi, 'Random'); c.color_ramp.interpolation = 'CONSTANT'
    lk(t, c, 'Color', bs, 'Base Color')
    return m

# ---------------------------------------------------------------- geometry builder
class B:
    def __init__(s, name, mats):
        s.name, s.mats, s.bm = name, mats, bmesh.new()
        s.lit = s.bm.faces.layers.float.new('lit'); s.tint = s.bm.faces.layers.float.new('tint')

    def _tag(s, r, mi):
        for f in {f for v in r['verts'] for f in v.link_faces}:
            f.material_index = mi

    def box(s, c, size, mi=0):
        s._tag(bmesh.ops.create_cube(s.bm, size=1.0, matrix=Matrix.LocRotScale(V(c), None, V(size))), mi)

    def cyl(s, c, r, h, mi=0, rot=None, seg=16):
        s._tag(bmesh.ops.create_cone(s.bm, cap_ends=True, cap_tris=False, segments=seg, radius1=r, radius2=r, depth=h,
                                     matrix=Matrix.LocRotScale(V(c), rot, None)), mi)

    def quad(s, pts, mi, lit=0.0, tint=0.0):
        f = s.bm.faces.new([s.bm.verts.new(p) for p in pts])
        f.material_index = mi; f[s.lit] = lit; f[s.tint] = tint

    def build(s, c):
        me = bpy.data.meshes.new(s.name)
        s.bm.to_mesh(me); s.bm.free()
        for m in s.mats:
            me.materials.append(m)
        return obj(s.name, me, c)

def obox(b, o, d, n, u, v, z0, z1, su, sv, mi=0):  # box on a facade frame: u along, v out of the wall
    c = o + d * u + n * v
    b.box((c.x, c.y, (z0 + z1) / 2), (abs(d.x) * su + abs(n.x) * sv, abs(d.y) * su + abs(n.y) * sv, z1 - z0), mi)

def wquad(b, o, d, n, u, w, zb, zt, v, mi, lit=0.0, tint=0.0):
    c = o + d * u + n * v
    p0, p1 = c - d * w / 2, c + d * w / 2
    b.quad([V((p0.x, p0.y, zb)), V((p1.x, p1.y, zb)), V((p1.x, p1.y, zt)), V((p0.x, p0.y, zt))], mi, lit, tint)

# ---------------------------------------------------------------- scene
def setup_scene():
    s = bpy.context.scene
    s.unit_settings.system, s.unit_settings.scale_length = 'METRIC', 1.0
    s.render.fps, s.render.resolution_x, s.render.resolution_y, s.render.resolution_percentage = 24, 1920, 1080, 100
    s.render.engine = 'CYCLES'
    s.cycles.samples, s.cycles.use_denoising, s.cycles.denoiser = 256, True, 'OPTIX'
    s.view_settings.view_transform = 'AgX'
    s.view_settings.look = 'AgX - Medium High Contrast'
    try:
        p = bpy.context.preferences.addons['cycles'].preferences
        p.compute_device_type = 'OPTIX'; p.get_devices()
        for d in p.devices:
            d.use = d.type == 'OPTIX'   # RTX 4060 only, CPU off
        s.cycles.device = 'GPU'
    except Exception as e:
        print('GPU setup skipped:', e)
    w = bpy.data.worlds.get('Night') or bpy.data.worlds.new('Night')
    bg = w.node_tree.nodes['Background']
    bg.inputs['Color'].default_value = (0.004, 0.007, 0.016, 1); bg.inputs['Strength'].default_value = 1.0
    s.world = w

# ---------------------------------------------------------------- street
def street(c):
    conc, asph = m_concrete('Pavement', 0.3, False), m_asphalt()
    paint = m_simple('Road_Paint', (0.7, 0.7, 0.62), 0.6)
    metal, head = m_simple('Pole_Metal', (0.04, 0.04, 0.045), 0.5, 0.9), m_emit('Lamp_Head', (1.0, 0.7, 0.35), 40.0)
    X = 120.0
    b = B('Ground_Lot', [conc]); b.box((0, 0, -0.05), (2 * X, 120, 0.1)); b.build(c)
    b = B('Road', [asph]); b.box((0, 0, 0.0), (2 * X, 10, 0.02)); b.build(c)
    b = B('Sidewalks', [conc])
    for s_ in (1, -1):
        b.box((0, s_ * 6.6, 0.075), (2 * X, 2.75, 0.15))     # y 5.25..7.95
        b.box((0, s_ * 5.125, 0.085), (2 * X, 0.25, 0.17))   # curb strip
    b.build(c)
    b = B('Road_Markings', [paint])
    for x in range(-116, 117, 8):
        b.box((x, 0, 0.015), (3.0, 0.15, 0.004))
    for k in range(10):
        b.box((26, -4.5 + k + 0.5, 0.015), (3.0, 0.5, 0.004))   # crosswalk
    b.build(c)
    # streetlights: one pole mesh, linked copies; south side rotated 180 deg so the arm reaches over the road
    pb = B('Streetlight', [metal, head])
    pb.cyl((0, 0, 3.5), 0.08, 7.0); pb.box((0, -1.1, 6.95), (0.1, 2.2, 0.1)); pb.box((0, -2.2, 6.85), (0.9, 0.4, 0.12), 1)
    pole = pb.build(c); pm = pole.data; bpy.data.objects.remove(pole)
    lights = [(x, 6.6, 0) for x in (-50, -25, 0, 25, 50)] + [(x, -6.6, math.pi) for x in (-37, 12.5, 37)]
    for i, (x, y, rz) in enumerate(lights):
        o = obj(f'Streetlight_{i}', pm, c); o.location, o.rotation_euler = (x, y, 0), (0, 0, rz)
        ly = y - math.cos(rz) * 2.2
        L = bpy.data.lights.new(f'StreetLamp_{i}', 'SPOT')
        L.color, L.energy, L.spot_size, L.spot_blend, L.shadow_soft_size = (1.0, 0.62, 0.3), 2000, math.radians(140), 0.8, 0.15
        obj(f'StreetLamp_{i}', L, c).location = (x, ly, 6.75)
    # parked cars: linked copies of one low-poly mesh (+X = front)
    paintm, glassm = m_car_paint(), m_simple('Car_Glass', (0.01, 0.012, 0.015), 0.05)
    cb = B('Car', [paintm, glassm, m_simple('Rubber', (0.015, 0.015, 0.015), 0.8)])
    cb.box((0, 0, 0.65), (4.5, 1.8, 0.7)); cb.box((-0.2, 0, 1.3), (2.4, 1.6, 0.6), 1); cb.box((-0.2, 0, 1.64), (2.5, 1.62, 0.08))
    for sx in (-1.4, 1.4):
        for sy in (-0.85, 0.85):
            cb.cyl((sx, sy, 0.33), 0.33, 0.22, 2, Matrix.Rotation(math.pi / 2, 3, 'X').to_quaternion(), 20)
    car = cb.build(c); cm = car.data; bpy.data.objects.remove(car)
    for i, (x, y, rz) in enumerate([(-24, -3.6, 0), (19, -3.6, 0), (-34, 3.6, math.pi), (11, 3.6, math.pi), (30, 3.6, math.pi)]):
        o = obj(f'Car_{i}', cm, c); o.location, o.rotation_euler = (x, y, 0), (0, 0, rz)
    cam = bpy.data.cameras.new('Cam_Preview'); cam.lens = 22
    co = obj('Cam_Preview', cam, c); co.location = (14, 3, 1.7)
    co.rotation_euler = (V((0, -15, 5.5)) - co.location).to_track_quat('-Z', 'Y').to_euler()
    bpy.context.scene.camera = co

# ---------------------------------------------------------------- background town
def town(c):
    wall, win = m_town_wall(), m_town_window()
    specs = [(-70, 1), (-46, 1), (-22, 1), (2, 1), (26, 1), (52, 1), (-32, -1), (30, -1)]
    for i, (x, sgn) in enumerate(specs):
        w, d, floors = rng.uniform(14, 20), rng.uniform(14, 18), rng.randint(4, 10)
        h, cy = floors * SH, sgn * (10 + d / 2)
        b = B(f'Town_{i}_Body', [wall]); b.box((x, cy, h / 2), (w, d, h)); b.box((x, cy, h + 0.4), (w + 0.4, d + 0.4, 0.8)); b.build(c)
        wb = B(f'Town_{i}_Windows', [win])
        for n_, d_ in FAC:
            n, dd = V(n_), V(d_)
            L, half = (w, d / 2) if n.y else (d, w / 2)
            o = V((x, cy, 0)) + n * (half + 0.02)
            cols = int(L // 3.2)
            for fl in range(floors):
                for k in range(cols):
                    wquad(wb, o, dd, n, (k - (cols - 1) / 2) * 3.2, 1.4, fl * SH + 0.9, fl * SH + 2.5, 0, 0,
                          1.0 if rng.random() < 0.6 else 0.0, rng.random())
        wb.build(c)

# ---------------------------------------------------------------- hero building
def hero(c):
    conc, glass, inter = m_concrete('Hero_Concrete', 0.35), m_glass(), m_interior()
    frame = m_simple('Hero_Frame', (0.03, 0.03, 0.035), 0.4, 0.8)
    ac, rail = m_simple('Hero_AC', (0.55, 0.55, 0.55), 0.5), m_simple('Hero_Rail', (0.02, 0.02, 0.02), 0.45, 0.9)
    ctr, cx, cy, T = V((HERO_C.x, HERO_C.y, 0)), HERO_C.x, HERO_C.y, WALL
    inner_y = HERO_D / 2 - T
    fb = B('Hero_Foundation', [conc]); fb.box((cx, cy, 0.1), (HERO_W + 0.4, HERO_D + 0.4, 0.2)); fb.build(c)
    for i in range(STOREYS):
        z0, z1 = i * SH, (i + 1) * SH
        cb, db = B(f'Hero_S{i}_Concrete', [conc]), B(f'Hero_S{i}_Details', [frame, glass, inter, ac, rail])
        hx = HERO_W / 2 - T
        for xa, xb, ya, yb in [(-hx, -CORE_HX, -inner_y, inner_y), (CORE_HX, hx, -inner_y, inner_y),
                               (-CORE_HX, CORE_HX, -inner_y, -CORE_HY), (-CORE_HX, CORE_HX, CORE_HY, inner_y)]:
            cb.box((cx + (xa + xb) / 2, cy + (ya + yb) / 2, z1 - 0.15), (xb - xa, yb - ya, 0.3))   # ceiling slab, shaft opening
        for n_, d_ in FAC:
            n, d = V(n_), V(d_)
            front = n.y != 0
            half = HERO_D / 2 if front else HERO_W / 2
            L, nb = (HERO_W, 5) if front else (HERO_D - 2 * T, 3)
            bay = L / nb
            o = ctr + n * (half - T / 2)
            prev = -L / 2
            for k in range(nb):
                u = -L / 2 + bay * (k + 0.5)
                door = i == 0 and n.y > 0 and k == 2
                w, zb, zt = 1.6, (0.2 if door else z0 + 0.9), (2.2 if door else z0 + 2.5)
                obox(cb, o, d, n, (prev + u - w / 2) / 2, 0, z0, z1, u - w / 2 - prev, T)
                if zb > z0:
                    obox(cb, o, d, n, u, 0, z0, zb, w, T)
                obox(cb, o, d, n, u, 0, zt, z1, w, T)
                prev = u + w / 2
                wquad(db, o, d, n, u, w, zb, zt, 0, 1)
                wquad(db, o, d, n, u, w, zb, zt, -0.7, 2, 1.0 if rng.random() < 0.75 else 0.0, rng.random())
                for uu in (u - w / 2 + 0.03, u + w / 2 - 0.03, u):
                    obox(db, o, d, n, uu, 0.02, zb, zt, 0.06, 0.1)
                for zz in (zb + 0.03, zt - 0.03):
                    obox(db, o, d, n, u, 0.02, zz - 0.03, zz + 0.03, w, 0.1)
                if n.y > 0 and i >= 1 and k in (1, 3):   # balcony (street side = +y)
                    vb = T / 2
                    obox(cb, o, d, n, u, vb + 0.7, z0 - 0.2, z0, 3.0, 1.5)
                    obox(db, o, d, n, u, vb + 1.45, z0 + 1.0, z0 + 1.05, 3.0, 0.05, 4)
                    for s_ in (-1.475, 1.475):
                        obox(db, o, d, n, u + s_, vb + 0.75, z0 + 1.0, z0 + 1.05, 0.05, 1.5, 4)
                        obox(db, o, d, n, u + s_, vb + 0.75, z0, z0 + 1.0, 0.04, 0.04, 4)
                    for j in range(7):
                        obox(db, o, d, n, u - 1.45 + j * 2.9 / 6, vb + 1.45, z0, z0 + 1.0, 0.04, 0.04, 4)
                if n.y > 0 and k in (0, 4) and rng.random() < 0.7:   # AC unit under the sill
                    obox(db, o, d, n, u, T / 2 + 0.2, z0 + 0.2, z0 + 0.75, 0.8, 0.4, 3)
            obox(cb, o, d, n, (prev + L / 2) / 2, 0, z0, z1, L / 2 - prev, T)
            if i == STOREYS - 1:
                obox(cb, o, d, n, 0, 0, z1, z1 + 0.5, L, T)   # parapet
        cb.build(c); db.build(c)
    # stairwell core: separate object, never fractured. U-shaped stair, door in the front wall each storey.
    k = B('Hero_StairCore', [conc]); H = STOREYS * SH + 0.5; t = T
    for sx in (-1, 1):
        k.box((cx + sx * (CORE_HX - t / 2), cy, H / 2), (t, 2 * CORE_HY, H))
    k.box((cx, cy - CORE_HY + t / 2, H / 2), (2 * CORE_HX - 2 * t, t, H))
    fy = cy + CORE_HY - t / 2   # door side faces the street (+y)
    for i in range(STOREYS):
        z0, z1 = i * SH, (i + 1) * SH + (0.5 if i == STOREYS - 1 else 0)
        for sx in (-1.15, 1.15):
            k.box((cx + sx, fy, (z0 + z1) / 2), (1.1, t, z1 - z0))
        k.box((cx, fy, (z0 + 2.2 + z1) / 2), (1.2, t, z1 - z0 - 2.2))
        for r in range(10):   # flight A (-y, x=-0.85), landing, flight B (+y, x=+0.85) back to the door side
            k.box((cx - 0.85, cy + 1.9 - 0.38 * (r + 0.5), z0 + 0.15 * (r + 1) - 0.125), (1.5, 0.38, 0.25))
            k.box((cx + 0.85, cy - 1.9 + 0.38 * (r + 0.5), z0 + 1.5 + 0.15 * (r + 1) - 0.125), (1.5, 0.38, 0.25))
        k.box((cx, cy - 2.05, z0 + 1.375), (3.4, 0.3, 0.25))
        k.box((cx, cy + 2.05, z0 + SH - 0.125), (3.4, 0.3, 0.25))
    k.build(c)

if RUN['scene']:
    setup_scene()
if RUN['street']:
    street(coll('Street'))
if RUN['town']:
    town(coll('Town'))
if RUN['hero']:
    hero(coll('Hero'))
bpy.data.orphans_purge(do_recursive=True)
print('Stage 1 done:', {c.name: len(c.objects) for c in bpy.data.collections})
