"""
Create a narrower version of the bowl stacker .3mf file.

Strategy: Thin the outer voronoi panels (beyond |X| > 33 in raw coords)
while keeping the interior bowl gap unchanged. This reduces the overall
width from ~152mm to ~120mm so two stackers fit side-by-side on a
quarter-circle corner shelf.

Interior dimensions (bowl gap) are preserved exactly.
"""
import zipfile
import re
import numpy as np

INPUT = 'Bowl_Stacker_John Lewis bowls.3mf'
OUTPUT = 'Bowl_Stacker_John Lewis bowls_narrow.3mf'

# --- Configuration ---
# In raw object coordinates (before build scale of 1.32x):
# The voronoi panel inner faces are at |X| ≈ 33
# The outer edges are at |X| ≈ 57.5
# We compress the outer region to make panels thinner.

INNER_THRESHOLD = 33.0   # X position of inner panel face (raw coords)
BUILD_SCALE_XY = 1.32173913  # from the .3mf build transform

# Target: 120mm total width (currently 152mm)
# Panel thickness: (120/2 - 33*1.32) / 1.32 + 33 = each side has ~12.4mm raw
TARGET_OUTER_X = 120.0 / (2.0 * BUILD_SCALE_XY)  # = 45.4mm raw
CURRENT_OUTER_X = 57.5  # approximate max |X| in raw coords

COMPRESS_FACTOR = (TARGET_OUTER_X - INNER_THRESHOLD) / (CURRENT_OUTER_X - INNER_THRESHOLD)
# ≈ 0.508

print(f"Compression settings:")
print(f"  Inner threshold: {INNER_THRESHOLD:.1f}mm raw")
print(f"  Current outer: ±{CURRENT_OUTER_X:.1f}mm raw → ±{CURRENT_OUTER_X * BUILD_SCALE_XY:.1f}mm final")
print(f"  Target outer: ±{TARGET_OUTER_X:.1f}mm raw → ±{TARGET_OUTER_X * BUILD_SCALE_XY:.1f}mm final")
print(f"  Compress factor: {COMPRESS_FACTOR:.3f}")
print(f"  Wall thickness: {(CURRENT_OUTER_X - INNER_THRESHOLD) * BUILD_SCALE_XY:.1f}mm → {(TARGET_OUTER_X - INNER_THRESHOLD) * BUILD_SCALE_XY:.1f}mm")
print(f"  Interior gap preserved: {2 * INNER_THRESHOLD * BUILD_SCALE_XY:.1f}mm")
print(f"  Total width: {2 * CURRENT_OUTER_X * BUILD_SCALE_XY:.1f}mm → {2 * TARGET_OUTER_X * BUILD_SCALE_XY:.1f}mm")
print()

# --- Read input ---
with zipfile.ZipFile(INPUT, 'r') as zf_in:
    names = zf_in.namelist()
    files = {}
    for name in names:
        files[name] = zf_in.read(name)

# --- Modify the mesh vertices ---
obj_key = '3D/Objects/object_7.model'
obj_xml = files[obj_key].decode('utf-8')

vertex_count = 0
modified_count = 0

def transform_vertex(match):
    global vertex_count, modified_count
    vertex_count += 1
    
    x = float(match.group(1))
    y_str = match.group(2)
    z_str = match.group(3)
    
    if abs(x) > INNER_THRESHOLD:
        modified_count += 1
        sign = 1.0 if x > 0 else -1.0
        new_x = sign * (INNER_THRESHOLD + (abs(x) - INNER_THRESHOLD) * COMPRESS_FACTOR)
        return f'<vertex x="{new_x:.7f}" y="{y_str}" z="{z_str}"/>'
    
    return match.group(0)  # unchanged

pattern = r'<vertex x="([^"]+)" y="([^"]+)" z="([^"]+)"/>'
modified_xml = re.sub(pattern, transform_vertex, obj_xml)

print(f"Processed {vertex_count} vertices, modified {modified_count} ({100*modified_count/vertex_count:.1f}%)")

files[obj_key] = modified_xml.encode('utf-8')

# --- Verify the result by parsing bounds ---
def get_bounds(xml_str):
    xs, ys, zs = [], [], []
    for m in re.finditer(r'<vertex x="([^"]+)" y="([^"]+)" z="([^"]+)"/>', xml_str):
        xs.append(float(m.group(1)))
        ys.append(float(m.group(2)))
        zs.append(float(m.group(3)))
    return (min(xs), max(xs)), (min(ys), max(ys)), (min(zs), max(zs))

print("\nOriginal mesh bounds (raw):")
xb, yb, zb = get_bounds(obj_xml)
print(f"  X: [{xb[0]:.2f}, {xb[1]:.2f}] span {xb[1]-xb[0]:.2f}")
print(f"  Y: [{yb[0]:.2f}, {yb[1]:.2f}] span {yb[1]-yb[0]:.2f}")
print(f"  Z: [{zb[0]:.2f}, {zb[1]:.2f}] span {zb[1]-zb[0]:.2f}")

print("\nModified mesh bounds (raw):")
xb2, yb2, zb2 = get_bounds(modified_xml)
print(f"  X: [{xb2[0]:.2f}, {xb2[1]:.2f}] span {xb2[1]-xb2[0]:.2f}")
print(f"  Y: [{yb2[0]:.2f}, {yb2[1]:.2f}] span {yb2[1]-yb2[0]:.2f}")
print(f"  Z: [{zb2[0]:.2f}, {zb2[1]:.2f}] span {zb2[1]-zb2[0]:.2f}")

print(f"\nFinal dimensions (after build scale {BUILD_SCALE_XY:.4f}x XY, 1.1206x Z):")
print(f"  Width (X):  {(xb2[1]-xb2[0]) * BUILD_SCALE_XY:.1f}mm  (was {(xb[1]-xb[0]) * BUILD_SCALE_XY:.1f}mm)")
print(f"  Depth (Y→Z after rotation, scaled XY): {(zb2[1]-zb2[0]) * BUILD_SCALE_XY:.1f}mm  (unchanged)")
print(f"  Height (Y raw → Z final, scaled Z): {(yb2[1]-yb2[0]) * 1.12058617:.1f}mm  (unchanged)")

# --- Write output ---
with zipfile.ZipFile(OUTPUT, 'w', zipfile.ZIP_DEFLATED) as zf_out:
    for name in names:
        zf_out.writestr(name, files[name])

print(f"\nSaved: {OUTPUT}")
print(f"\nTwo of these side by side: {2 * (xb2[1]-xb2[0]) * BUILD_SCALE_XY:.0f}mm + gap")
