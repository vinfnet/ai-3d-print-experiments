"""
Generate an STL file of a screwdriver stuck in a banana.
Total length approximately 15cm (150mm).

Banana: ~100mm along its curve, ~30mm diameter at widest
Screwdriver: handle ~50mm, shaft ~40mm, blade ~15mm
The screwdriver blade pierces into the banana from the top.
"""

import numpy as np
from stl import mesh
import math


def create_circle_points(radius, n_points=24):
    """Create points around a circle in the XY plane."""
    angles = np.linspace(0, 2 * np.pi, n_points, endpoint=False)
    return np.column_stack([np.cos(angles) * radius, np.sin(angles) * radius])


def create_tube_segment(p1, p2, r1, r2, n_sides=24):
    """Create triangles for a tube segment between two points with given radii."""
    direction = p2 - p1
    length = np.linalg.norm(direction)
    if length < 1e-10:
        return []

    direction = direction / length

    # Find perpendicular vectors
    if abs(direction[2]) < 0.9:
        up = np.array([0, 0, 1.0])
    else:
        up = np.array([1.0, 0, 0])

    right = np.cross(direction, up)
    right = right / np.linalg.norm(right)
    up = np.cross(right, direction)
    up = up / np.linalg.norm(up)

    triangles = []
    for i in range(n_sides):
        angle1 = 2 * np.pi * i / n_sides
        angle2 = 2 * np.pi * ((i + 1) % n_sides) / n_sides

        # Points on the two circles
        offset1_a = (np.cos(angle1) * right + np.sin(angle1) * up) * r1
        offset1_b = (np.cos(angle2) * right + np.sin(angle2) * up) * r1
        offset2_a = (np.cos(angle1) * right + np.sin(angle1) * up) * r2
        offset2_b = (np.cos(angle2) * right + np.sin(angle2) * up) * r2

        v1 = p1 + offset1_a
        v2 = p1 + offset1_b
        v3 = p2 + offset2_a
        v4 = p2 + offset2_b

        # Two triangles per quad
        triangles.append([v1, v2, v3])
        triangles.append([v2, v4, v3])

    return triangles


def create_cap(center, direction, radius, n_sides=24, inward=False):
    """Create triangles for a circular cap (end cap)."""
    direction = direction / np.linalg.norm(direction)

    if abs(direction[2]) < 0.9:
        up = np.array([0, 0, 1.0])
    else:
        up = np.array([1.0, 0, 0])

    right = np.cross(direction, up)
    right = right / np.linalg.norm(right)
    up = np.cross(right, direction)
    up = up / np.linalg.norm(up)

    triangles = []
    for i in range(n_sides):
        angle1 = 2 * np.pi * i / n_sides
        angle2 = 2 * np.pi * ((i + 1) % n_sides) / n_sides

        v1 = center
        v2 = center + (np.cos(angle1) * right + np.sin(angle1) * up) * radius
        v3 = center + (np.cos(angle2) * right + np.sin(angle2) * up) * radius

        if inward:
            triangles.append([v1, v3, v2])
        else:
            triangles.append([v1, v2, v3])

    return triangles


def create_swept_shape(path_points, radius_func, n_sides=24):
    """Create a mesh by sweeping a circle along a path with varying radius."""
    triangles = []

    for i in range(len(path_points) - 1):
        p1 = path_points[i]
        p2 = path_points[i + 1]
        r1 = radius_func(i / (len(path_points) - 1))
        r2 = radius_func((i + 1) / (len(path_points) - 1))

        triangles.extend(create_tube_segment(p1, p2, r1, r2, n_sides))

    # End caps
    direction_start = path_points[1] - path_points[0]
    direction_end = path_points[-1] - path_points[-2]
    r_start = radius_func(0)
    r_end = radius_func(1)

    if r_start > 0.1:
        triangles.extend(create_cap(path_points[0], -direction_start, r_start, n_sides))
    if r_end > 0.1:
        triangles.extend(create_cap(path_points[-1], direction_end, r_end, n_sides))

    return triangles


def create_banana():
    """Create banana geometry - a curved, tapered shape."""
    n_points = 60
    n_sides = 28

    # Banana follows an arc - curve radius ~120mm, arc ~50 degrees
    # This gives a banana about 100mm along the curve
    curve_radius = 130.0
    arc_start = -0.42  # radians
    arc_end = 0.42

    angles = np.linspace(arc_start, arc_end, n_points)

    path_points = []
    for a in angles:
        x = curve_radius * np.sin(a)
        y = 0
        z = curve_radius * np.cos(a) - curve_radius  # shift so center is at origin
        path_points.append(np.array([x, y, z]))

    path_points = np.array(path_points)

    # Center the banana
    center = (path_points[0] + path_points[-1]) / 2
    path_points -= center
    # Lay it along X axis mostly
    # Rotate 90 degrees so banana is roughly along X
    # The banana is already roughly along X due to sin/cos

    def banana_radius(t):
        """Banana cross-section radius - fat in middle, tapered at ends."""
        # Main body radius with taper
        base = 15.0  # max radius ~15mm (30mm diameter)
        # Smooth taper at both ends
        taper = 1.0
        if t < 0.15:
            taper = np.sin(t / 0.15 * np.pi / 2)
        elif t > 0.85:
            taper = np.sin((1 - t) / 0.15 * np.pi / 2)

        # Slight bulge in the middle
        bulge = 1.0 + 0.08 * np.sin(t * np.pi)
        return base * taper * bulge

    # Create banana cross-sections with slight pentagonal shape
    triangles = []

    # Build the banana with elliptical cross-sections (slightly flattened)
    def get_frame(path_pts, idx):
        """Get a coordinate frame at a path point."""
        if idx == 0:
            tangent = path_pts[1] - path_pts[0]
        elif idx == len(path_pts) - 1:
            tangent = path_pts[-1] - path_pts[-2]
        else:
            tangent = path_pts[idx + 1] - path_pts[idx - 1]
        tangent = tangent / np.linalg.norm(tangent)

        if abs(tangent[1]) < 0.9:
            up = np.array([0, 1.0, 0])
        else:
            up = np.array([1.0, 0, 0])

        right = np.cross(tangent, up)
        right = right / np.linalg.norm(right)
        up = np.cross(right, tangent)
        up = up / np.linalg.norm(up)
        return tangent, right, up

    # Generate cross-section rings
    rings = []
    for i in range(n_points):
        t = i / (n_points - 1)
        r = banana_radius(t)
        tangent, right, up = get_frame(path_points, i)
        center = path_points[i]

        ring = []
        for j in range(n_sides):
            angle = 2 * np.pi * j / n_sides
            # Slightly elliptical - wider than tall
            rx = r * 1.0
            ry = r * 0.85
            point = center + (np.cos(angle) * right * rx + np.sin(angle) * up * ry)
            ring.append(point)
        rings.append(ring)

    # Connect rings with triangles
    for i in range(len(rings) - 1):
        for j in range(n_sides):
            j_next = (j + 1) % n_sides

            v1 = rings[i][j]
            v2 = rings[i][j_next]
            v3 = rings[i + 1][j]
            v4 = rings[i + 1][j_next]

            triangles.append([v1, v2, v3])
            triangles.append([v2, v4, v3])

    # End caps
    # Start cap
    start_center = path_points[0]
    tangent_start, _, _ = get_frame(path_points, 0)
    for j in range(n_sides):
        j_next = (j + 1) % n_sides
        triangles.append([start_center, rings[0][j_next], rings[0][j]])

    # End cap
    end_center = path_points[-1]
    for j in range(n_sides):
        j_next = (j + 1) % n_sides
        triangles.append([end_center, rings[-1][j], rings[-1][j_next]])

    # Add a small stem at one end
    stem_start = path_points[-1]
    tangent_end, _, _ = get_frame(path_points, n_points - 1)
    stem_length = 8.0
    stem_points = []
    for i in range(8):
        t = i / 7.0
        stem_points.append(stem_start + tangent_end * stem_length * t)
    stem_points = np.array(stem_points)

    def stem_radius(t):
        return 3.0 * (1 - t * 0.6)

    triangles.extend(create_swept_shape(stem_points, stem_radius, 12))

    return triangles, path_points


def create_screwdriver_handle(base_pos, direction, length=50.0):
    """Create screwdriver handle with grip texture."""
    direction = direction / np.linalg.norm(direction)
    n_points = 40
    n_sides = 24

    triangles = []

    # Handle path
    handle_points = []
    for i in range(n_points):
        t = i / (n_points - 1)
        handle_points.append(base_pos + direction * length * t)
    handle_points = np.array(handle_points)

    def handle_radius(t):
        """Handle profile - bulges slightly, then tapers at the butt end."""
        # Main shape
        base_r = 9.0  # 18mm diameter handle

        # Taper near the shaft end
        if t < 0.08:
            shape = 0.6 + 0.4 * (t / 0.08)
        # Flare from shaft to handle
        elif t < 0.15:
            shape = 1.0
        # Main body with subtle grip bumps
        elif t < 0.85:
            grip_t = (t - 0.15) / 0.7
            # Subtle wavy grip pattern
            shape = 1.0 + 0.06 * np.sin(grip_t * 8 * np.pi)
        # Rounded butt end
        else:
            end_t = (t - 0.85) / 0.15
            shape = 1.0 * np.cos(end_t * np.pi / 2)
            shape = max(shape, 0.01)

        return base_r * shape

    triangles.extend(create_swept_shape(handle_points, handle_radius, n_sides))

    return triangles


def create_screwdriver_shaft(base_pos, direction, length=40.0, radius=3.0):
    """Create screwdriver shaft (round rod)."""
    direction = direction / np.linalg.norm(direction)
    n_points = 20
    n_sides = 16

    shaft_points = []
    for i in range(n_points):
        t = i / (n_points - 1)
        shaft_points.append(base_pos + direction * length * t)
    shaft_points = np.array(shaft_points)

    def shaft_radius(t):
        return radius

    return create_swept_shape(shaft_points, shaft_radius, n_sides)


def create_screwdriver_blade(base_pos, direction, length=15.0):
    """Create a flathead screwdriver blade tip."""
    direction = direction / np.linalg.norm(direction)

    # Find perpendicular axes
    if abs(direction[1]) < 0.9:
        up = np.array([0, 1.0, 0])
    else:
        up = np.array([1.0, 0, 0])

    right = np.cross(direction, up)
    right = right / np.linalg.norm(right)
    up = np.cross(right, direction)
    up = up / np.linalg.norm(up)

    triangles = []

    # Blade is flat - wide in one direction, thin in the other
    # It transitions from round shaft to flat blade
    n_points = 15
    n_sides = 20

    blade_points = []
    for i in range(n_points):
        t = i / (n_points - 1)
        blade_points.append(base_pos + direction * length * t)

    # Build cross-section rings that go from round to flat
    rings = []
    for i in range(n_points):
        t = i / (n_points - 1)

        # Width increases slightly towards tip, thickness decreases
        width = 3.0 + t * 3.0  # 3mm to 6mm wide
        thickness = 3.0 * (1 - t * 0.7)  # 3mm to ~1mm thick

        center = blade_points[i]
        ring = []
        for j in range(n_sides):
            angle = 2 * np.pi * j / n_sides
            # Elliptical cross-section
            point = center + (np.cos(angle) * right * width + np.sin(angle) * up * thickness)
            ring.append(point)
        rings.append(ring)

    # Connect rings
    for i in range(len(rings) - 1):
        for j in range(n_sides):
            j_next = (j + 1) % n_sides
            v1 = rings[i][j]
            v2 = rings[i][j_next]
            v3 = rings[i + 1][j]
            v4 = rings[i + 1][j_next]
            triangles.append([v1, v2, v3])
            triangles.append([v2, v4, v3])

    # Tip cap
    tip_center = np.array(blade_points[-1])
    for j in range(n_sides):
        j_next = (j + 1) % n_sides
        triangles.append([tip_center, rings[-1][j], rings[-1][j_next]])

    # Base cap (connects to shaft)
    base_center = np.array(blade_points[0])
    for j in range(n_sides):
        j_next = (j + 1) % n_sides
        triangles.append([base_center, rings[0][j_next], rings[0][j]])

    return triangles


def create_screwdriver_in_banana():
    """Create the full scene - screwdriver stuck in a banana."""
    all_triangles = []

    # Create banana
    banana_tris, banana_path = create_banana()
    all_triangles.extend(banana_tris)

    # Find a point on the banana to insert the screwdriver
    # Insert it roughly 40% along the banana, angled slightly
    insert_idx = int(len(banana_path) * 0.4)
    insert_point = banana_path[insert_idx]

    # Screwdriver direction - mostly upward (Y+) with slight angle
    screw_dir = np.array([0.1, 1.0, 0.15])
    screw_dir = screw_dir / np.linalg.norm(screw_dir)

    # The blade goes INTO the banana, handle sticks OUT
    # Blade tip is inside the banana
    blade_length = 15.0
    shaft_length = 35.0
    handle_length = 50.0

    # Position: blade goes from inside banana upward
    # The blade enters the banana from above
    blade_entry = insert_point + screw_dir * 12.0  # Entry point on banana surface (approx)
    blade_base = blade_entry  # Where shaft meets blade
    shaft_base = blade_base + screw_dir * shaft_length
    handle_base = shaft_base
    handle_end = handle_base + screw_dir * handle_length

    # Create screwdriver parts (only the parts that are visible - outside banana)
    # Blade is partially inside banana, so we start from near the surface
    blade_visible_start = insert_point + screw_dir * 5.0
    blade_tris = create_screwdriver_blade(blade_visible_start, -screw_dir, blade_length)

    # Shaft from banana surface upward
    shaft_tris = create_screwdriver_shaft(blade_entry, screw_dir, shaft_length, radius=3.0)

    # Handle
    handle_tris = create_screwdriver_handle(shaft_base, screw_dir, handle_length)

    all_triangles.extend(blade_tris)
    all_triangles.extend(shaft_tris)
    all_triangles.extend(handle_tris)

    return all_triangles


def triangles_to_mesh(triangles):
    """Convert triangle list to numpy-stl mesh."""
    n = len(triangles)
    stl_mesh = mesh.Mesh(np.zeros(n, dtype=mesh.Mesh.dtype))

    for i, tri in enumerate(triangles):
        for j in range(3):
            stl_mesh.vectors[i][j] = tri[j]

    return stl_mesh


def main():
    print("Generating screwdriver-in-banana model...")

    triangles = create_screwdriver_in_banana()
    print(f"  Total triangles: {len(triangles)}")

    stl_mesh = triangles_to_mesh(triangles)

    # Verify dimensions
    minx = stl_mesh.x.min()
    maxx = stl_mesh.x.max()
    miny = stl_mesh.y.min()
    maxy = stl_mesh.y.max()
    minz = stl_mesh.z.min()
    maxz = stl_mesh.z.max()

    print(f"  Bounding box:")
    print(f"    X: {minx:.1f} to {maxx:.1f} ({maxx-minx:.1f} mm)")
    print(f"    Y: {miny:.1f} to {maxy:.1f} ({maxy-miny:.1f} mm)")
    print(f"    Z: {minz:.1f} to {maxz:.1f} ({maxz-minz:.1f} mm)")

    # Calculate overall diagonal
    diag = np.sqrt((maxx-minx)**2 + (maxy-miny)**2 + (maxz-minz)**2)
    print(f"  Diagonal: {diag:.1f} mm")

    # Scale to target ~150mm in the longest dimension
    dims = [maxx - minx, maxy - miny, maxz - minz]
    longest = max(dims)
    # The longest dimension should be about 150mm
    # The banana + screwdriver combined length
    target = 150.0

    if abs(longest - target) > 10:
        scale = target / longest
        print(f"  Scaling by {scale:.3f} to target {target}mm")
        stl_mesh.vectors *= scale

        # Re-check dimensions
        minx = stl_mesh.x.min()
        maxx = stl_mesh.x.max()
        miny = stl_mesh.y.min()
        maxy = stl_mesh.y.max()
        minz = stl_mesh.z.min()
        maxz = stl_mesh.z.max()
        print(f"  Scaled bounding box:")
        print(f"    X: {minx:.1f} to {maxx:.1f} ({maxx-minx:.1f} mm)")
        print(f"    Y: {miny:.1f} to {maxy:.1f} ({maxy-miny:.1f} mm)")
        print(f"    Z: {minz:.1f} to {maxz:.1f} ({maxz-minz:.1f} mm)")

    # Center on build plate (Z min = 0)
    stl_mesh.translate([0, 0, -stl_mesh.z.min()])

    output_path = "screwdriver_in_banana.stl"
    stl_mesh.save(output_path)
    print(f"\n  Saved to: {output_path}")
    print("  Ready for slicing and 3D printing!")


if __name__ == "__main__":
    main()
