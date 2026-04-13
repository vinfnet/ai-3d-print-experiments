"""
Generate an STL of a platform adapter for Crank Brothers Egg Beater pedals.
Clips into the Egg Beater like a cleat, provides a flat pedal surface for
normal shoes. Print twice — one for each pedal.

Print orientation (bottom to top — designed for minimal supports):
  1. Platform — ~95×75mm plate with grip ridges (flat on print bed)
  2. Transition body — tapers inward from platform to cleat (no overhangs)
  3. Cleat interface — wing tabs on top (small, easy to print)

Crank Brothers brass cleat dimensions (from real cleat image):
  The brass cleat has two brass wings, one on each side of a black center
  mounting plate (SPD 2-bolt pattern). Each wing has a distinctive peanut/
  figure-8 shape: wider at the front and back tips, narrower in the middle
  where the pedal's spring tines grip the waist.

  The Egg Beater pedal has 4 spring tines in an X pattern. When clipping in,
  the cleat drops onto the spindle and the tines snap around the waist of
  each wing. The wider fore/aft ends prevent the tines from sliding off.

  Key measurements (from real brass cleat):
  - Center channel width: ~10mm (spindle clearance + mounting plate)
  - Each wing: ~8.5mm wide at tips, ~5mm at waist, ~15mm fore-aft
  - Wing height (protrusion): ~3.5mm
  - Total width (outer wing to outer wing): ~27mm
  - The 4 pedal tines sit at about 18mm apart (tine-to-tine across spindle),
    gripping each wing at a radius of about 8-9mm from pedal center
"""

import numpy as np
from stl import mesh


# ═══════════════════════════════════════════════════════════════════════
#  Geometry helpers
# ═══════════════════════════════════════════════════════════════════════

def box_triangles(x, y, z, wx, wy, wz):
    """Axis-aligned box from (x,y,z) to (x+wx, y+wy, z+wz). 12 tris."""
    v = [
        np.array([x,      y,      z]),
        np.array([x + wx, y,      z]),
        np.array([x + wx, y + wy, z]),
        np.array([x,      y + wy, z]),
        np.array([x,      y,      z + wz]),
        np.array([x + wx, y,      z + wz]),
        np.array([x + wx, y + wy, z + wz]),
        np.array([x,      y + wy, z + wz]),
    ]
    faces = [
        (0, 1, 5, 4),  # front  (Y=y)
        (2, 3, 7, 6),  # back   (Y=y+wy)
        (3, 0, 4, 7),  # left   (X=x)
        (1, 2, 6, 5),  # right  (X=x+wx)
        (4, 5, 6, 7),  # top    (Z=z+wz)
        (3, 2, 1, 0),  # bottom (Z=z)
    ]
    tris = []
    for a, b, c, d in faces:
        tris.append([v[a], v[b], v[c]])
        tris.append([v[a], v[c], v[d]])
    return tris


def rounded_box_triangles(x, y, z, wx, wy, wz, radius, n_seg=6):
    """Box with rounded vertical edges (Z-axis). Approximated with facets."""
    if radius <= 0 or radius > min(wx, wy) / 2:
        return box_triangles(x, y, z, wx, wy, wz)

    tris = []
    r = radius

    # 2D rounded-rect cross section in XY, extruded along Z
    corners = [
        (x + r,      y + r),
        (x + wx - r, y + r),
        (x + wx - r, y + wy - r),
        (x + r,      y + wy - r),
    ]
    start_angles = [np.pi, 1.5 * np.pi, 0.0, 0.5 * np.pi]

    outline = []
    for ci, (cx, cy) in enumerate(corners):
        sa = start_angles[ci]
        for i in range(n_seg + 1):
            a = sa + (np.pi / 2) * i / n_seg
            outline.append((cx + r * np.cos(a), cy + r * np.sin(a)))

    n_pts = len(outline)
    z_bot = z
    z_top = z + wz
    bot_ring = [np.array([px, py, z_bot]) for px, py in outline]
    top_ring = [np.array([px, py, z_top]) for px, py in outline]

    # Side walls
    for i in range(n_pts):
        ni = (i + 1) % n_pts
        tris.append([bot_ring[i], bot_ring[ni], top_ring[i]])
        tris.append([bot_ring[ni], top_ring[ni], top_ring[i]])

    # Top & bottom face fans
    cx_mid = x + wx / 2
    cy_mid = y + wy / 2
    top_center = np.array([cx_mid, cy_mid, z_top])
    bot_center = np.array([cx_mid, cy_mid, z_bot])
    for i in range(n_pts):
        ni = (i + 1) % n_pts
        tris.append([top_center, top_ring[i], top_ring[ni]])
        tris.append([bot_center, bot_ring[ni], bot_ring[i]])

    return tris


def peanut_wing_triangles(cx, cy, z_bot, height,
                          tip_rx, tip_ry, waist_rx, length, n_seg=32):
    """Peanut/figure-8 shaped wing: wider at fore/aft tips, narrower waist.
    The shape is built from a parametric outline that varies the X-radius
    along the Y-axis: wide at Y-extremes (tips), narrow at Y=0 (waist).
    Centered at (cx, cy). 'length' is full fore-aft extent (Y-axis).
    tip_rx = half-width at fore/aft tips, waist_rx = half-width at center."""
    tris = []
    z_top = z_bot + height
    half_l = length / 2

    # Generate outline: parametric curve, angle sweeps 0..2pi
    # At angle 0 (front tip), rx = tip_rx; at angle pi/2 (side/waist), rx = waist_rx
    # Use a smooth blend: rx(a) = waist_rx + (tip_rx - waist_rx) * |cos(a)|
    # ry is constant = half_l
    outline_bot = []
    outline_top = []
    for i in range(n_seg):
        a = 2 * np.pi * i / n_seg
        # Smooth varying radius: wider at front/back (cos=+/-1), narrow at sides (cos=0)
        rx = waist_rx + (tip_rx - waist_rx) * abs(np.cos(a))
        px = cx + rx * np.cos(a)
        py = cy + half_l * np.sin(a)
        outline_bot.append(np.array([px, py, z_bot]))
        outline_top.append(np.array([px, py, z_top]))

    bot_center = np.array([cx, cy, z_bot])
    top_center = np.array([cx, cy, z_top])

    for i in range(n_seg):
        ni = (i + 1) % n_seg
        # Side wall
        tris.append([outline_bot[i], outline_bot[ni], outline_top[ni]])
        tris.append([outline_bot[i], outline_top[ni], outline_top[i]])
        # Top cap
        tris.append([top_center, outline_top[i], outline_top[ni]])
        # Bottom cap
        tris.append([bot_center, outline_bot[ni], outline_bot[i]])

    return tris


def elliptical_disc_triangles(cx, cy, z_bot, rx, ry, height, n_seg=24):
    """Elliptical disc (short cylinder with elliptical cross-section).
    Centered at (cx, cy), with semi-axes rx (X) and ry (Y).
    Generates a closed watertight solid with top, bottom, and side faces."""
    tris = []
    # Generate perimeter points
    angles = [2 * np.pi * i / n_seg for i in range(n_seg)]
    z_top = z_bot + height

    bot_ring = [np.array([cx + rx * np.cos(a), cy + ry * np.sin(a), z_bot]) for a in angles]
    top_ring = [np.array([cx + rx * np.cos(a), cy + ry * np.sin(a), z_top]) for a in angles]
    bot_center = np.array([cx, cy, z_bot])
    top_center = np.array([cx, cy, z_top])

    for i in range(n_seg):
        ni = (i + 1) % n_seg
        # Side wall
        tris.append([bot_ring[i], bot_ring[ni], top_ring[ni]])
        tris.append([bot_ring[i], top_ring[ni], top_ring[i]])
        # Top cap
        tris.append([top_center, top_ring[i], top_ring[ni]])
        # Bottom cap
        tris.append([bot_center, bot_ring[ni], bot_ring[i]])

    return tris


def tapered_box_triangles(x_bot, y_bot, wx_bot, wy_bot,
                          x_top, y_top, wx_top, wy_top,
                          z_bot, z_top):
    """Frustum (tapered box) with rectangular cross-sections at bottom and top.
    Bottom rect at z_bot: (x_bot, y_bot) -> (x_bot+wx_bot, y_bot+wy_bot).
    Top rect at z_top:    (x_top, y_top) -> (x_top+wx_top, y_top+wy_top).
    Returns triangles for the 6 faces (2 tris each = 12 tris)."""
    # Bottom corners
    b0 = np.array([x_bot,          y_bot,          z_bot])
    b1 = np.array([x_bot + wx_bot, y_bot,          z_bot])
    b2 = np.array([x_bot + wx_bot, y_bot + wy_bot, z_bot])
    b3 = np.array([x_bot,          y_bot + wy_bot, z_bot])
    # Top corners
    t0 = np.array([x_top,          y_top,          z_top])
    t1 = np.array([x_top + wx_top, y_top,          z_top])
    t2 = np.array([x_top + wx_top, y_top + wy_top, z_top])
    t3 = np.array([x_top,          y_top + wy_top, z_top])

    tris = []
    # Front face (min-Y side)
    tris.append([b0, b1, t1]); tris.append([b0, t1, t0])
    # Back face (max-Y side)
    tris.append([b2, b3, t3]); tris.append([b2, t3, t2])
    # Left face (min-X side)
    tris.append([b3, b0, t0]); tris.append([b3, t0, t3])
    # Right face (max-X side)
    tris.append([b1, b2, t2]); tris.append([b1, t2, t1])
    # Top face
    tris.append([t0, t1, t2]); tris.append([t0, t2, t3])
    # Bottom face
    tris.append([b3, b2, b1]); tris.append([b3, b1, b0])
    return tris


# ═══════════════════════════════════════════════════════════════════════
#  Cleat dimensions — Crank Brothers Egg Beater engagement
# ═══════════════════════════════════════════════════════════════════════

# The Egg Beater pedal has 4 spring-loaded tines forming an X/bowtie shape.
# The cleat drops onto the pedal spindle, and the tines flex outward then
# snap around the waist (narrowest point) of each brass wing.
#
# Engagement geometry (from real brass cleat image + pedal cage):
#   - Two peanut/figure-8 shaped brass wings, one per side of center
#   - Each wing: wider at fore/aft tips, narrow waist where tines grip
#   - Center gap: ~10mm wide for spindle + mounting plate
#   - Pedal tines spring inward and grip at the wing waist
#   - Wing tips prevent tines sliding off: wider than tine grip points
#   - Tine-to-tine gap on pedal: ~18mm across spindle

# Center channel (spindle + mounting plate clearance)
CHANNEL_W    = 10.0    # center channel width

# Each peanut-shaped wing
WING_TIP_RX  = 4.25    # half-width at fore/aft tips (~8.5mm wide at tips)
WING_WAIST_RX = 2.5    # half-width at waist (~5mm wide where tines grip)
WING_LENGTH  = 15.0    # full fore-aft length of each wing
WING_H       = 3.5     # wing height (protrusion above base)

# Derived positions
WING_CX_OFF  = CHANNEL_W / 2 + WING_TIP_RX  # X offset of each wing center
ENGAGE_W     = 2 * (WING_CX_OFF + WING_TIP_RX)  # total wingspan ~27mm

# Cleat base plate (wider than wings for structural connection)
BASE_W       = 34.0    # base plate width
BASE_L       = max(22.0, WING_LENGTH + 4)  # covers wing span + margin
BASE_H       = 4.0     # base plate thickness

# Platform dimensions
PLATFORM_W   = 95.0    # width (left-right under foot)
PLATFORM_L   = 75.0    # length (fore-aft)
PLATFORM_H   = 4.0     # plate thickness
CORNER_R     = 5.0     # rounded corner radius

# Transition zone
TRANS_H      = 6.0     # height of tapered transition from cleat to platform

# Grip ridges
RIDGE_COUNT  = 6
RIDGE_W      = 3.0     # width of each ridge
RIDGE_H      = 1.5     # height above platform surface
RIDGE_L      = 65.0    # length (runs fore-aft, shorter than platform)

# Vertical layout (bottom to top) — platform-down for minimal supports:
#   Z=0                 bottom of platform (on print bed)
#   Z=PLATFORM_H        top of platform / bottom of transition
#   Z=...+TRANS_H        top of transition / bottom of cleat base
#   Z=...+BASE_H         top of cleat base / bottom of wing tabs
#   Z=...+WING_TAB_H     top of wing tabs (topmost point)
# Ridges sit below the platform at Z < 0 (printed on bed surface).

Z_PLAT_BOT   = 0.0
Z_PLAT_TOP   = PLATFORM_H
Z_TRANS_BOT  = Z_PLAT_TOP
Z_TRANS_TOP  = Z_TRANS_BOT + TRANS_H
Z_BASE_BOT   = Z_TRANS_TOP
Z_BASE_TOP   = Z_BASE_BOT + BASE_H
Z_WING_BOT   = Z_BASE_TOP
Z_WING_TOP   = Z_WING_BOT + WING_H

# For transition taper: taper to base plate footprint (not engagement zone)
CLEAT_WIDTH  = BASE_W
CLEAT_LENGTH = BASE_L


# ═══════════════════════════════════════════════════════════════════════
#  Component: Cleat base plate (two blocks flanking center channel)
# ═══════════════════════════════════════════════════════════════════════

def cleat_base():
    """Base plate centered at origin with an open center channel for the
    pedal spindle. Two solid blocks flank the channel, connecting the
    wing pads to the transition body below."""
    tris = []
    half_w = BASE_W / 2
    half_l = BASE_L / 2
    half_ch = CHANNEL_W / 2

    # Left block: from -half_w to -half_ch
    tris += box_triangles(
        x=-half_w, y=-half_l, z=Z_BASE_BOT,
        wx=half_w - half_ch, wy=BASE_L, wz=BASE_H
    )
    # Right block: from +half_ch to +half_w
    tris += box_triangles(
        x=half_ch, y=-half_l, z=Z_BASE_BOT,
        wx=half_w - half_ch, wy=BASE_L, wz=BASE_H
    )
    return tris


# ═══════════════════════════════════════════════════════════════════════
#  Component: Cleat wing tabs (engage Egg Beater tines)
# ═══════════════════════════════════════════════════════════════════════

def cleat_wings():
    """Two peanut/figure-8 shaped wing pads matching the real Crank Brothers
    brass cleat. Each wing is wider at fore/aft tips and narrower at the
    waist where the pedal's spring tines snap in and grip.
    The shape ensures tines can't slide off the wing tips."""
    tris = []

    # Left wing (negative X side)
    tris += peanut_wing_triangles(
        cx=-WING_CX_OFF, cy=0, z_bot=Z_WING_BOT, height=WING_H,
        tip_rx=WING_TIP_RX, tip_ry=WING_LENGTH / 2,
        waist_rx=WING_WAIST_RX, length=WING_LENGTH, n_seg=48
    )
    # Right wing (positive X side)
    tris += peanut_wing_triangles(
        cx=+WING_CX_OFF, cy=0, z_bot=Z_WING_BOT, height=WING_H,
        tip_rx=WING_TIP_RX, tip_ry=WING_LENGTH / 2,
        waist_rx=WING_WAIST_RX, length=WING_LENGTH, n_seg=48
    )

    return tris


# ═══════════════════════════════════════════════════════════════════════
#  Component: Transition body (tapered from cleat to platform footprint)
# ═══════════════════════════════════════════════════════════════════════

def transition_body():
    """Tapered frustum from platform footprint (bottom) to cleat footprint (top).
    Tapers inward going up — zero overhangs, no supports needed.
    Uses multiple tapered-box slices for a smooth taper."""
    tris = []
    n_slices = 8

    half_cw = CLEAT_WIDTH / 2
    half_cl = CLEAT_LENGTH / 2
    half_pw = PLATFORM_W / 2
    half_pl = PLATFORM_L / 2

    for i in range(n_slices):
        t0 = i / n_slices
        t1 = (i + 1) / n_slices
        z0 = Z_TRANS_BOT + t0 * TRANS_H
        z1 = Z_TRANS_BOT + t1 * TRANS_H

        # Smooth easing (cubic ease-in-out) for a natural taper
        def ease(t):
            return t * t * (3 - 2 * t)

        e0 = ease(t0)
        e1 = ease(t1)

        # Taper from platform (large) at bottom to cleat (small) at top
        hw0 = half_pw + (half_cw - half_pw) * e0
        hl0 = half_pl + (half_cl - half_pl) * e0
        hw1 = half_pw + (half_cw - half_pw) * e1
        hl1 = half_pl + (half_cl - half_pl) * e1

        tris += tapered_box_triangles(
            x_bot=-hw0, y_bot=-hl0, wx_bot=2 * hw0, wy_bot=2 * hl0,
            x_top=-hw1, y_top=-hl1, wx_top=2 * hw1, wy_top=2 * hl1,
            z_bot=z0, z_top=z1
        )

    return tris


# ═══════════════════════════════════════════════════════════════════════
#  Component: Platform plate (with rounded corners)
# ═══════════════════════════════════════════════════════════════════════

def platform_top():
    """Flat platform plate centered at origin in XY, with rounded corners.
    Sits at the bottom of the model (on print bed)."""
    half_w = PLATFORM_W / 2
    half_l = PLATFORM_L / 2
    return rounded_box_triangles(
        x=-half_w, y=-half_l, z=Z_PLAT_BOT,
        wx=PLATFORM_W, wy=PLATFORM_L, wz=PLATFORM_H,
        radius=CORNER_R, n_seg=8
    )


# ═══════════════════════════════════════════════════════════════════════
#  Component: Grip ridges on platform top surface
# ═══════════════════════════════════════════════════════════════════════

def grip_ridges():
    """Parallel raised ridges on the platform shoe-contact surface.
    In this orientation the shoe-contact surface faces down (Z < 0),
    so ridges extend below the platform into negative Z.
    They print directly on the bed for a clean finish."""
    tris = []
    half_rl = RIDGE_L / 2

    # Evenly space ridges across platform width
    total_span = PLATFORM_W - 2 * CORNER_R - RIDGE_W
    spacing = total_span / (RIDGE_COUNT - 1)
    start_x = -total_span / 2

    for i in range(RIDGE_COUNT):
        rx = start_x + i * spacing - RIDGE_W / 2
        tris += rounded_box_triangles(
            x=rx, y=-half_rl, z=Z_PLAT_BOT - RIDGE_H,
            wx=RIDGE_W, wy=RIDGE_L, wz=RIDGE_H,
            radius=min(RIDGE_W, RIDGE_H) / 2, n_seg=4
        )

    return tris


# ═══════════════════════════════════════════════════════════════════════
#  Component: Reinforcement ribs (connect cleat to platform underside)
# ═══════════════════════════════════════════════════════════════════════

def reinforcement_ribs():
    """Diagonal ribs inside the transition zone connecting the platform
    to the cleat, adding structural rigidity under pedaling loads.
    Ribs go from platform corners (bottom) to cleat corners (top)."""
    tris = []
    rib_thick = 2.5

    half_cw = CLEAT_WIDTH / 2
    half_pw = PLATFORM_W / 2
    half_cl = CLEAT_LENGTH / 2

    rib_z_bot = Z_TRANS_BOT
    rib_z_top = Z_TRANS_TOP

    # Front-left rib: platform corner (bottom) to cleat corner (top)
    tris += tapered_box_triangles(
        x_bot=-half_pw + CORNER_R, y_bot=-half_cl,
        wx_bot=rib_thick, wy_bot=rib_thick,
        x_top=-half_cw, y_top=-half_cl,
        wx_top=rib_thick, wy_top=rib_thick,
        z_bot=rib_z_bot, z_top=rib_z_top
    )
    # Front-right rib
    tris += tapered_box_triangles(
        x_bot=half_pw - CORNER_R - rib_thick, y_bot=-half_cl,
        wx_bot=rib_thick, wy_bot=rib_thick,
        x_top=half_cw - rib_thick, y_top=-half_cl,
        wx_top=rib_thick, wy_top=rib_thick,
        z_bot=rib_z_bot, z_top=rib_z_top
    )
    # Back-left rib
    tris += tapered_box_triangles(
        x_bot=-half_pw + CORNER_R, y_bot=half_cl - rib_thick,
        wx_bot=rib_thick, wy_bot=rib_thick,
        x_top=-half_cw, y_top=half_cl - rib_thick,
        wx_top=rib_thick, wy_top=rib_thick,
        z_bot=rib_z_bot, z_top=rib_z_top
    )
    # Back-right rib
    tris += tapered_box_triangles(
        x_bot=half_pw - CORNER_R - rib_thick, y_bot=half_cl - rib_thick,
        wx_bot=rib_thick, wy_bot=rib_thick,
        x_top=half_cw - rib_thick, y_top=half_cl - rib_thick,
        wx_top=rib_thick, wy_top=rib_thick,
        z_bot=rib_z_bot, z_top=rib_z_top
    )

    return tris


# ═══════════════════════════════════════════════════════════════════════
#  Assemble & export
# ═══════════════════════════════════════════════════════════════════════

def main():
    print("Generating Egg Beater pedal platform adapter ...")
    print(f"  Cleat: {ENGAGE_W:.0f}mm wingspan, {CHANNEL_W:.0f}mm channel, "
          f"wings {2*WING_TIP_RX:.0f}mm tip / {2*WING_WAIST_RX:.0f}mm waist x {WING_LENGTH:.0f}mm")

    all_tris = []

    base = cleat_base()
    all_tris += base
    print(f"  Cleat base     : {len(base):>5} tris")

    wings = cleat_wings()
    all_tris += wings
    print(f"  Cleat wings    : {len(wings):>5} tris")

    trans = transition_body()
    all_tris += trans
    print(f"  Transition body: {len(trans):>5} tris")

    ribs = reinforcement_ribs()
    all_tris += ribs
    print(f"  Reinforce ribs : {len(ribs):>5} tris")

    plat = platform_top()
    all_tris += plat
    print(f"  Platform plate : {len(plat):>5} tris")

    ridges = grip_ridges()
    all_tris += ridges
    print(f"  Grip ridges    : {len(ridges):>5} tris")

    total = len(all_tris)
    print(f"  TOTAL          : {total:>5} tris")

    # Build mesh
    m = mesh.Mesh(np.zeros(total, dtype=mesh.Mesh.dtype))
    for i, tri in enumerate(all_tris):
        for j in range(3):
            m.vectors[i][j] = tri[j]

    # Print dimensions
    xr = m.x.max() - m.x.min()
    yr = m.y.max() - m.y.min()
    zr = m.z.max() - m.z.min()
    print(f"\n  Size: {xr:.1f} x {yr:.1f} x {zr:.1f} mm")
    print(f"  (width x depth x height)")

    # Translate Z-min to 0 (flat on print bed)
    m.translate([0, 0, -m.z.min()])

    out = "eggbeater_adapter.stl"
    m.save(out)
    print(f"\n  Saved -> {out}")
    print(f"    Print this file TWICE -- one adapter for each pedal.")
    print(f"    Recommended material: PETG or Nylon (PLA may be brittle under load).")
    print(f"    You may need to lightly sand the cleat interface for a precise fit.")


if __name__ == "__main__":
    main()
