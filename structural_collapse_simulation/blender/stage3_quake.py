# Sanjeevni - Stage 3: quake envelope + shake noise, used by stage 4-5 for the camera shake.
# Ground is NOT keyframed: Blender teleports a kinematic body once per frame, the velocity spike snaps the fixed constraints
# (tested: even 1.8 cm shake collapses the building by frame 24). The quake is sold by camera shake; the collapse timing comes from stage 2.
# Envelope: ramp 6-34, main shock to 70, decay to ~0 by 185, aftershock at 205.
import math, random

def ss(a, b, x):
    t = min(1.0, max(0.0, (x - a) / (b - a)))
    return t * t * (3 - 2 * t)

def env(f):
    return max(ss(6, 34, f) * (1 - 0.97 * ss(70, 185, f)), 0.45 * math.exp(-((f - 205) / 9) ** 2))

def mk(seed, freqs):   # smooth deterministic noise: sum of sines (Hz), ~[-1, 1]
    r = random.Random(seed)
    ph = [(fr, r.uniform(0, 6.283)) for fr in freqs]
    return lambda f: sum(math.sin(2 * math.pi * fr * f / 24 + p) for fr, p in ph) / len(ph) * 1.6
