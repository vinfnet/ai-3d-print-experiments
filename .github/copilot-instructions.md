# Copilot Instructions — AI 3D Print Experiments

## Project Overview

Procedural 3D-printable STL model generator. Each Python script constructs triangle meshes from geometric primitives (spheres, cylinders, swept profiles, extruded text) using only `numpy` and `numpy-stl`. No CAD libraries — all geometry is hand-built from vertices and triangle faces.

## Architecture & Patterns

### Script structure (follow existing scripts as templates)
Every generator script follows this pattern — see `generate_coffee_cup.py` for the simplest example:

1. **Helper functions** that produce `list[list[np.ndarray]]` — each inner list is a triangle (3 vertices)
2. **Component functions** (e.g. `cup_body()`, `cup_handle()`) that return triangle lists for a single part
3. **`main()`** that assembles components, builds an `stl.mesh.Mesh`, prints dimensions, translates Z-min to 0, and saves

```python
# Triangle format used throughout: list of [v0, v1, v2] where each vertex is np.array([x, y, z])
all_tris += component_function()
m = mesh.Mesh(np.zeros(len(all_tris), dtype=mesh.Mesh.dtype))
for i, tri in enumerate(all_tris):
    for j in range(3):
        m.vectors[i][j] = tri[j]
m.save("output.stl")
```

### Geometry conventions
- **Units**: millimeters (real-world print dimensions, typically 80–150 mm total)
- **Orientation**: Z-up; models are translated so Z-min = 0 (flat on print bed) before saving
- **Front face**: typically -Y direction (see `generate_cloud_ms_logo.py` logo placement at `front_y=-28.0`)
- **Watertight meshes**: cap all tube ends and close all holes — important for 3D printing
- **Triangle winding**: outward-facing normals via consistent vertex winding order; inner surfaces use reversed winding

### Common geometric primitives (reuse from existing scripts)
| Primitive | Reference |
|-----------|-----------|
| Hollow tapered cylinder | `cup_body()` in `generate_coffee_cup.py` |
| Swept tube along path | `create_swept_shape()` in `generate_screwdriver_banana.py` |
| Sphere / hemisphere | `sphere_triangles()` in `generate_cloud_ms_logo.py` |
| Axis-aligned box | `box_triangles()` in `generate_cloud_ms_logo.py` |
| Cylinder between two points | `cylinder_triangles()` in `generate_cloud_ms_logo.py` |
| Torus arc segment | `torus_segment()` in `generate_cloud_ms_logo.py` |
| 3D extruded text (stroke font) | `text_3d()` / `STROKE_FONT` in `generate_cloud_ms_logo.py` |

### Naming & output
- Script: `generate_<descriptive_name>.py`
- Output STL: `<descriptive_name>.stl` (saved in repo root)
- Print bounding box info and triangle counts during generation

## Dependencies

Only two packages: `numpy` and `numpy-stl`. Import `stl.mesh` as `from stl import mesh`.

```bash
python -m venv .venv && source .venv/bin/activate
pip install numpy numpy-stl
```

## Security

A pre-commit hook (`.githooks/pre-commit`) scans staged files for secret patterns. Configure with:
```bash
git config core.hooksPath .githooks
```

## When adding a new model

1. Create `generate_<name>.py` following the pattern above
2. Reuse primitive helpers from existing scripts or copy them in (no shared library yet)
3. Target real-world dimensions in mm; print the bounding box in `main()`
4. Ensure Z-min = 0 before saving
5. Add the model to the table in `README.md`
