"""
Generate an STL of a cloud with:
- Microsoft logo embossed on the front
- A padlock through the cloud
- 3D text 'Azure Confidential Computing' below the logo
"""

import numpy as np
from stl import mesh
import math


# ═══════════════════════════════════════════════════════════════════════
#  Helpers
# ═══════════════════════════════════════════════════════════════════════

def sphere_triangles(cx, cy, cz, r, n_lat=20, n_lon=24, half=False):
    """Generate triangles for a sphere (or hemisphere if half=True).
    Sphere centered at (cx, cy, cz) with radius r."""
    tris = []
    lat_end = n_lat // 2 if half else n_lat

    for i in range(lat_end):
        theta1 = np.pi * i / n_lat
        theta2 = np.pi * (i + 1) / n_lat
        for j in range(n_lon):
            phi1 = 2 * np.pi * j / n_lon
            phi2 = 2 * np.pi * (j + 1) / n_lon

            # Four corners of the quad on the sphere
            def sp(th, ph):
                return np.array([
                    cx + r * np.sin(th) * np.cos(ph),
                    cy + r * np.sin(th) * np.sin(ph),
                    cz + r * np.cos(th)
                ])

            p1 = sp(theta1, phi1)
            p2 = sp(theta1, phi2)
            p3 = sp(theta2, phi1)
            p4 = sp(theta2, phi2)

            # Two triangles per quad
            if i > 0:
                tris.append([p1, p2, p3])
            if i < lat_end - 1:
                tris.append([p2, p4, p3])

    return tris


def box_triangles(x, y, z, wx, wy, wz):
    """Axis-aligned box from (x,y,z) to (x+wx, y+wy, z+wz). 12 tris."""
    # 8 vertices
    v = [
        np.array([x,      y,      z]),       # 0: front-bottom-left
        np.array([x + wx, y,      z]),       # 1: front-bottom-right
        np.array([x + wx, y + wy, z]),       # 2: back-bottom-right
        np.array([x,      y + wy, z]),       # 3: back-bottom-left
        np.array([x,      y,      z + wz]),  # 4: front-top-left
        np.array([x + wx, y,      z + wz]),  # 5: front-top-right
        np.array([x + wx, y + wy, z + wz]),  # 6: back-top-right
        np.array([x,      y + wy, z + wz]),  # 7: back-top-left
    ]
    # 6 faces, 2 tris each, outward normals
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


# ═══════════════════════════════════════════════════════════════════════
#  Cloud shape — union of overlapping spheres
# ═══════════════════════════════════════════════════════════════════════

def cloud_shape():
    """Generate a puffy cloud from multiple overlapping spheres.
    Cloud is centered roughly at origin, front face towards -Y."""
    tris = []

    # Sphere positions and radii — arranged to form a cloud silhouette
    # (cx, cy, cz, radius)
    # Main body (wide, flat-ish cluster)
    spheres = [
        # Central large puffs
        (  0,  0,  0, 28),
        ( 22,  0,  5, 24),
        (-22,  0,  3, 25),
        ( 10,  0, 16, 22),
        (-12,  0, 14, 20),
        (  0,  0, 22, 18),

        # Side puffs
        ( 40,  0, -2, 20),
        (-40,  0, -4, 18),
        ( 50,  0, -8, 14),
        (-50,  0, -6, 13),

        # Top puffs
        ( 15,  0, 28, 14),
        ( -8,  0, 30, 12),
        ( 28,  0, 18, 16),
        (-28,  0, 16, 15),

        # Depth puffs (give it thickness)
        (  0, 12,  0, 22),
        ( 20, 10,  4, 18),
        (-18, 10,  2, 18),
        (  0, -8,  0, 20),
        ( 15, -6,  5, 16),
        (-15, -6,  3, 16),

        # Bottom flattening (smaller spheres to fill the base)
        ( 10,  0, -12, 18),
        (-10,  0, -14, 16),
        ( 30,  0, -10, 14),
        (-30,  0, -12, 13),
        (  0,  0, -10, 16),
    ]

    for cx, cy, cz, r in spheres:
        tris += sphere_triangles(cx, cy, cz, r, n_lat=18, n_lon=22)

    return tris


# ═══════════════════════════════════════════════════════════════════════
#  Microsoft logo — 4 raised squares on the front of the cloud
# ═══════════════════════════════════════════════════════════════════════

def microsoft_logo(center_x=0, center_z=5, front_y=-28.0):
    """
    Microsoft logo: 2×2 grid of squares with a gap.
    Embossed on the front face of the cloud (protruding in -Y direction).
    """
    tris = []

    square_size = 10.0    # each square is 10×10 mm
    gap = 2.0             # gap between squares
    depth = 3.0           # how far the logo protrudes

    # Total grid is (2*square_size + gap) wide and tall
    total = 2 * square_size + gap
    half = total / 2

    # The four squares, starting from top-left
    # Grid positions: (col, row) where (0,0)=top-left
    for row in range(2):
        for col in range(2):
            sx = center_x - half + col * (square_size + gap)
            sz = center_z + half - (row + 1) * square_size - row * gap
            sy = front_y - depth  # protrude outward from cloud surface

            tris += box_triangles(sx, sy, sz, square_size, depth, square_size)

    # Add a thin backplate behind the logo to connect it to the cloud
    plate_margin = 2.0
    plate_x = center_x - half - plate_margin
    plate_z = center_z - half - plate_margin
    plate_w = total + 2 * plate_margin
    plate_h = total + 2 * plate_margin
    plate_depth = 2.0

    tris += box_triangles(plate_x, front_y - plate_depth, plate_z,
                          plate_w, plate_depth + 1.0, plate_h)

    return tris


# ═══════════════════════════════════════════════════════════════════════
#  Padlock — shackle arch + rectangular body, going through the cloud
# ═══════════════════════════════════════════════════════════════════════

def torus_segment(cx, cy, cz, R, r, angle_start, angle_end,
                  n_arc=30, n_tube=14, axis='z'):
    """Partial torus (arc of a tube). R=major radius, r=tube radius.
    Arc in the XZ plane by default."""
    tris = []
    rings = []
    for i in range(n_arc + 1):
        a = angle_start + (angle_end - angle_start) * i / n_arc
        # Center of tube cross-section on the arc
        if axis == 'z':  # arc in XZ plane
            arc_cx = cx + R * np.cos(a)
            arc_cy = cy
            arc_cz = cz + R * np.sin(a)
            # tangent direction
            tx = -np.sin(a)
            tz = np.cos(a)
            # radial outward from torus center
            rx = np.cos(a)
            rz = np.sin(a)
            # cross-section directions: radial and Y
            ring = []
            for j in range(n_tube):
                b = 2 * np.pi * j / n_tube
                px = arc_cx + r * np.cos(b) * rx
                py = arc_cy + r * np.sin(b)
                pz = arc_cz + r * np.cos(b) * rz
                ring.append(np.array([px, py, pz]))
            rings.append(ring)

    # Stitch rings
    for i in range(len(rings) - 1):
        for j in range(n_tube):
            jn = (j + 1) % n_tube
            tris += [[rings[i][j], rings[i][jn], rings[i+1][j]],
                     [rings[i][jn], rings[i+1][jn], rings[i+1][j]]]

    # Cap ends
    for end in [0, -1]:
        c = np.mean(rings[end], axis=0)
        for j in range(n_tube):
            jn = (j + 1) % n_tube
            if end == 0:
                tris.append([c, rings[end][jn], rings[end][j]])
            else:
                tris.append([c, rings[end][j], rings[end][jn]])
    return tris


def cylinder_triangles(p1, p2, radius, n_sides=16):
    """Solid cylinder between two 3D points."""
    d = np.array(p2, dtype=float) - np.array(p1, dtype=float)
    length = np.linalg.norm(d)
    if length < 1e-6:
        return []  # degenerate — skip
    d = d / length

    if abs(d[1]) < 0.9:
        ref = np.array([0, 1.0, 0])
    else:
        ref = np.array([1.0, 0, 0])
    r_vec = np.cross(d, ref)
    r_vec = r_vec / np.linalg.norm(r_vec)
    u_vec = np.cross(r_vec, d)

    ring1, ring2 = [], []
    for j in range(n_sides):
        a = 2 * np.pi * j / n_sides
        offset = r_vec * np.cos(a) * radius + u_vec * np.sin(a) * radius
        ring1.append(np.array(p1) + offset)
        ring2.append(np.array(p2) + offset)

    tris = []
    for j in range(n_sides):
        jn = (j + 1) % n_sides
        tris += [[ring1[j], ring1[jn], ring2[j]],
                 [ring1[jn], ring2[jn], ring2[j]]]
    # Caps
    c1, c2 = np.array(p1, dtype=float), np.array(p2, dtype=float)
    for j in range(n_sides):
        jn = (j + 1) % n_sides
        tris.append([c1, ring1[jn], ring1[j]])
        tris.append([c2, ring2[j], ring2[jn]])
    return tris


def rotate_tris(tris, angle_deg, axis='y', pivot=None):
    """Rotate all triangle vertices around an axis through pivot."""
    a = np.radians(angle_deg)
    if axis == 'y':   # rotate in XZ plane
        R = np.array([[np.cos(a), 0, np.sin(a)],
                      [0, 1, 0],
                      [-np.sin(a), 0, np.cos(a)]])
    elif axis == 'z':  # rotate in XY plane
        R = np.array([[np.cos(a), -np.sin(a), 0],
                      [np.sin(a),  np.cos(a), 0],
                      [0, 0, 1]])
    else:  # x
        R = np.array([[1, 0, 0],
                      [0, np.cos(a), -np.sin(a)],
                      [0, np.sin(a),  np.cos(a)]])
    if pivot is None:
        pivot = np.array([0.0, 0.0, 0.0])
    else:
        pivot = np.array(pivot, dtype=float)

    out = []
    for tri in tris:
        out.append([R @ (np.array(v) - pivot) + pivot for v in tri])
    return out


def translate_tris(tris, offset):
    """Translate all triangle vertices by offset [dx, dy, dz]."""
    o = np.array(offset, dtype=float)
    return [[np.array(v) + o for v in tri] for tri in tris]


def padlock():
    """Larger, more prominent padlock built at origin, meant to be
    repositioned and rotated by the caller."""
    tris = []
    cx, cy, cz = 0.0, 0.0, 0.0

    # ── Lock body (bigger) ──
    body_w = 32.0
    body_d = 16.0
    body_h = 26.0
    body_x = cx - body_w / 2
    body_y = cy - body_d / 2
    body_z = cz

    tris += box_triangles(body_x, body_y, body_z, body_w, body_d, body_h)

    # Rounded top of body - add a row of small spheres
    for sx in np.linspace(-body_w/2 + 4, body_w/2 - 4, 5):
        tris += sphere_triangles(cx + sx, cy, body_z + body_h, 5.0,
                                 n_lat=10, n_lon=12)

    # Keyhole — cylinder on front face
    kh_y = cy - body_d / 2 - 2.0
    kh_z = body_z + body_h * 0.40
    tris += cylinder_triangles(
        [cx, kh_y, kh_z],
        [cx, kh_y - 3.0, kh_z],
        3.5, n_sides=14
    )
    # Keyhole slot
    tris += box_triangles(cx - 1.5, kh_y - 3.0, kh_z - 6.0,
                          3.0, 3.0, 6.0)

    # ── Shackle (U-shape arch, thicker) ──
    shackle_r = 4.0
    arch_R = 12.0
    arch_cz = body_z + body_h

    tris += torus_segment(
        cx, cy, arch_cz,
        R=arch_R, r=shackle_r,
        angle_start=0, angle_end=np.pi,
        n_arc=24, n_tube=14
    )

    # Two vertical legs
    leg_left_x = cx - arch_R
    leg_right_x = cx + arch_R
    leg_bottom_z = body_z + 4

    tris += cylinder_triangles(
        [leg_left_x, cy, leg_bottom_z],
        [leg_left_x, cy, arch_cz],
        shackle_r, n_sides=14
    )
    tris += cylinder_triangles(
        [leg_right_x, cy, leg_bottom_z],
        [leg_right_x, cy, arch_cz],
        shackle_r, n_sides=14
    )

    return tris


# ═══════════════════════════════════════════════════════════════════════
#  3D Block text — stroke-based letter rendering
# ═══════════════════════════════════════════════════════════════════════

def stroke_letter(segments, ox, oz, front_y, scale, depth, thickness):
    """Render a letter from line segments as extruded rectangular bars.
    Each segment is (x1, z1, x2, z2) in a 0-1 unit cell."""
    tris = []
    for x1, z1, x2, z2 in segments:
        # Convert to world coords
        wx1 = ox + x1 * scale
        wz1 = oz + z1 * scale
        wx2 = ox + x2 * scale
        wz2 = oz + z2 * scale

        dx = wx2 - wx1
        dz = wz2 - wz1
        seg_len = math.sqrt(dx * dx + dz * dz)
        if seg_len < 0.01:
            continue

        # Perpendicular for thickness
        half_t = thickness / 2
        nx = -dz / seg_len * half_t
        nz = dx / seg_len * half_t

        # 4 corners of the front face
        fl = np.array([wx1 - nx, front_y, wz1 - nz])
        fr = np.array([wx1 + nx, front_y, wz1 + nz])
        bl = np.array([wx2 - nx, front_y, wz2 - nz])
        br = np.array([wx2 + nx, front_y, wz2 + nz])

        # Extrude in -Y (outward from cloud)
        fl2 = fl + np.array([0, -depth, 0])
        fr2 = fr + np.array([0, -depth, 0])
        bl2 = bl + np.array([0, -depth, 0])
        br2 = br + np.array([0, -depth, 0])

        verts = [fl, fr, br, bl, fl2, fr2, br2, bl2]
        faces = [
            (0, 1, 2, 3),  # back (Y=front_y)
            (7, 6, 5, 4),  # front (Y=front_y-depth)
            (0, 3, 7, 4),  # left
            (2, 1, 5, 6),  # right
            (3, 2, 6, 7),  # top
            (0, 4, 5, 1),  # bottom
        ]
        for a, b, c, d in faces:
            tris.append([verts[a], verts[b], verts[c]])
            tris.append([verts[a], verts[c], verts[d]])

    return tris


# Simple stroke font — each letter defined as line segments in a 0-1 cell
# Format: list of (x1, z1, x2, z2) where z=0 is bottom, z=1 is top
STROKE_FONT = {
    'A': [(0,0, 0.5,1), (0.5,1, 1,0), (0.15,0.4, 0.85,0.4)],
    'B': [(0,0, 0,1), (0,1, 0.7,1), (0.7,1, 0.8,0.85), (0.8,0.85, 0.7,0.7),
          (0.7,0.7, 0.8,0.55), (0.8,0.55, 0.7,0.5), (0,0.5, 0.7,0.5),
          (0.7,0.5, 0.8,0.35), (0.8,0.35, 0.8,0.15), (0.8,0.15, 0.7,0),
          (0.7,0, 0,0)],
    'C': [(0.85,0.15, 0.5,0), (0.5,0, 0.15,0.15), (0.15,0.15, 0,0.4),
          (0,0.4, 0,0.6), (0,0.6, 0.15,0.85), (0.15,0.85, 0.5,1),
          (0.5,1, 0.85,0.85)],
    'D': [(0,0, 0,1), (0,1, 0.6,1), (0.6,1, 0.9,0.7), (0.9,0.7, 0.9,0.3),
          (0.9,0.3, 0.6,0), (0.6,0, 0,0)],
    'E': [(0,0, 0,1), (0,1, 0.8,1), (0,0.5, 0.6,0.5), (0,0, 0.8,0)],
    'F': [(0,0, 0,1), (0,1, 0.8,1), (0,0.5, 0.6,0.5)],
    'G': [(0.85,0.85, 0.5,1), (0.5,1, 0.15,0.85), (0.15,0.85, 0,0.6),
          (0,0.6, 0,0.4), (0,0.4, 0.15,0.15), (0.15,0.15, 0.5,0),
          (0.5,0, 0.85,0.15), (0.85,0.15, 0.85,0.5), (0.85,0.5, 0.5,0.5)],
    'H': [(0,0, 0,1), (1,0, 1,1), (0,0.5, 1,0.5)],
    'I': [(0.2,0, 0.8,0), (0.5,0, 0.5,1), (0.2,1, 0.8,1)],
    'K': [(0,0, 0,1), (0,0.5, 0.8,1), (0,0.5, 0.8,0)],
    'L': [(0,1, 0,0), (0,0, 0.8,0)],
    'M': [(0,0, 0,1), (0,1, 0.5,0.5), (0.5,0.5, 1,1), (1,1, 1,0)],
    'N': [(0,0, 0,1), (0,1, 1,0), (1,0, 1,1)],
    'O': [(0.5,0, 0.15,0.15), (0.15,0.15, 0,0.4), (0,0.4, 0,0.6),
          (0,0.6, 0.15,0.85), (0.15,0.85, 0.5,1), (0.5,1, 0.85,0.85),
          (0.85,0.85, 1,0.6), (1,0.6, 1,0.4), (1,0.4, 0.85,0.15),
          (0.85,0.15, 0.5,0)],
    'P': [(0,0, 0,1), (0,1, 0.7,1), (0.7,1, 0.85,0.85), (0.85,0.85, 0.85,0.65),
          (0.85,0.65, 0.7,0.5), (0.7,0.5, 0,0.5)],
    'R': [(0,0, 0,1), (0,1, 0.7,1), (0.7,1, 0.85,0.85), (0.85,0.85, 0.85,0.65),
          (0.85,0.65, 0.7,0.5), (0.7,0.5, 0,0.5), (0.4,0.5, 0.85,0)],
    'S': [(0.85,0.85, 0.5,1), (0.5,1, 0.15,0.85), (0.15,0.85, 0.15,0.65),
          (0.15,0.65, 0.5,0.5), (0.5,0.5, 0.85,0.35), (0.85,0.35, 0.85,0.15),
          (0.85,0.15, 0.5,0), (0.5,0, 0.15,0.15)],
    'T': [(0,1, 1,1), (0.5,1, 0.5,0)],
    'U': [(0,1, 0,0.2), (0,0.2, 0.2,0), (0.2,0, 0.8,0), (0.8,0, 1,0.2),
          (1,0.2, 1,1)],
    'V': [(0,1, 0.5,0), (0.5,0, 1,1)],
    'W': [(0,1, 0.25,0), (0.25,0, 0.5,0.6), (0.5,0.6, 0.75,0), (0.75,0, 1,1)],
    'X': [(0,0, 1,1), (0,1, 1,0)],
    'Y': [(0,1, 0.5,0.5), (1,1, 0.5,0.5), (0.5,0.5, 0.5,0)],
    'Z': [(0,1, 1,1), (1,1, 0,0), (0,0, 1,0)],
    ' ': [],
}


def text_3d(text, center_x, center_z, front_y, char_height=7.0, depth=2.5):
    """Render a string as 3D extruded block letters."""
    tris = []
    text = text.upper()
    char_width = char_height * 0.65
    spacing = char_height * 0.18
    thickness = char_height * 0.14  # stroke thickness

    total_w = len(text) * char_width + (len(text) - 1) * spacing
    start_x = center_x - total_w / 2

    for idx, ch in enumerate(text):
        segs = STROKE_FONT.get(ch, [])
        ox = start_x + idx * (char_width + spacing)
        oz = center_z
        tris += stroke_letter(segs, ox, oz, front_y, char_height, depth, thickness)

    return tris


# ═══════════════════════════════════════════════════════════════════════
#  Flat base for printability
# ═══════════════════════════════════════════════════════════════════════

def flat_base(width=120, depth=40, thickness=3, z_bottom=-30):
    """A flat slab at the bottom of the cloud so it sits on the print bed."""
    x = -width / 2
    y = -depth / 2
    return box_triangles(x, y, z_bottom, width, depth, thickness)


def support_pillars(base_z=-44, cloud_bottom_z=-28, nameplate_cz=-32,
                    nameplate_top_z=-23, nameplate_bot_z=-41,
                    front_y=-28.0):
    """Structural supports:
    - Vertical pillars from base up into cloud body
    - Angled brackets from cloud underside to nameplate back
    """
    tris = []
    pillar_r = 3.5  # radius of support pillars

    # ── Main vertical pillars: base → cloud ──
    # Three pillars spread across the width, going from base
    # up into the cloud body for solid connection
    pillar_positions = [
        (-35, 0),   # left
        (  0, 0),   # center
        ( 35, 0),   # right
    ]
    for px, py in pillar_positions:
        # Pillar from base top surface up into cloud
        z_bot = base_z + 3  # top of base slab
        z_top = cloud_bottom_z + 8  # penetrate into cloud
        tris += cylinder_triangles(
            [px, py, z_bot],
            [px, py, z_top],
            pillar_r, n_sides=14
        )
        # Flared base (wider foot for adhesion)
        tris += cylinder_triangles(
            [px, py, z_bot],
            [px, py, z_bot + 3],
            pillar_r * 1.6, n_sides=14
        )
        # Flared top where it meets cloud
        tris += cylinder_triangles(
            [px, py, z_top - 3],
            [px, py, z_top],
            pillar_r * 1.4, n_sides=14
        )

    # ── Nameplate brackets: cloud underside → nameplate back ──
    # Two L-shaped brackets on left and right connecting
    # the cloud bottom to the back of the nameplate
    bracket_r = 2.5
    for side_x in [-40, 40]:
        # Vertical section: from nameplate top to cloud bottom
        vert_bot = nameplate_top_z
        vert_top = cloud_bottom_z + 5
        tris += cylinder_triangles(
            [side_x, front_y + 6, vert_bot],
            [side_x, front_y + 6, vert_top],
            bracket_r, n_sides=12
        )
        # Horizontal section: from vertical pillar to nameplate
        # (connects at the nameplate's Z center)
        tris += cylinder_triangles(
            [side_x, front_y + 6, nameplate_cz],
            [side_x, front_y, nameplate_cz],
            bracket_r, n_sides=12
        )
        # Small gusset / fillet at the L-joint (reinforcing block)
        gusset_size = 5.0
        tris += box_triangles(
            side_x - gusset_size / 2,
            front_y,
            nameplate_cz - gusset_size / 2,
            gusset_size, 8.0, gusset_size
        )

    # ── Center back strut: vertical bar behind nameplate ──
    # Connects base directly to nameplate for rigidity
    tris += box_triangles(
        -3, front_y + 2, base_z + 3,
        6, 8, nameplate_bot_z - (base_z + 3)
    )

    return tris


def text_nameplate(text_line1, text_line2,
                   plate_cx=0, plate_cz=-32, front_y=-28.0,
                   plate_w=110, plate_h=18, plate_d=3.0):
    """Flat plate with two lines of 3D text raised on the front surface."""
    tris = []

    # Plate
    tris += box_triangles(plate_cx - plate_w / 2,
                          front_y - plate_d,
                          plate_cz - plate_h / 2,
                          plate_w, plate_d, plate_h)

    # Slight bevel / frame around plate
    bevel = 1.5
    tris += box_triangles(plate_cx - plate_w / 2 - bevel,
                          front_y - plate_d - 0.5,
                          plate_cz - plate_h / 2 - bevel,
                          plate_w + 2 * bevel, 0.5, plate_h + 2 * bevel)

    # Text on the plate front
    text_y = front_y - plate_d - 0.5  # on front of plate
    tris += text_3d(text_line1,
                    center_x=plate_cx,
                    center_z=plate_cz + 2.5,
                    front_y=text_y,
                    char_height=4.5, depth=2.0)
    tris += text_3d(text_line2,
                    center_x=plate_cx,
                    center_z=plate_cz - 4.0,
                    front_y=text_y,
                    char_height=4.5, depth=2.0)
    return tris


# ═══════════════════════════════════════════════════════════════════════
#  Assemble & export
# ═══════════════════════════════════════════════════════════════════════

def main():
    print("Generating cloud + padlock + MS logo + nameplate …")

    all_tris = []

    cloud = cloud_shape()
    all_tris += cloud
    print(f"  Cloud      : {len(cloud):>6} tris")

    logo = microsoft_logo(center_x=0, center_z=5, front_y=-28.0)
    all_tris += logo
    print(f"  MS logo    : {len(logo):>6} tris")

    # Padlock — build at origin then move to right side and tilt
    lock = padlock()
    # Tilt ~20° clockwise (lean to the right) around Y axis
    lock = rotate_tris(lock, angle_deg=-20, axis='y')
    # Tilt slightly forward
    lock = rotate_tris(lock, angle_deg=8, axis='x')
    # Move to upper-right of cloud
    lock = translate_tris(lock, [30, -4, 12])
    all_tris += lock
    print(f"  Padlock    : {len(lock):>6} tris")

    # Nameplate with text below the cloud
    plate = text_nameplate("AZURE CONFIDENTIAL", "COMPUTING",
                           plate_cx=0, plate_cz=-32, front_y=-28.0)
    all_tris += plate
    print(f"  Nameplate  : {len(plate):>6} tris")

    # Structural supports connecting everything
    supports = support_pillars(base_z=-44, cloud_bottom_z=-28,
                               nameplate_cz=-32,
                               nameplate_top_z=-23,
                               nameplate_bot_z=-41,
                               front_y=-28.0)
    all_tris += supports
    print(f"  Supports   : {len(supports):>6} tris")

    base = flat_base(width=130, z_bottom=-44)
    all_tris += base
    print(f"  Base       : {len(base):>6} tris")

    total = len(all_tris)
    print(f"  ──────────────────────")
    print(f"  TOTAL      : {total:>6} tris")

    # Build mesh
    m = mesh.Mesh(np.zeros(total, dtype=mesh.Mesh.dtype))
    for i, tri in enumerate(all_tris):
        for j in range(3):
            m.vectors[i][j] = tri[j]

    xr = m.x.max() - m.x.min()
    yr = m.y.max() - m.y.min()
    zr = m.z.max() - m.z.min()
    print(f"\n  Raw size: {xr:.1f} × {yr:.1f} × {zr:.1f} mm")

    # Place on build plate
    m.translate([0, 0, -m.z.min()])

    xr = m.x.max() - m.x.min()
    yr = m.y.max() - m.y.min()
    zr = m.z.max() - m.z.min()
    print(f"  Final  : {xr:.1f} × {yr:.1f} × {zr:.1f} mm (w × d × h)")

    out = "cloud_microsoft_logo.stl"
    m.save(out)
    print(f"  ✓ Saved → {out}")


if __name__ == "__main__":
    main()
