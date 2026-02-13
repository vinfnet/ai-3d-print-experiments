"""
Generate an STL file of a coffee cup for 3D printing.
~80mm tall, ~75mm rim diameter — a standard mug size.
Features: slightly tapered body, flat base, C-shaped handle.
"""

import numpy as np
from stl import mesh


def norm(v):
    n = np.linalg.norm(v)
    return v / n if n > 1e-12 else v


# ═══════════════════════════════════════════════════════════════════════
#  Cup body — hollow cylinder, slightly wider at top
# ═══════════════════════════════════════════════════════════════════════

def cup_body(height=80.0, r_bottom=32.0, r_top=37.0, wall=2.5,
             base_thick=3.0, n_sides=48, n_height=40):
    """Hollow tapered cylinder with a solid bottom."""
    tris = []

    # Radii at each height step (outer and inner)
    def r_outer(t):
        return r_bottom + (r_top - r_bottom) * t

    def r_inner(t):
        return r_outer(t) - wall

    # Build rings
    outer_rings = []
    inner_rings = []
    for i in range(n_height + 1):
        t = i / n_height
        z = t * height
        ro = r_outer(t)
        ri = r_inner(t)
        o_ring, i_ring = [], []
        for j in range(n_sides):
            a = 2 * np.pi * j / n_sides
            ca, sa = np.cos(a), np.sin(a)
            o_ring.append(np.array([ca * ro, sa * ro, z]))
            i_ring.append(np.array([ca * ri, sa * ri, z]))
        outer_rings.append(o_ring)
        inner_rings.append(i_ring)

    # Outer surface
    for i in range(n_height):
        for j in range(n_sides):
            jn = (j + 1) % n_sides
            tris += [[outer_rings[i][j], outer_rings[i][jn], outer_rings[i+1][j]],
                     [outer_rings[i][jn], outer_rings[i+1][jn], outer_rings[i+1][j]]]

    # Inner surface (reversed winding)
    for i in range(n_height):
        for j in range(n_sides):
            jn = (j + 1) % n_sides
            tris += [[inner_rings[i][j], inner_rings[i+1][j], inner_rings[i][jn]],
                     [inner_rings[i][jn], inner_rings[i+1][j], inner_rings[i+1][jn]]]

    # Top rim — connect outer to inner at Z = height
    for j in range(n_sides):
        jn = (j + 1) % n_sides
        tris += [[outer_rings[-1][j], outer_rings[-1][jn], inner_rings[-1][j]],
                 [outer_rings[-1][jn], inner_rings[-1][jn], inner_rings[-1][j]]]

    # Bottom — flat disc (outer surface only, since it's solid base)
    # Outer bottom ring
    center_bot = np.array([0.0, 0.0, 0.0])
    for j in range(n_sides):
        jn = (j + 1) % n_sides
        tris.append([center_bot, outer_rings[0][jn], outer_rings[0][j]])

    # Inner bottom — close the inside at z = base_thick
    # Find the ring closest to base_thick
    base_ring_idx = max(1, int(base_thick / height * n_height))
    center_base = np.array([0.0, 0.0, base_thick])
    for j in range(n_sides):
        jn = (j + 1) % n_sides
        tris.append([center_base, inner_rings[base_ring_idx][j],
                     inner_rings[base_ring_idx][jn]])

    # Fill inner wall from z=0 to z=base_thick (close off the gap)
    for i in range(base_ring_idx):
        for j in range(n_sides):
            jn = (j + 1) % n_sides
            # Close inner surface below base with outer radius
            # (the inner cavity doesn't exist below the base)
            tris += [[inner_rings[i][j], inner_rings[i+1][j], inner_rings[i][jn]],
                     [inner_rings[i][jn], inner_rings[i+1][j], inner_rings[i+1][jn]]]

    return tris


# ═══════════════════════════════════════════════════════════════════════
#  Handle — C-shaped torus section on the side
# ═══════════════════════════════════════════════════════════════════════

def cup_handle(cup_height=80.0, r_cup_mid=35.0, handle_r=18.0,
               tube_r=5.0, n_arc=40, n_tube=16):
    """C-shaped handle attached to the side of the cup."""
    tris = []

    # Handle center is offset from cup center
    # Arc goes from ~20% up the cup to ~75% up
    z_bottom = cup_height * 0.22
    z_top = cup_height * 0.78
    z_center = (z_bottom + z_top) / 2
    arc_center = np.array([r_cup_mid, 0.0, z_center])

    # Arc spans from bottom attachment to top attachment
    arc_half = np.pi * 0.72  # slightly more than half circle
    arc_angles = np.linspace(arc_half, -arc_half, n_arc)

    # Path of the handle centerline (arc in the XZ plane at Y=0)
    path = []
    for a in arc_angles:
        x = arc_center[0] + handle_r * np.cos(a)
        z = arc_center[2] + handle_r * np.sin(a)
        path.append(np.array([x, 0.0, z]))
    path = np.array(path)

    # Build tube rings along the path
    rings = []
    for i in range(n_arc):
        # Tangent
        if i == 0:
            t = norm(path[1] - path[0])
        elif i == n_arc - 1:
            t = norm(path[-1] - path[-2])
        else:
            t = norm(path[i+1] - path[i-1])

        # Frame
        ref = np.array([0, 1.0, 0])
        r = norm(np.cross(t, ref))
        u = norm(np.cross(r, t))

        # Tube radius varies — slightly thicker in the middle
        frac = i / (n_arc - 1)
        tr = tube_r * (1.0 + 0.15 * np.sin(frac * np.pi))

        # Slightly oval cross-section (wider in Y, thinner radially)
        ring = []
        for j in range(n_tube):
            a = 2 * np.pi * j / n_tube
            pt = path[i] + r * np.cos(a) * tr * 0.85 + u * np.sin(a) * tr
            ring.append(pt)
        rings.append(ring)

    # Stitch rings
    for i in range(n_arc - 1):
        for j in range(n_tube):
            jn = (j + 1) % n_tube
            tris += [[rings[i][j], rings[i][jn], rings[i+1][j]],
                     [rings[i][jn], rings[i+1][jn], rings[i+1][j]]]

    # Cap the ends (they merge into the cup wall in practice,
    # but capping makes the mesh watertight)
    for end, winding in [(0, -1), (-1, 1)]:
        center = path[end].copy()
        for j in range(n_tube):
            jn = (j + 1) % n_tube
            if winding == -1:
                tris.append([center, rings[end][jn], rings[end][j]])
            else:
                tris.append([center, rings[end][j], rings[end][jn]])

    return tris


# ═══════════════════════════════════════════════════════════════════════
#  Assemble & export
# ═══════════════════════════════════════════════════════════════════════

def main():
    print("Generating coffee cup …")

    CUP_H = 80.0
    R_BOT = 32.0
    R_TOP = 37.0

    all_tris = []

    body = cup_body(height=CUP_H, r_bottom=R_BOT, r_top=R_TOP)
    all_tris += body
    print(f"  Cup body : {len(body):>5} tris")

    handle = cup_handle(cup_height=CUP_H, r_cup_mid=(R_BOT + R_TOP) / 2)
    all_tris += handle
    print(f"  Handle   : {len(handle):>5} tris")

    total = len(all_tris)
    print(f"  TOTAL    : {total:>5} tris")

    # Build mesh
    m = mesh.Mesh(np.zeros(total, dtype=mesh.Mesh.dtype))
    for i, tri in enumerate(all_tris):
        for j in range(3):
            m.vectors[i][j] = tri[j]

    # Print dimensions
    xr = m.x.max() - m.x.min()
    yr = m.y.max() - m.y.min()
    zr = m.z.max() - m.z.min()
    print(f"\n  Size: {xr:.1f} × {yr:.1f} × {zr:.1f} mm")
    print(f"  (width × depth × height)")

    # Z min should already be 0, but ensure it
    m.translate([0, 0, -m.z.min()])

    out = "coffee_cup.stl"
    m.save(out)
    print(f"  ✓ Saved → {out}")


if __name__ == "__main__":
    main()
