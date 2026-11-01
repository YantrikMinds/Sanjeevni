# Sanjeevni - Stage 2: destruction rig. Blender 5.1.1. Run AFTER stage1_scene.py (hero freshly built; re-run stage1 with only hero=True to reset).
# Own Voronoi fracture (Cell Fracture / Rigid Body Tools are extensions in 5.x, not needed).
# Per floor: seeds on the mid-surface of the concrete -> convex cells by plane bisection -> chunks (Hero_Chunks) -> fixed constraints (Hero_Constraints).
# Cascade = breaking thresholds (insurance) + keyframed constraint 'enabled' per floor, bottom-up (guaranteed, set SCHEDULE=False for pure physics).
import bpy, bmesh, random, time
from mathutils import Vector, Matrix
from mathutils.kdtree import KDTree

SEED = 2024
STOREYS = 4
CHUNK = globals().get('CHUNK', 1.2)                  # target chunk size (m): ~230 chunks/floor. 1.0 -> ~330/floor (heavier bake)
SHRINK = 0.985               # per-chunk scale about its centre = visual gap, so neighbours never interpenetrate on frame 1
K_NEAR = 24                  # Voronoi neighbours tested per cell
LINK_DIST = 1.7 * CHUNK      # max centre distance for a constraint
K_BREAK = (30, 45, 60, 80)   # breaking threshold = K * weight impulse of the lighter chunk, per floor (ground floor weakest)
FAIL = ((40, 64), (60, 90), (80, 112), (100, 130))   # frame windows in which each floor's constraints are released
EPI_X = -7.0                 # failure wave travels +x from here
SCHEDULE = True
END = 336
DENSITY = 2400.0
rng = random.Random(SEED)
V = Vector
t0 = time.time()

# ---------------------------------------------------------------- cleanup
_ov = None   # ops need a 3D view: borrow one when run from outside the UI (MCP socket); headless has no windows
for _w in bpy.context.window_manager.windows:
    for _a in _w.screen.areas:
        if _a.type == 'VIEW_3D' and not _ov:
            _ov = bpy.context.temp_override(window=_w, screen=_w.screen, area=_a, region=next(r for r in _a.regions if r.type == 'WINDOW'))
if _ov:
    _ov.__enter__()
if bpy.context.object and bpy.context.object.mode != 'OBJECT':   # object ops fail in Edit Mode
    bpy.ops.object.mode_set(mode='OBJECT')
sc = bpy.context.scene
for n in ('Hero_Chunks', 'Hero_Constraints'):
    c = bpy.data.collections.get(n)
    if c:
        for o in list(c.objects):
            bpy.data.objects.remove(o)
        bpy.data.collections.remove(c)
if sc.rigidbody_world:
    bpy.ops.rigidbody.world_remove()
for n in ('RigidBodyWorld', 'RigidBodyConstraints'):
    if bpy.data.collections.get(n):
        bpy.data.collections.remove(bpy.data.collections[n])

def new_coll(n):
    c = bpy.data.collections.new(n)
    sc.collection.children.link(c)
    return c

cc, kc = new_coll('Hero_Chunks'), new_coll('Hero_Constraints')
# every hero-type building (the hero + the Town_Hero_k copies from add_town.py) gets the same rig; objects are found per collection (copies are named Hero_S0_Concrete.001 ...)
BLD = []
for cn in ['Hero'] + sorted(c.name for c in bpy.data.collections if c.name.startswith('Town_Hero_')):
    cl = bpy.data.collections[cn].objects
    pick = lambda pre: next(o for o in cl if o.name.startswith(pre))
    core = pick('Hero_StairCore')
    cx = sum((core.matrix_world @ V(b) for b in core.bound_box), V()).x / 8
    src_ = [pick(f'Hero_S{i}_Concrete') for i in range(STOREYS)]
    BLD.append(dict(src=src_, det=[pick(f'Hero_S{i}_Details') for i in range(STOREYS)], core=core, cx=cx, mat=src_[0].data.materials[0]))

# ---------------------------------------------------------------- material: texture coords must travel with the chunk (world Position would swim)
for conc in {b['mat'] for b in BLD}:
    t = conc.node_tree
    for g in [n for n in t.nodes if n.bl_idname == 'ShaderNodeNewGeometry']:
        for l in list(g.outputs['Position'].links):
            a = t.nodes.new('ShaderNodeAttribute'); a.attribute_name = 'rest_pos'
            t.links.new(a.outputs['Vector'], l.to_socket)

# ---------------------------------------------------------------- fracture
def seeds_for(o):
    me = o.data
    polys = [(p.area, [me.vertices[i].co.copy() for i in p.vertices], p.normal.copy()) for p in me.polygons]
    cum, s = [], 0.0
    for a, _, _ in polys:
        s += a; cum.append(s)
    pts, miss, r2 = [], 0, (0.85 * CHUNK) ** 2
    while miss < 500:
        _, vs, n = rng.choices(polys, cum_weights=cum)[0]
        p = vs[0] + (vs[1] - vs[0]) * rng.random() + (vs[3] - vs[0]) * rng.random() - n * 0.15   # all faces are cube quads; 0.15 = half wall thickness
        if all((p - q).length_squared > r2 for q in pts):
            pts.append(p); miss = 0
        else:
            miss += 1
    return pts

def fracture(o, fl, bi):
    pts = seeds_for(o)
    kd = KDTree(len(pts))
    for i, p in enumerate(pts):
        kd.insert(p, i)
    kd.balance()
    out, vsum = [], 0.0
    for i, p in enumerate(pts):
        bm = bmesh.new(); bm.from_mesh(o.data)
        for q, j, _ in kd.find_n(p, K_NEAR + 1):
            if j == i:
                continue
            n, co = (q - p).normalized(), (p + q) / 2
            if any((v.co - co).dot(n) > 1e-6 for v in bm.verts):
                cut = bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], dist=1e-6, plane_co=co, plane_no=n, clear_outer=True)['geom_cut']
                bd = [e for e in cut if isinstance(e, bmesh.types.BMEdge) and e.is_valid and e.is_boundary]
                if bd:   # cap every cut right away so later cuts clip a closed solid (filling once at the end tangles the loops)
                    bmesh.ops.holes_fill(bm, edges=bd, sides=64)
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        vol = bm.calc_volume() if bm.faces else 0.0
        if vol < 1e-4:
            bm.free(); continue
        me = bpy.data.meshes.new(f'Chunk_S{fl}_{i}'); bm.to_mesh(me); bm.free()
        me.materials.append(o.data.materials[0])
        co = [v.co.copy() for v in me.vertices]
        ra = me.attributes.new('rest_pos', 'FLOAT_VECTOR', 'POINT')
        ra.data.foreach_set('vector', [x for c_ in co for x in c_])
        cen = sum(co, V()) / len(co)
        lo, hi = V(map(min, zip(*co))), V(map(max, zip(*co)))
        me.transform(Matrix.Translation(-cen)); me.transform(Matrix.Scale(SHRINK, 4))
        ch = bpy.data.objects.new(me.name, me); ch.location = cen + V((0, 0, 0.006 if lo.z < 0.02 else 0)); cc.objects.link(ch)   # lift ground-level chunks off the ground so frame 1 has no contact
        out.append(dict(o=ch, vol=vol, lo=lo, hi=hi, c=cen, fl=fl, b=bi))
        vsum += vol
    ref = bmesh.new(); ref.from_mesh(o.data); vref = ref.calc_volume(); ref.free()
    print(f'  S{fl}: {len(out)} chunks, volume {vsum:.2f} / {vref:.2f} m3 ({100 * vsum / vref:.1f}%)')
    return out

chunks = []
for bi, B_ in enumerate(BLD):
    for i, o in enumerate(B_['src']):
        chunks += fracture(o, i, bi)
        bpy.data.objects.remove(o)
print('fracture', round(time.time() - t0, 1), 's, chunks', len(chunks))

# ---------------------------------------------------------------- details (frames, glass, interiors, balconies, AC): split loose parts, parent to nearest chunk of their floor
def split_parent(det, fl, bi):
    ids = [c for c in chunks if c['fl'] == fl and c['b'] == bi]; kd = KDTree(len(ids))
    for k, c in enumerate(ids):
        kd.insert(c['c'], k)
    kd.balance()
    bpy.ops.object.select_all(action='DESELECT')
    det.select_set(True); bpy.context.view_layer.objects.active = det
    before = set(bpy.data.objects.keys())
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.separate(type='LOOSE'); bpy.ops.object.mode_set(mode='OBJECT')
    for p in [det] + [bpy.data.objects[n] for n in set(bpy.data.objects.keys()) - before]:
        m = sum((V(b) for b in p.bound_box), V()) / 8
        ch = ids[kd.find(m)[1]]['o']
        p.parent = ch; p.matrix_parent_inverse = Matrix.Translation(-ch.location)

for bi, B_ in enumerate(BLD):
    for i in range(STOREYS):
        split_parent(B_['det'][i], i, bi)
print('details', round(time.time() - t0, 1), 's')

# ---------------------------------------------------------------- rigid body world
bpy.ops.rigidbody.world_add()
rbw = sc.rigidbody_world
rbw.substeps_per_frame, rbw.solver_iterations, rbw.time_scale = 20, 40, 1.0
rbw.point_cache.frame_start, rbw.point_cache.frame_end = 1, END
sc.frame_start, sc.frame_end = 1, END

def select(objs):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]

select([c['o'] for c in chunks])
bpy.ops.rigidbody.objects_add(type='ACTIVE')
mavg = DENSITY * sum(c['vol'] for c in chunks) / len(chunks)
for c in chunks:
    rb = c['o'].rigid_body
    rb.mass = max(5.0, DENSITY * c['vol'])
    rb.friction, rb.restitution = 0.85, 0.0
    rb.linear_damping, rb.angular_damping = 0.15, 0.6
    rb.collision_shape, rb.use_margin, rb.collision_margin = 'CONVEX_HULL', True, 0.002
    rb.use_deactivation = False
    c['m'] = rb.mass

# ---------------------------------------------------------------- gravel: loose rubble resting on every slab (and the roof); it rains down as floors fail
N_DEBRIS = globals().get('N_DEBRIS', 1100)
LEVELS = globals().get('LEVELS', (0, 1, 2, 3, 4))
dr = random.Random(77)
bbs = [(V(map(min, zip(*[c['lo'] for c in chunks if c['b'] == b]))), V(map(max, zip(*[c['hi'] for c in chunks if c['b'] == b])))) for b in range(len(BLD))]
dcol = new_coll('Hero_Debris')
gmats = []
for gi, gc in enumerate(((0.30, 0.29, 0.27), (0.40, 0.33, 0.28), (0.22, 0.22, 0.22))):
    gm = bpy.data.materials.new(f'M_Gravel{gi}'); gm.use_nodes = True; gb = gm.node_tree.nodes['Principled BSDF']
    gb.inputs['Base Color'].default_value, gb.inputs['Roughness'].default_value = (*gc, 1), 0.92
    gmats.append(gm)
gmeshes = []
for gi in range(9):
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=1, radius=1.0)
    for v in bm.verts:
        v.co = V((v.co.x * dr.uniform(0.6, 1.2), v.co.y * dr.uniform(0.6, 1.2), v.co.z * dr.uniform(0.5, 1.1)))   # irregular convex lump
    me = bpy.data.meshes.new(f'Gravel{gi}'); bm.to_mesh(me); bm.free(); me.materials.append(gmats[gi % 3]); gmeshes.append(me)
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()
debris, dpos, tries = [], [], 0
N_DEBRIS *= len(BLD)   # per building; tries alternate between buildings
while len(debris) < N_DEBRIS and tries < 20000 * len(BLD):
    tries += 1
    bb_lo, bb_hi = bbs[tries % len(BLD)]
    fl = dr.choice(LEVELS)   # 0-3 slabs, 4 = roof
    z0, dist = (3.0 * fl + 2.6, 3.2) if fl < 4 else (13.0, 1.2)
    x, y = dr.uniform(bb_lo.x + 0.3, bb_hi.x - 0.3), dr.uniform(bb_lo.y + 0.3, bb_hi.y - 0.3)
    hit, loc, nor, _, ho, _ = sc.ray_cast(dg, V((x, y, z0)), V((0, 0, -1)), distance=dist)
    if not (hit and ho.name.startswith('Chunk_') and nor.z > 0.8):
        continue
    if any((loc - q).length < 0.8 for q in dpos):   # overlapping convex hulls at frame 1 = solver kick that breaks the constraints
        continue
    # needs flat floor under the whole footprint and free air around it (a piece starting inside a wall or on a chunk lip gets kicked and breaks the constraints)
    if any(not (lambda r: r[0] and abs(r[1].z - loc.z) < 0.02)(sc.ray_cast(dg, loc + V((dx, dy, 0.5)), V((0, 0, -1)), distance=1.0))
           for dx, dy in ((0.4, 0), (-0.4, 0), (0, 0.4), (0, -0.4), (0.3, 0.3), (-0.3, -0.3), (0.3, -0.3), (-0.3, 0.3))):
        continue
    if any(sc.ray_cast(dg, loc + V((0, 0, h)), V(dv), distance=0.5)[0] for h in (0.12, 0.35) for dv in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0.7, 0.7, 0), (-0.7, -0.7, 0), (0.7, -0.7, 0), (-0.7, 0.7, 0))):
        continue
    s = V((dr.uniform(0.07, 0.25), dr.uniform(0.07, 0.25), dr.uniform(0.05, 0.18)))
    me = dr.choice(gmeshes)
    rot = Matrix.Rotation(dr.uniform(0, 6.28), 3, 'Z') @ Matrix.Rotation(dr.uniform(0, 6.28), 3, 'X') @ Matrix.Rotation(dr.uniform(0, 6.28), 3, 'Y')
    low = min((rot @ V((v.co.x * s.x, v.co.y * s.y, v.co.z * s.z))).z for v in me.vertices)   # rest the lowest vertex on the slab, whatever the tilt
    d = bpy.data.objects.new(f'Debris_{len(debris)}', me); dcol.objects.link(d)
    d.scale, d.location, d.rotation_euler = s, loc + V((0, 0, 0.012 - low)), rot.to_euler()
    debris.append(d); dpos.append(loc)
print('debris', len(debris), 'of', N_DEBRIS, 'tries', tries)
if debris:
    select(debris)
    bpy.ops.rigidbody.objects_add(type='ACTIVE')
    for d in debris:
        rb = d.rigid_body
        rb.mass = max(1.0, DENSITY * 4.19 * d.scale.x * d.scale.y * d.scale.z)
        rb.friction, rb.restitution, rb.linear_damping, rb.angular_damping = 0.8, 0.0, 0.1, 0.4
        rb.collision_shape, rb.use_margin, rb.collision_margin, rb.use_deactivation = 'CONVEX_HULL', True, 0.001, False

# static world: animated (kinematic) so stage 3 can shake it. Hero_Foundation is visual only (it overlaps ground-floor chunks).
STATIC = {'Ground_Lot': 'BOX', 'Road': 'BOX', 'Sidewalks': 'MESH', **{b['core'].name: 'MESH' for b in BLD}}
stat = [bpy.data.objects[n] for n in STATIC if n in bpy.data.objects]
for o in stat:   # Blender centres BOX colliders on the object origin, not the mesh bounds: move the origin to the bbox centre (else the ground sits 5 cm high)
    if STATIC[o.name] == 'BOX':
        bc = sum((V(b) for b in o.bound_box), V()) / 8
        o.data.transform(Matrix.Translation(-bc)); o.location += bc
select(stat)
bpy.ops.rigidbody.objects_add(type='PASSIVE')
for o in stat:
    rb = o.rigid_body
    rb.kinematic, rb.collision_shape, rb.friction, rb.restitution = True, STATIC[o.name], 0.9, 0.0
    rb.use_margin, rb.collision_margin = True, 0.0
ground = bpy.data.objects['Ground_Lot']

# ---------------------------------------------------------------- constraints
dt = 1.0 / (sc.render.fps * rbw.substeps_per_frame)
links = []
for bi, B_ in enumerate(BLD):
    mine = [c for c in chunks if c['b'] == bi]
    for a in range(len(mine)):
        A = mine[a]
        for b in range(a + 1, len(mine)):
            B = mine[b]
            if (A['c'] - B['c']).length > LINK_DIST:
                continue
            if all(A['lo'][k] - 0.05 <= B['hi'][k] and B['lo'][k] - 0.05 <= A['hi'][k] for k in range(3)):
                links.append((A, B, (A['c'] + B['c']) / 2, min(A['fl'], B['fl']), min(A['m'], B['m']), bi))
    for A in mine:
        if A['fl'] == 0 and A['lo'].z < 0.05:   # ground floor anchored to the ground until it fails
            links.append((A, dict(o=ground, m=A['m']), V((A['c'].x, A['c'].y, 0.0)), 0, A['m'], bi))
    core = B_['core']
    core.data.materials.clear(); core.data.materials.append(B_['mat'])   # was flat white; the concrete shader reads rest_pos, so give the core its own
    core.data.attributes.new('rest_pos', 'FLOAT_VECTOR', 'POINT').data.foreach_set('vector', [x for v in core.data.vertices for x in (core.matrix_world @ v.co)])
    # L-shaped chunks at the shaft corners have hulls that overlap the core: tie them to it (also kills their collision until release)
    cb = [V(b) for b in core.bound_box]
    clo, chi = V(map(min, zip(*cb))), V(map(max, zip(*cb)))
    for A in mine:
        if all(A['lo'][k] - 0.1 <= chi[k] and clo[k] - 0.1 <= A['hi'][k] for k in range(3)):
            links.append((A, dict(o=core, m=A['m']), A['c'], A['fl'], A['m'], bi))
print('links', len(links))

tmpl = bpy.data.objects.new('RBC_tmpl', None); tmpl.empty_display_size = 0.08; kc.objects.link(tmpl)
select([tmpl])
bpy.ops.rigidbody.constraint_add(type='FIXED')
rcons = rbw.constraints
for k, (A, B, p, fl, m, bi) in enumerate(links):
    e = tmpl.copy(); e.name = f'RBC_{k}'; e.location = p
    kc.objects.link(e)
    if e.name not in rcons.objects:
        rcons.objects.link(e)
    r = e.rigid_body_constraint
    r.object1, r.object2 = A['o'], B['o']
    r.disable_collisions, r.use_breaking = B['o'] is not ground, True   # Bullet keeps the no-collide pair even after release: the ground must stay collidable
    r.breaking_threshold = K_BREAK[fl] * max(m, 0.3 * mavg) * 9.81 * dt
    if SCHEDULE:
        a, b = FAIL[fl]
        cx = BLD[bi]['cx']   # wave starts at the building's own left side; copies fail a few frames after the hero
        f = int(a + round(0.15 * abs(cx)) + (b - a) * min(1.0, max(0.0, (p.x - cx - EPI_X) / 18.0) * 0.8 + rng.random() * 0.2))
        e.keyframe_insert('rigid_body_constraint.enabled', frame=1)
        r.enabled = False
        e.keyframe_insert('rigid_body_constraint.enabled', frame=f)
        r.enabled = True
bpy.data.objects.remove(tmpl)
bpy.context.view_layer.layer_collection.children['Hero_Constraints'].hide_viewport = True

# ---------------------------------------------------------------- settle test: sim the quiet first frames, delete any gravel that gets kicked (hull overlaps the raycasts can't see), repeat until clean
def reset_cache():
    rbw.time_scale = 0.999; rbw.time_scale = 1.0   # rna update invalidates the point cache
for it in range(8):
    sc.frame_set(1)
    p1 = {o.name: o.matrix_world.translation.copy() for o in debris + [c['o'] for c in chunks]}
    for f in range(2, 13):
        sc.frame_set(f)
    moved = [o for o in debris if (o.matrix_world.translation - p1[o.name]).length > 0.05]
    cmoved = sum(1 for c in chunks if (c['o'].matrix_world.translation - p1[c['o'].name]).length > 0.05)
    print(f'settle pass {it}: {len(moved)} gravel kicked, {cmoved} chunks moved')
    if not moved:
        break
    for o in moved:
        debris.remove(o); bpy.data.objects.remove(o)
    reset_cache()
sc.frame_set(1)
bpy.data.orphans_purge(do_recursive=True)
if _ov:
    _ov.__exit__(None, None, None)
print('Stage 2 done:', len(chunks), 'chunks,', len(links), 'constraints,', round(time.time() - t0, 1), 's')
