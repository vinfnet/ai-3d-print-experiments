"""
Generate STL files for a hanging fridge can rack.

The rack clips onto the front edge of a typical glass fridge shelf and hangs
underneath it, holding a single row of 330ml drink cans lying on their side,
axis left-right, so the row runs front-to-back into the fridge.

A 380mm deep shelf fits FIVE 330ml cans (Ø66mm each, 72mm bay pitch → 364mm).

Printable parts (all fit a 220 x 220mm bed):
  fridge_can_rack_bay.stl         x5  — one can bay, 72mm long
  fridge_can_rack_shelf_clip.stl  x2  — wraps the glass front edge
  fridge_can_rack_end_stop.stl    x1  — rear stop wall

  fridge_can_rack_assembly.stl        — preview of the assembled rack
                                        (visualisation only, do not print)

All parts are exported already rotated into their recommended print
orientation, with Z-min = 0.
"""

import numpy as np
from stl import mesh

# ═══════════════════════════════════════════════════════════════════════
#  Design parameters (millimetres)
# ═══════════════════════════════════════════════════════════════════════

CAN_DIA = 66.3          # 330ml sleek/standard can diameter
CAN_LEN = 115.0         # 330ml can height (lying down → length across fridge)

SHELF_DEPTH = 380.0     # glass shelf depth
GLASS_T = 6.0           # glass shelf thickness — MEASURE YOURS AND EDIT

N_BAYS = 5              # cans in the row
BAY = 72.0              # bay pitch along the fridge depth

W_IN = 121.0            # clear inner width (can length + play)
WALL = 3.0              # side wall thickness
X_IN = W_IN / 2         # 60.5 — inner face of side wall
X_OUT = X_IN + WALL     # 63.5 — outer face of side wall

FLOOR_T = 3.0           # floor plate thickness
WALL_H = 71.0           # floor top → glass underside
Z_FLOOR = FLOOR_T                    # 3.0  — top of floor (cans roll on this)
Z_GLASS_BOT = Z_FLOOR + WALL_H       # 74.0 — glass underside / top of walls
Z_GLASS_TOP = Z_GLASS_BOT + GLASS_T  # 80.0 — glass top surface

RIDGE_H = 6.0           # ramp between bays that stops cans rolling
RIDGE_LEN = 8.0

LAP = 18.0              # lap-joint overlap length
X_LAP_MID = X_IN + WALL / 2     # 62.0 — split plane of the lapped wall
LAP_GAP = 0.2                   # sliding clearance on the lap joint
X_TAB_IN = X_LAP_MID + LAP_GAP  # 62.2 — inner face of the outer lap plate

BUMP_Y0, BUMP_Y1 = 6.0, 14.0    # snap bump on the inner lap plate
BUMP_RAMP = 3.0
BUMP_Z0, BUMP_Z1 = 32.0, 42.0
BUMP_X1 = X_OUT - 0.1           # 63.4 — bump tip
WIN_Y0, WIN_Y1 = 5.0, 15.0      # matching window in the outer lap plate
WIN_Z0, WIN_Z1 = 31.0, 43.0

CLIP_FLANGE_LEN = 140.0   # how far the clip lies back on top of the glass
CLIP_FLANGE_X0 = 40.0     # inner edge of the top flange
CLIP_T = 3.0
CLIP_NOSE = 9.0           # thickness of the wrap in front of the glass edge
CLIP_RISER_X0 = 59.0      # keeps the loading mouth 118mm clear
CLIP_RISER_X1 = X_OUT + 1.0

STOP_H = 40.0             # rear stop wall height
STOP_T = 4.0

RACK_LEN = N_BAYS * BAY + STOP_T   # under-shelf footprint, front to back


# ═══════════════════════════════════════════════════════════════════════
#  Primitives — everything is an axis-aligned prism
# ═══════════════════════════════════════════════════════════════════════

def prism(poly, axis, c0, c1):
    """Extrude a 2D polygon along `axis` from c0 to c1.

    `poly` is a list of (u, v) points; the (u, v, axis) triads are
    right-handed:  z → (x, y),  x → (y, z),  y → (z, x).
    The polygon is auto-oriented so that normals point outward.
    """
    pts = [np.asarray(p, dtype=float) for p in poly]

    # Shoelace — make sure the polygon is counter-clockwise in (u, v)
    area = 0.0
    for i in range(len(pts)):
        u0, v0 = pts[i]
        u1, v1 = pts[(i + 1) % len(pts)]
        area += u0 * v1 - u1 * v0
    if area < 0:
        pts = pts[::-1]

    def to3d(u, v, c):
        if axis == 'z':
            return np.array([u, v, c])
        if axis == 'x':
            return np.array([c, u, v])
        return np.array([v, c, u])          # axis == 'y'

    lo = [to3d(u, v, c0) for u, v in pts]
    hi = [to3d(u, v, c1) for u, v in pts]

    tris = []
    n = len(pts)

    # Side walls
    for i in range(n):
        j = (i + 1) % n
        tris += [[lo[i], lo[j], hi[j]],
                 [lo[i], hi[j], hi[i]]]

    # Caps — fan triangulation (all polygons used here are convex)
    for i in range(1, n - 1):
        tris.append([lo[0], lo[i + 1], lo[i]])   # c0 cap faces -axis
        tris.append([hi[0], hi[i], hi[i + 1]])   # c1 cap faces +axis

    return tris


def box(x0, x1, y0, y1, z0, z1):
    """Axis-aligned box with outward normals."""
    return prism([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], 'z', z0, z1)


def mirror_x(tris):
    """Mirror across X = 0, keeping normals outward."""
    out = []
    for t in tris:
        m = [np.array([-v[0], v[1], v[2]]) for v in t]
        out.append([m[0], m[2], m[1]])
    return out


def translate(tris, dx=0.0, dy=0.0, dz=0.0):
    d = np.array([dx, dy, dz], dtype=float)
    return [[v + d for v in t] for t in tris]


def rotate(tris, matrix):
    m = np.asarray(matrix, dtype=float)
    return [[m @ v for v in t] for t in tris]


ROT_LAY_ON_SIDE = [[0, 0, 1],   # (x, y, z) → (z, y, -x): outer side face down
                   [0, 1, 0],
                   [-1, 0, 0]]

ROT_LAY_ON_BACK = [[1, 0, 0],   # (x, y, z) → (x, z, -y): rear face down
                   [0, 0, 1],
                   [0, -1, 0]]


# ═══════════════════════════════════════════════════════════════════════
#  Shared wall features
# ═══════════════════════════════════════════════════════════════════════

def inner_lap_plate(y0):
    """Inner half of the lapped wall + snap bump (the 'male' half of a joint).

    Occupies y0 … y0+LAP on the +X side.
    """
    tris = box(X_IN, X_LAP_MID, y0, y0 + LAP, Z_FLOOR, Z_GLASS_BOT)

    # Snap bump with a lead-in ramp on the entry (far) side
    tris += box(X_LAP_MID, BUMP_X1, y0 + BUMP_Y0, y0 + BUMP_Y1 - BUMP_RAMP,
                BUMP_Z0, BUMP_Z1)
    tris += prism([(X_LAP_MID, y0 + BUMP_Y1),
                   (X_LAP_MID, y0 + BUMP_Y1 - BUMP_RAMP),
                   (BUMP_X1, y0 + BUMP_Y1 - BUMP_RAMP)],
                  'z', BUMP_Z0, BUMP_Z1)
    return tris


def outer_lap_plate(y0):
    """Outer half of the lapped wall, pierced by the snap window
    (the 'female' half of a joint). Occupies y0 … y0+LAP on the +X side."""
    x0, x1 = X_TAB_IN, X_OUT
    tris = []
    tris += box(x0, x1, y0, y0 + LAP, Z_FLOOR, WIN_Z0)
    tris += box(x0, x1, y0, y0 + LAP, WIN_Z1, Z_GLASS_BOT)
    tris += box(x0, x1, y0, y0 + WIN_Y0, WIN_Z0, WIN_Z1)
    tris += box(x0, x1, y0 + WIN_Y1, y0 + LAP, WIN_Z0, WIN_Z1)
    return tris


# ═══════════════════════════════════════════════════════════════════════
#  Part 1 — can bay module (print x5)
# ═══════════════════════════════════════════════════════════════════════

def bay_module():
    tris = []

    # Floor
    tris += box(-X_OUT, X_OUT, 0.0, BAY, 0.0, FLOOR_T)

    # Anti-roll ridge at the front of the bay: ramps up from the floor so a
    # can can be pushed in from the front, then drops vertically into the bay.
    tris += prism([(0.0, Z_FLOOR), (RIDGE_LEN, Z_FLOOR),
                   (RIDGE_LEN, Z_FLOOR + RIDGE_H)], 'x', -X_IN, X_IN)

    side = []
    # Main wall (full thickness) between the two lap zones
    side += box(X_IN, X_OUT, LAP, BAY, Z_FLOOR, Z_GLASS_BOT)
    # Front of the bay: inner half only, with the snap bump
    side += inner_lap_plate(0.0)
    # Rear of the bay: outer half only, overhanging into the next module
    side += outer_lap_plate(BAY)

    tris += side
    tris += mirror_x(side)
    return tris


# ═══════════════════════════════════════════════════════════════════════
#  Part 2 — shelf clip (print x2)
# ═══════════════════════════════════════════════════════════════════════

def shelf_clip():
    """Wraps the glass front edge and laps onto the front bay's side wall."""
    tris = []

    # Lap plate onto the front bay (female half of the joint)
    tris += outer_lap_plate(0.0)

    # Nose — the part in front of the glass edge, joins rail to flange
    tris += box(CLIP_RISER_X0, CLIP_RISER_X1, -CLIP_NOSE, 0.0,
                Z_FLOOR, Z_GLASS_TOP + CLIP_T)
    tris += box(CLIP_FLANGE_X0, CLIP_RISER_X0, -CLIP_NOSE, 0.0,
                Z_GLASS_BOT, Z_GLASS_TOP + CLIP_T)

    # Flange lying on top of the glass
    tris += box(CLIP_FLANGE_X0, CLIP_RISER_X1, 0.0, CLIP_FLANGE_LEN,
                Z_GLASS_TOP, Z_GLASS_TOP + CLIP_T)

    return tris


# ═══════════════════════════════════════════════════════════════════════
#  Part 3 — rear end stop (print x1)
# ═══════════════════════════════════════════════════════════════════════

def end_stop():
    tris = []

    side = inner_lap_plate(0.0)
    tris += side
    tris += mirror_x(side)

    # Stop wall across the back
    tris += box(-X_OUT, X_OUT, LAP, LAP + STOP_T, 0.0, Z_FLOOR + STOP_H)
    return tris


# ═══════════════════════════════════════════════════════════════════════
#  Assembly (visualisation only)
# ═══════════════════════════════════════════════════════════════════════

def assembly():
    tris = []
    for i in range(N_BAYS):
        tris += translate(bay_module(), dy=i * BAY)

    clip = shelf_clip()
    tris += clip
    tris += mirror_x(clip)

    tris += translate(end_stop(), dy=N_BAYS * BAY)
    return tris


# ═══════════════════════════════════════════════════════════════════════
#  Export helpers
# ═══════════════════════════════════════════════════════════════════════

def save(tris, filename, label, matrix=None, drop_to_zero=True):
    if matrix is not None:
        tris = rotate(tris, matrix)

    m = mesh.Mesh(np.zeros(len(tris), dtype=mesh.Mesh.dtype))
    for i, tri in enumerate(tris):
        for j in range(3):
            m.vectors[i][j] = tri[j]

    if drop_to_zero:
        m.translate([0, 0, -m.z.min()])

    xr = m.x.max() - m.x.min()
    yr = m.y.max() - m.y.min()
    zr = m.z.max() - m.z.min()
    print(f"  {label:<22} {len(tris):>5} tris   "
          f"{xr:6.1f} x {yr:6.1f} x {zr:6.1f} mm  →  {filename}")
    m.save(filename)


def main():
    print("Generating fridge can rack …")
    print(f"  Shelf depth {SHELF_DEPTH:.0f}mm → {N_BAYS} x 330ml cans "
          f"({RACK_LEN:.0f}mm of shelf used)\n")

    save(bay_module(), "fridge_can_rack_bay.stl", "Can bay (x5)")
    save(shelf_clip(), "fridge_can_rack_shelf_clip.stl", "Shelf clip (x2)",
         matrix=ROT_LAY_ON_SIDE)
    save(end_stop(), "fridge_can_rack_end_stop.stl", "End stop (x1)",
         matrix=ROT_LAY_ON_BACK)
    save(assembly(), "fridge_can_rack_assembly.stl", "Assembly (preview)")

    print(f"\n  Assembled rack: {2 * (X_OUT + 1.0):.0f}mm wide, "
          f"{RACK_LEN + CLIP_NOSE:.0f}mm long, "
          f"{Z_GLASS_TOP + CLIP_T:.0f}mm tall")
    print(f"  Needs {Z_GLASS_BOT:.0f}mm of clearance under the shelf")
    print(f"  Set GLASS_T (currently {GLASS_T:.1f}mm) to your shelf thickness")


if __name__ == "__main__":
    main()
