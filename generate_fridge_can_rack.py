"""
Generate STL files for a hanging fridge can rack.

The rack clips onto the front edge of a typical glass fridge shelf and hangs
underneath it, holding a single row of 330ml drink cans standing UPRIGHT.
The row runs front to back into the fridge, so the rack is only one can wide.

A 380mm deep shelf fits FIVE 330ml cans (Ø66.3mm each, 70mm bay pitch).

Printable parts (all fit a 220 x 220mm bed, none need supports):
  fridge_can_rack_bay.stl               x4  — one can bay, 70mm long
  fridge_can_rack_bay_front.stl         x1  — front bay, with retaining lip
  fridge_can_rack_shelf_clip_right.stl  x1  — wraps the glass front edge
  fridge_can_rack_shelf_clip_left.stl   x1  — mirror image of the above
  fridge_can_rack_end_stop.stl          x1  — rear wall

  fridge_can_rack_assembly.stl              — preview of the assembled rack
                                              (visualisation only, DO NOT print)

Every part is exported already rotated into its recommended print
orientation, with Z-min = 0.
"""

import numpy as np
from stl import mesh

# ═══════════════════════════════════════════════════════════════════════
#  Design parameters (millimetres)
# ═══════════════════════════════════════════════════════════════════════

CAN_DIA = 66.3          # 330ml can body diameter
CAN_H = 115.0           # 330ml can height (standing upright)

SHELF_DEPTH = 380.0     # glass shelf depth
GLASS_T = 6.0           # glass shelf thickness — MEASURE YOURS AND EDIT

N_BAYS = 5              # cans in the row
BAY = 70.0              # bay pitch along the fridge depth

W_IN = 72.0             # clear inner width (can diameter + play)
WALL = 3.0              # side wall thickness
X_IN = W_IN / 2         # 36.0 — inner face of side wall
X_OUT = X_IN + WALL     # 39.0 — outer face of side wall

FLOOR_T = 3.0           # floor plate thickness
Z_FLOOR = FLOOR_T                    # 3.0   — cans stand on this
WALL_H = 147.0                       # floor top → glass underside
Z_GLASS_BOT = Z_FLOOR + WALL_H       # 150.0 — glass underside
Z_GLASS_TOP = Z_GLASS_BOT + GLASS_T  # 156.0 — glass top surface

RIDGE_T = 3.0           # floor ridge that stops cans sliding fore/aft
RIDGE_H = 4.0

LIP_H = 20.0            # front retaining lip, above the floor
LIP_T = 3.0

# The side walls are open frames: two horizontal bands joined by posts.
# This saves a lot of filament and still makes a stiff deep beam.
BAND_LOW = (Z_FLOOR, 38.0)
BAND_HIGH = (132.0, Z_GLASS_BOT)
BANDS = [BAND_LOW, BAND_HIGH]
POST_Y0, POST_Y1 = 30.0, 40.0        # extra mid-bay post

LAP = 18.0              # lap-joint overlap length
X_LAP_MID = X_IN + WALL / 2     # 37.5 — split plane of the lapped wall
LAP_GAP = 0.2                   # sliding clearance on the lap joint
X_TAB_IN = X_LAP_MID + LAP_GAP  # 37.7 — inner face of the outer lap plate

# One snap bump per band: (z_low, z_high)
BUMPS = [(14.0, 24.0), (137.0, 145.0)]
BUMP_X1 = X_OUT - 0.1           # 38.9 — bump tip
BUMP_Y0, BUMP_Y1 = 6.0, 14.0    # along the lap
BUMP_RAMP = 3.0                 # lead-in ramp on the insertion side
WIN_Y0, WIN_Y1 = 5.0, 15.0      # matching window in the outer lap plate
WIN_Z_MARGIN = 1.0

CLIP_NOSE = 9.0           # thickness of the wrap in front of the glass edge
CLIP_NOSE_X0 = 20.0       # inner edge of the nose block
CLIP_NOSE_Z0 = 142.0      # above the can's loading height — keeps the mouth clear
CLIP_FLANGE_LEN = 140.0   # how far the clip lies back on top of the glass
CLIP_FLANGE_X0 = 14.0     # inner edge of the top flange
CLIP_T = 3.0

STOP_T = 4.0              # rear wall thickness

# Front-to-back footprint under the shelf: lip → back of the rear lap
RACK_DEPTH = LIP_T + N_BAYS * BAY + LAP


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


# (x, y, z) → (x, -z, y): rolls the part forward so the -Y face is on the bed
ROT_FACE_DOWN = [[1, 0, 0],
                 [0, 0, -1],
                 [0, 1, 0]]

# (x, y, z) → (z, y, -x): puts the +X face on the bed
ROT_ON_RIGHT_FACE = [[0, 0, 1],
                     [0, 1, 0],
                     [-1, 0, 0]]

# (x, y, z) → (-z, y, x): puts the -X face on the bed
ROT_ON_LEFT_FACE = [[0, 0, -1],
                    [0, 1, 0],
                    [1, 0, 0]]


# ═══════════════════════════════════════════════════════════════════════
#  Lap joints — how the modules chain together
# ═══════════════════════════════════════════════════════════════════════

def _bumps_in(bands):
    return [b for b in BUMPS
            if any(z0 <= b[0] and b[1] <= z1 for z0, z1 in bands)]


def inner_lap_plate(y0, bands=BANDS):
    """Inner (male) half of a lapped wall, with snap bumps.

    Occupies y0 … y0+LAP on the +X side. It slides forward (-Y) into the
    matching outer plate, so the bump ramps up from its y0 edge.
    """
    tris = []
    for bz0, bz1 in bands:
        tris += box(X_IN, X_LAP_MID, y0, y0 + LAP, bz0, bz1)

    for pz0, pz1 in _bumps_in(bands):
        tris += prism([(X_LAP_MID, y0 + BUMP_Y0),
                       (BUMP_X1, y0 + BUMP_Y0 + BUMP_RAMP),
                       (X_LAP_MID, y0 + BUMP_Y0 + BUMP_RAMP)],
                      'z', pz0, pz1)
        tris += box(X_LAP_MID, BUMP_X1,
                    y0 + BUMP_Y0 + BUMP_RAMP, y0 + BUMP_Y1, pz0, pz1)
    return tris


def outer_lap_plate(y0, bands=BANDS):
    """Outer (female) half of a lapped wall, pierced by the snap windows.

    Occupies y0 … y0+LAP on the +X side."""
    x0, x1 = X_TAB_IN, X_OUT
    tris = []
    for bz0, bz1 in bands:
        wins = [b for b in BUMPS if bz0 <= b[0] and b[1] <= bz1]
        if not wins:
            tris += box(x0, x1, y0, y0 + LAP, bz0, bz1)
            continue
        pz0, pz1 = wins[0]
        wz0, wz1 = pz0 - WIN_Z_MARGIN, pz1 + WIN_Z_MARGIN
        tris += box(x0, x1, y0, y0 + LAP, bz0, wz0)
        tris += box(x0, x1, y0, y0 + LAP, wz1, bz1)
        tris += box(x0, x1, y0, y0 + WIN_Y0, wz0, wz1)
        tris += box(x0, x1, y0 + WIN_Y1, y0 + LAP, wz0, wz1)
    return tris


# ═══════════════════════════════════════════════════════════════════════
#  Part 1/2 — can bay module (print x4, plus x1 of the front variant)
# ═══════════════════════════════════════════════════════════════════════

def bay_module(front=False):
    """One upright-can bay. `front=True` adds the front retaining lip."""
    y_floor0 = -LIP_T if front else 0.0

    tris = box(-X_OUT, X_OUT, y_floor0, BAY, 0.0, FLOOR_T)

    # Floor ridge — locates the can and stops it sliding front to back
    tris += box(-X_IN, X_IN, 0.0, RIDGE_T, Z_FLOOR, Z_FLOOR + RIDGE_H)

    side = []
    for bz0, bz1 in BANDS:                       # horizontal bands
        side += box(X_IN, X_OUT, LAP, BAY, bz0, bz1)
    side += inner_lap_plate(0.0)                 # front: male half
    side += outer_lap_plate(BAY)                 # rear: female half
    # Vertical posts joining the two bands
    side += box(X_IN, X_OUT, 0.0, LAP, BAND_LOW[1], BAND_HIGH[0])
    side += box(X_IN, X_OUT, POST_Y0, POST_Y1, BAND_LOW[1], BAND_HIGH[0])

    tris += side
    tris += mirror_x(side)

    if front:
        tris += box(-X_OUT, X_OUT, -LIP_T, 0.0, 0.0, Z_FLOOR + LIP_H)

    return tris


# ═══════════════════════════════════════════════════════════════════════
#  Part 3/4 — shelf clip (print one of each hand)
# ═══════════════════════════════════════════════════════════════════════

def shelf_clip():
    """Right-hand clip: wraps the glass front edge, laps onto the front bay.

    The nose sits above the height a can reaches while being loaded, so the
    front of the rack stays open.
    """
    tris = outer_lap_plate(0.0, bands=[BAND_HIGH])

    # Nose — wraps around the front edge of the glass
    tris += box(CLIP_NOSE_X0, X_OUT, -CLIP_NOSE, 0.0,
                CLIP_NOSE_Z0, Z_GLASS_TOP + CLIP_T)

    # Flange lying on top of the glass
    tris += box(CLIP_FLANGE_X0, X_OUT, 0.0, CLIP_FLANGE_LEN,
                Z_GLASS_TOP, Z_GLASS_TOP + CLIP_T)

    return tris


# ═══════════════════════════════════════════════════════════════════════
#  Part 5 — rear end stop
# ═══════════════════════════════════════════════════════════════════════

def end_stop():
    side = inner_lap_plate(0.0)
    tris = side + mirror_x(side)
    # The wall sits just inside the lap zone, clear of the bay's outer plates
    tris += box(-X_TAB_IN, X_TAB_IN, 0.0, STOP_T, 0.0, Z_GLASS_BOT)
    return tris


# ═══════════════════════════════════════════════════════════════════════
#  Assembly (visualisation only)
# ═══════════════════════════════════════════════════════════════════════

def assembly():
    tris = bay_module(front=True)
    for i in range(1, N_BAYS):
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
    print(f"  {label:<26} {len(tris):>5} tris   "
          f"{xr:6.1f} x {yr:6.1f} x {zr:6.1f} mm  →  {filename}")
    m.save(filename)


def main():
    print("Generating fridge can rack (cans standing upright) …")
    print(f"  Shelf depth {SHELF_DEPTH:.0f}mm → {N_BAYS} x 330ml cans "
          f"({RACK_DEPTH:.0f}mm of shelf used)\n")

    save(bay_module(), "fridge_can_rack_bay.stl", "Can bay (x4)")
    save(bay_module(front=True), "fridge_can_rack_bay_front.stl",
         "Front can bay (x1)")
    save(shelf_clip(), "fridge_can_rack_shelf_clip_right.stl",
         "Shelf clip, right (x1)", matrix=ROT_ON_RIGHT_FACE)
    save(mirror_x(shelf_clip()), "fridge_can_rack_shelf_clip_left.stl",
         "Shelf clip, left (x1)", matrix=ROT_ON_LEFT_FACE)
    save(end_stop(), "fridge_can_rack_end_stop.stl", "End stop (x1)",
         matrix=ROT_FACE_DOWN)
    save(assembly(), "fridge_can_rack_assembly.stl", "Assembly (preview)")

    print(f"\n  Assembled rack: {2 * X_OUT:.0f}mm wide, "
          f"{RACK_DEPTH:.0f}mm deep, {Z_GLASS_TOP + CLIP_T:.0f}mm tall")
    print(f"  Needs {Z_GLASS_BOT:.0f}mm of clearance under the shelf "
          f"and {CLIP_T:.0f}mm above it")
    print(f"  Set GLASS_T (currently {GLASS_T:.1f}mm) to your shelf thickness")


if __name__ == "__main__":
    main()
