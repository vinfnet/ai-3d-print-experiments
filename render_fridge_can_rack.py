"""
Render PNG visualisations of the fridge can rack.

Pure numpy + zlib software renderer (flat shading, orthographic z-buffer) —
no matplotlib or other extra dependencies required.

Outputs:
  fridge_can_rack.png        — assembled rack under a glass shelf, loaded
                               with five 330ml cans
  fridge_can_rack_parts.png  — the three printable parts
"""

import struct
import zlib

import numpy as np
from stl import mesh

import generate_fridge_can_rack as rack


# ═══════════════════════════════════════════════════════════════════════
#  Tiny PNG writer
# ═══════════════════════════════════════════════════════════════════════

def write_png(filename, rgb):
    """rgb: (H, W, 3) uint8 array."""
    h, w, _ = rgb.shape
    raw = b"".join(b"\x00" + rgb[y].tobytes() for y in range(h))

    def chunk(tag, data):
        c = struct.pack(">I", len(data)) + tag + data
        return c + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(raw, 9))
    png += chunk(b"IEND", b"")
    with open(filename, "wb") as f:
        f.write(png)


# ═══════════════════════════════════════════════════════════════════════
#  Geometry helpers
# ═══════════════════════════════════════════════════════════════════════

def tris_to_array(tris):
    return np.asarray([[np.asarray(v, dtype=float) for v in t] for t in tris])


def load_stl(filename):
    m = mesh.Mesh.from_file(filename)
    return np.array(m.vectors, dtype=float)


def cylinder_z(x, y, radius, z0, z1, n=48):
    """Cylinder with its axis along Z — stands in for an upright can."""
    tris = []
    ring = [(x + radius * np.cos(a), y + radius * np.sin(a))
            for a in np.linspace(0, 2 * np.pi, n, endpoint=False)]
    for i in range(n):
        j = (i + 1) % n
        a, b = ring[i], ring[j]
        p0 = np.array([a[0], a[1], z0])
        p1 = np.array([b[0], b[1], z0])
        p2 = np.array([b[0], b[1], z1])
        p3 = np.array([a[0], a[1], z1])
        tris += [[p0, p1, p2], [p0, p2, p3]]
    for z, flip in ((z0, True), (z1, False)):
        c = np.array([x, y, z])
        for i in range(n):
            j = (i + 1) % n
            p = np.array([ring[i][0], ring[i][1], z])
            q = np.array([ring[j][0], ring[j][1], z])
            tris.append([c, q, p] if flip else [c, p, q])
    return tris_to_array(tris)


# ═══════════════════════════════════════════════════════════════════════
#  Renderer
# ═══════════════════════════════════════════════════════════════════════

def render(objects, size, cam_dir, light=(-0.4, -0.7, 0.8), bg=(250, 250, 250),
           margin=0.06):
    """objects: list of (triangles (N,3,3), colour (r,g,b), alpha)."""
    w, h = size
    cam_dir = np.asarray(cam_dir, dtype=float)
    cam_dir /= np.linalg.norm(cam_dir)
    view = -cam_dir
    right = np.cross(view, np.array([0.0, 0.0, 1.0]))
    right /= np.linalg.norm(right)
    up = np.cross(right, view)
    light = np.asarray(light, dtype=float)
    light /= np.linalg.norm(light)

    allv = np.concatenate([o[0].reshape(-1, 3) for o in objects])
    centre = (allv.min(axis=0) + allv.max(axis=0)) / 2

    def project(v):
        d = v - centre
        return np.stack([d @ right, d @ up, d @ view], axis=-1)

    proj = [project(o[0].reshape(-1, 3)).reshape(o[0].shape) for o in objects]
    pv = np.concatenate([p.reshape(-1, 3) for p in proj])
    ext_u = pv[:, 0].max() - pv[:, 0].min()
    ext_v = pv[:, 1].max() - pv[:, 1].min()
    scale = min(w * (1 - 2 * margin) / ext_u, h * (1 - 2 * margin) / ext_v)

    img = np.zeros((h, w, 3), dtype=float)
    img[:] = np.asarray(bg, dtype=float)

    opaque = [(p, o[1], o[2]) for p, o in zip(proj, objects) if o[2] >= 1.0]
    glassy = [(p, o[1], o[2]) for p, o in zip(proj, objects) if o[2] < 1.0]

    depth = np.full((h, w), np.inf)
    _draw(img, depth, opaque, scale, w, h, right, up, view, light, None)

    if glassy:
        gimg = img.copy()
        gdepth = np.full((h, w), np.inf)
        _draw(gimg, gdepth, glassy, scale, w, h, right, up, view, light, None)
        visible = gdepth < depth
        alpha = glassy[0][2]
        img[visible] = img[visible] * (1 - alpha) + gimg[visible] * alpha

    return np.clip(img, 0, 255).astype(np.uint8)


def _draw(img, depth, items, scale, w, h, right, up, view, light, _unused):
    for tri, colour, _alpha in items:
        colour = np.asarray(colour, dtype=float)

        # Screen-space coordinates (y flipped so +up is up in the image)
        sx = tri[:, :, 0] * scale + w / 2
        sy = h / 2 - tri[:, :, 1] * scale
        sz = tri[:, :, 2]

        # World-space normals for shading
        e1 = tri[:, 1] - tri[:, 0]
        e2 = tri[:, 2] - tri[:, 0]
        n = np.cross(e1, e2)
        ln = np.linalg.norm(n, axis=1)
        ln[ln == 0] = 1.0
        n = n / ln[:, None]
        # Back-facing triangles get flipped toward the camera
        facing = n[:, 2] > 0
        n[facing] *= -1
        world_n = n[:, 0:1] * right + n[:, 1:2] * up + n[:, 2:3] * view
        shade = 0.30 + 0.70 * np.clip(world_n @ light, 0, 1)

        for k in range(tri.shape[0]):
            x0, x1, x2 = sx[k]
            y0, y1, y2 = sy[k]
            area = (x1 - x0) * (y2 - y0) - (x2 - x0) * (y1 - y0)
            if abs(area) < 1e-9:
                continue
            xmin = max(int(np.floor(min(x0, x1, x2))), 0)
            xmax = min(int(np.ceil(max(x0, x1, x2))), w - 1)
            ymin = max(int(np.floor(min(y0, y1, y2))), 0)
            ymax = min(int(np.ceil(max(y0, y1, y2))), h - 1)
            if xmin > xmax or ymin > ymax:
                continue

            px, py = np.meshgrid(np.arange(xmin, xmax + 1) + 0.5,
                                 np.arange(ymin, ymax + 1) + 0.5)
            w0 = ((x1 - x0) * (py - y0) - (px - x0) * (y1 - y0)) / area
            w1 = ((px - x0) * (y2 - y0) - (x2 - x0) * (py - y0)) / area
            inside = (w0 >= 0) & (w1 >= 0) & (w0 + w1 <= 1)
            if not inside.any():
                continue

            z = sz[k][0] + w1 * (sz[k][1] - sz[k][0]) + w0 * (sz[k][2] - sz[k][0])
            sub = depth[ymin:ymax + 1, xmin:xmax + 1]
            hit = inside & (z < sub)
            if not hit.any():
                continue
            sub[hit] = z[hit]
            img[ymin:ymax + 1, xmin:xmax + 1][hit] = colour * shade[k]


# ═══════════════════════════════════════════════════════════════════════
#  Scenes
# ═══════════════════════════════════════════════════════════════════════

RACK_COLOUR = (60, 130, 200)
CAN_COLOUR = (210, 80, 70)
GLASS_COLOUR = (180, 225, 235)


def scene_assembly():
    rack_tris = load_stl("fridge_can_rack_assembly.stl")
    # The saved assembly has Z-min = 0; that matches the design coordinates.

    cans = []
    r = rack.CAN_DIA / 2
    for i in range(rack.N_BAYS):
        y = i * rack.BAY + rack.RIDGE_T + r
        cans.append(cylinder_z(0.0, y, r,
                               rack.Z_FLOOR, rack.Z_FLOOR + rack.CAN_H))
    cans = np.concatenate(cans)

    shelf = rack.box(-190.0, 190.0, 0.0, rack.SHELF_DEPTH,
                     rack.Z_GLASS_BOT, rack.Z_GLASS_TOP)
    shelf = tris_to_array(shelf)

    return [(rack_tris, RACK_COLOUR, 1.0),
            (cans, CAN_COLOUR, 1.0),
            (shelf, GLASS_COLOUR, 0.45)]


def scene_parts():
    parts = [
        ("fridge_can_rack_bay.stl", RACK_COLOUR),
        ("fridge_can_rack_bay_front.stl", (70, 105, 170)),
        ("fridge_can_rack_shelf_clip_right.stl", (90, 170, 120)),
        ("fridge_can_rack_end_stop.stl", (200, 160, 70)),
    ]

    out = []
    dy = 0.0
    for filename, colour in parts:
        tris = load_stl(filename).copy()
        span = tris[:, :, 1].max() - tris[:, :, 1].min()
        tris[:, :, 1] += dy - tris[:, :, 1].min()
        out.append((tris, colour, 1.0))
        dy += span + 50.0
    return out


def main():
    print("Rendering fridge can rack …")

    img = render(scene_assembly(), (1400, 900), cam_dir=(-0.75, -1.0, 0.55))
    write_png("fridge_can_rack.png", img)
    print("  ✓ fridge_can_rack.png")

    img = render(scene_parts(), (1400, 620), cam_dir=(-0.6, -1.0, 0.75))
    write_png("fridge_can_rack_parts.png", img)
    print("  ✓ fridge_can_rack_parts.png")


if __name__ == "__main__":
    main()
