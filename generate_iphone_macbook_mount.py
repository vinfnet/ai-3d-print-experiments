"""
Generate an STL file of an iPhone 16 Pro (in Apple Silicone Case) mount
that clips onto the top edge of a MacBook Pro 14" screen.

Design constraints:
- iPhone in landscape orientation in the official Apple Silicone Case
- Hooks over top edge of MacBook Pro 14" screen
- Does NOT obstruct the MacBook webcam (with ~30mm privacy cover)
- Does NOT cover any visible/active screen area (front lip stays in bezel)
- Minimal material for fast printing

Key dimensions (mm):
- iPhone 16 Pro + Apple Silicone Case: ~150.5 x 72.5 x 12.5
- MacBook Pro 14" screen panel top edge: ~4.3mm thick
- MacBook bezel at top: ~3.5mm (safe zone for front lip)
- Webcam privacy cover: ~30mm wide, centered
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

    # Build a 2D rounded-rect cross section in XY, then extrude along Z
    # Corner centers
    corners = [
        (x + r,      y + r),       # bottom-left
        (x + wx - r, y + r),       # bottom-right
        (x + wx - r, y + wy - r),  # top-right
        (x + r,      y + wy - r),  # top-left
    ]
    start_angles = [np.pi, 1.5 * np.pi, 0.0, 0.5 * np.pi]

    # Construct the outline points going around the perimeter
    outline = []
    for ci, (cx, cy) in enumerate(corners):
        sa = start_angles[ci]
        for i in range(n_seg + 1):
            a = sa + (np.pi / 2) * i / n_seg
            outline.append((cx + r * np.cos(a), cy + r * np.sin(a)))

    n_pts = len(outline)

    # Bottom and top rings
    z_bot = z
    z_top = z + wz
    bot_ring = [np.array([px, py, z_bot]) for px, py in outline]
    top_ring = [np.array([px, py, z_top]) for px, py in outline]

    # Side walls
    for i in range(n_pts):
        ni = (i + 1) % n_pts
        tris.append([bot_ring[i], bot_ring[ni], top_ring[i]])
        tris.append([bot_ring[ni], top_ring[ni], top_ring[i]])

    # Top face (fan from center)
    cx_mid = x + wx / 2
    cy_mid = y + wy / 2
    top_center = np.array([cx_mid, cy_mid, z_top])
    bot_center = np.array([cx_mid, cy_mid, z_bot])
    for i in range(n_pts):
        ni = (i + 1) % n_pts
        tris.append([top_center, top_ring[i], top_ring[ni]])
        tris.append([bot_center, bot_ring[ni], bot_ring[i]])

    return tris


# ═══════════════════════════════════════════════════════════════════════
#  Mount components
# ═══════════════════════════════════════════════════════════════════════

# --- Overall parameters ---
# iPhone 16 Pro in Apple Silicone Case (landscape)
PHONE_W = 151.0     # width in landscape (longer dimension + tolerance)
PHONE_H = 73.0      # height in landscape (shorter dimension + tolerance)
PHONE_D = 12.8      # depth/thickness with case + tolerance

# MacBook Pro 14" screen top edge
SCREEN_THICK = 4.5   # screen panel thickness (slightly generous for fit)
BEZEL_TOP = 3.5      # bezel height at top of screen (front lip zone)

# Webcam privacy cover zone
WEBCAM_WIDTH = 32.0   # 30mm cover + 2mm margin

# Structural parameters
WALL = 2.0            # wall thickness
LIP_DEPTH = 2.5       # front lip depth (how far it comes down on screen front)
BACK_DEPTH = 14.0     # how far the back hook extends behind the screen
CRADLE_DEPTH = 14.0   # phone cradle depth (holds phone)
CRADLE_LIP = 8.0      # lip height to hold phone from falling forward
CRADLE_BACK = 10.0    # back support height
SUPPORT_WIDTH = 20.0  # width of each support arm
CORNER_R = 2.0        # corner rounding radius


def clip_arm(x_start, arm_width):
    """
    One clip arm that hooks over the MacBook screen top edge.
    The clip has:
    - A back plate that goes behind the screen
    - A top bridge over the screen edge
    - A minimal front lip that stays within the bezel
    
    Coordinate system:
    - X: horizontal (along screen top edge)
    - Y: depth (negative = behind screen, positive = in front)
    - Z: vertical (up from screen top edge)
    
    Screen top edge sits at Y=0 (front face) to Y=-SCREEN_THICK (back face)
    Z=0 is the top of the screen edge.
    """
    tris = []

    # Back plate: behind the screen, extends downward
    # From Y = -SCREEN_THICK to Y = -(SCREEN_THICK + WALL)
    # From Z = -BACK_DEPTH to Z = WALL (above screen top)
    tris += box_triangles(
        x_start, -(SCREEN_THICK + WALL), -BACK_DEPTH,
        arm_width, WALL, BACK_DEPTH + WALL
    )

    # Top bridge: sits on top of the screen edge
    # From Y = -(SCREEN_THICK + WALL) to Y = WALL
    # At Z = 0 to Z = WALL
    tris += box_triangles(
        x_start, -(SCREEN_THICK + WALL), 0,
        arm_width, SCREEN_THICK + 2 * WALL, WALL
    )

    # Front lip: comes down on front of screen, within bezel zone
    # From Y = 0 to Y = WALL
    # From Z = -LIP_DEPTH to Z = WALL
    tris += box_triangles(
        x_start, 0, -LIP_DEPTH,
        arm_width, WALL, LIP_DEPTH + WALL
    )

    return tris


def phone_cradle(x_start, cradle_width):
    """
    Cradle that sits on top of the clip to hold the phone in landscape.
    The cradle is a U-shape: back wall + floor + front lip.
    
    Sits on top of the clip at Z = WALL (top of bridge).
    Phone rests with its back against the back wall, bottom on the floor.
    """
    tris = []

    z_base = WALL  # on top of clip bridge

    # Floor of cradle: phone sits on this
    # Extends from back wall to front lip
    total_depth = WALL + PHONE_D + WALL  # back wall + phone + front wall
    tris += box_triangles(
        x_start, -(SCREEN_THICK / 2 + total_depth / 2), z_base,
        cradle_width, total_depth, WALL
    )

    # Back support wall
    back_y = -(SCREEN_THICK / 2 + total_depth / 2)
    tris += box_triangles(
        x_start, back_y, z_base,
        cradle_width, WALL, WALL + CRADLE_BACK
    )

    # Front lip (lower, just enough to stop phone sliding forward)
    front_y = -(SCREEN_THICK / 2 + total_depth / 2) + total_depth - WALL
    tris += box_triangles(
        x_start, front_y, z_base,
        cradle_width, WALL, WALL + CRADLE_LIP
    )

    return tris


def side_wall(x_pos, is_right=False):
    """
    Side wall at the end of the cradle to prevent phone sliding sideways.
    """
    tris = []
    z_base = WALL
    total_depth = WALL + PHONE_D + WALL
    y_start = -(SCREEN_THICK / 2 + total_depth / 2)

    x = x_pos - WALL if is_right else x_pos

    tris += box_triangles(
        x, y_start, z_base,
        WALL, total_depth, WALL + CRADLE_BACK
    )

    return tris


def angled_brace(x_start, brace_width):
    """
    Triangular brace connecting the clip back plate to the cradle back wall
    for rigidity. Built as a series of thin box slices approximating a wedge.
    """
    tris = []
    z_base = WALL
    total_depth = WALL + PHONE_D + WALL
    back_y = -(SCREEN_THICK / 2 + total_depth / 2)

    # Brace runs from top of cradle back wall down to the back plate
    brace_top_z = z_base + WALL + CRADLE_BACK
    brace_bot_z = z_base
    brace_back_y = -(SCREEN_THICK + WALL)

    n_steps = 8
    for i in range(n_steps):
        t = i / n_steps
        t_next = (i + 1) / n_steps
        # Interpolate from cradle back to clip back
        z0 = brace_top_z - t * (brace_top_z - brace_bot_z)
        z1 = brace_top_z - t_next * (brace_top_z - brace_bot_z)
        y0 = back_y + WALL + t * (brace_back_y - (back_y + WALL))
        y1 = back_y + WALL + t_next * (brace_back_y - (back_y + WALL))

        # Small box segment
        seg_h = z0 - z1
        if seg_h > 0.1:
            tris += box_triangles(
                x_start, min(y0, y1), z1,
                brace_width, WALL, seg_h
            )

    return tris


def main():
    print("Generating iPhone 16 Pro MacBook mount …")
    print(f"  Phone (in case, landscape): {PHONE_W:.1f} × {PHONE_H:.1f} × {PHONE_D:.1f} mm")
    print(f"  Screen thickness: {SCREEN_THICK:.1f} mm")
    print(f"  Webcam clearance: {WEBCAM_WIDTH:.1f} mm")

    all_tris = []

    # The mount is symmetric about X=0. The total phone width is PHONE_W.
    # We need to leave a gap in the center for the webcam.
    # 
    # Layout (top view, looking down):
    #   |--arm--|--cradle--|  [webcam gap]  |--cradle--|--arm--|
    #
    # Two support arms on each side, with cradle sections between them.

    half_phone = PHONE_W / 2
    half_webcam = WEBCAM_WIDTH / 2

    # Each side has:
    # - An outer clip arm at the phone edge
    # - An inner clip arm near the webcam gap
    # - Cradle floor connecting them

    # === LEFT SIDE (negative X) ===
    # Outer arm: from -half_phone to -half_phone + SUPPORT_WIDTH
    left_outer_x = -half_phone
    tris = clip_arm(left_outer_x, SUPPORT_WIDTH)
    all_tris += tris
    print(f"  Left outer clip arm: {len(tris)} tris")

    # Inner arm: from -half_webcam - SUPPORT_WIDTH to -half_webcam
    left_inner_x = -half_webcam - SUPPORT_WIDTH
    tris = clip_arm(left_inner_x, SUPPORT_WIDTH)
    all_tris += tris
    print(f"  Left inner clip arm: {len(tris)} tris")

    # Left cradle: spans from left_outer_x to left_inner_x + SUPPORT_WIDTH
    left_cradle_x = left_outer_x
    left_cradle_w = (left_inner_x + SUPPORT_WIDTH) - left_outer_x
    tris = phone_cradle(left_cradle_x, left_cradle_w)
    all_tris += tris
    print(f"  Left cradle: {len(tris)} tris")

    # Left braces (on each arm)
    tris = angled_brace(left_outer_x + SUPPORT_WIDTH / 2 - WALL / 2, WALL)
    all_tris += tris
    tris2 = angled_brace(left_inner_x + SUPPORT_WIDTH / 2 - WALL / 2, WALL)
    all_tris += tris2
    print(f"  Left braces: {len(tris) + len(tris2)} tris")

    # === RIGHT SIDE (positive X) ===
    right_inner_x = half_webcam
    tris = clip_arm(right_inner_x, SUPPORT_WIDTH)
    all_tris += tris
    print(f"  Right inner clip arm: {len(tris)} tris")

    right_outer_x = half_phone - SUPPORT_WIDTH
    tris = clip_arm(right_outer_x, SUPPORT_WIDTH)
    all_tris += tris
    print(f"  Right outer clip arm: {len(tris)} tris")

    # Right cradle
    right_cradle_x = right_inner_x
    right_cradle_w = (right_outer_x + SUPPORT_WIDTH) - right_inner_x
    tris = phone_cradle(right_cradle_x, right_cradle_w)
    all_tris += tris
    print(f"  Right cradle: {len(tris)} tris")

    # Right braces
    tris = angled_brace(right_inner_x + SUPPORT_WIDTH / 2 - WALL / 2, WALL)
    all_tris += tris
    tris2 = angled_brace(right_outer_x + SUPPORT_WIDTH / 2 - WALL / 2, WALL)
    all_tris += tris2
    print(f"  Right braces: {len(tris) + len(tris2)} tris")

    # === SIDE WALLS (prevent phone sliding left/right) ===
    tris = side_wall(left_outer_x)
    all_tris += tris
    tris2 = side_wall(right_outer_x + SUPPORT_WIDTH, is_right=True)
    all_tris += tris2
    print(f"  Side walls: {len(tris) + len(tris2)} tris")

    # === BUILD MESH ===
    total = len(all_tris)
    print(f"\n  TOTAL: {total} tris")

    m = mesh.Mesh(np.zeros(total, dtype=mesh.Mesh.dtype))
    for i, tri in enumerate(all_tris):
        for j in range(3):
            m.vectors[i][j] = tri[j]

    # Print dimensions
    xr = m.x.max() - m.x.min()
    yr = m.y.max() - m.y.min()
    zr = m.z.max() - m.z.min()
    print(f"  Size: {xr:.1f} × {yr:.1f} × {zr:.1f} mm (W × D × H)")

    # Translate so Z-min = 0 (flat on print bed)
    m.translate([0, 0, -m.z.min()])

    out = "iphone_macbook_mount.stl"
    m.save(out)
    print(f"  ✓ Saved → {out}")

    # Print clearance info
    print(f"\n  Design notes:")
    print(f"    Webcam gap: {WEBCAM_WIDTH:.0f}mm centered (clear of privacy cover)")
    print(f"    Front lip: {LIP_DEPTH:.1f}mm (within {BEZEL_TOP:.1f}mm bezel)")
    print(f"    Phone held in landscape mode")
    print(f"    Fits iPhone 16 Pro in Apple Silicone Case")


if __name__ == "__main__":
    main()
