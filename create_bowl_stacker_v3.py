"""
Create Bowl_stacker_JL_v3.3mf from the existing narrow bowl stacker.

v3 keeps the bowl cavity and overall height/depth unchanged, but trims the
outer side panels a little more so two stackers can fit comfortably within a
250x280mm shelf footprint without overhang.
"""
import re
import zipfile
from typing import Match, Tuple

INPUT = "Bowl_Stacker_John Lewis bowls.3mf"
OUTPUT = "Bowl_stacker_JL_v3.3mf"

OBJ_KEY = "3D/Objects/object_7.model"
INNER_THRESHOLD = 33.0
BUILD_SCALE_XY = 1.32173913
CURRENT_OUTER_X = 57.5
TARGET_WIDTH_MM = 118.0
TARGET_OUTER_X = TARGET_WIDTH_MM / (2.0 * BUILD_SCALE_XY)
COMPRESS_FACTOR = (TARGET_OUTER_X - INNER_THRESHOLD) / (CURRENT_OUTER_X - INNER_THRESHOLD)

VERTEX_PATTERN = re.compile(r'<vertex x="([^"]+)" y="([^"]+)" z="([^"]+)"/>')


def transform_vertex(match: Match[str]) -> str:
    x = float(match.group(1))
    y_str = match.group(2)
    z_str = match.group(3)

    if abs(x) <= INNER_THRESHOLD:
        return match.group(0)

    sign = 1.0 if x > 0 else -1.0
    new_x = sign * (INNER_THRESHOLD + (abs(x) - INNER_THRESHOLD) * COMPRESS_FACTOR)
    return f'<vertex x="{new_x:.7f}" y="{y_str}" z="{z_str}"/>'


def get_bounds(xml_str: str) -> Tuple[Tuple[float, float], Tuple[float, float], Tuple[float, float]]:
    xs, ys, zs = [], [], []
    for match in VERTEX_PATTERN.finditer(xml_str):
        xs.append(float(match.group(1)))
        ys.append(float(match.group(2)))
        zs.append(float(match.group(3)))
    return (min(xs), max(xs)), (min(ys), max(ys)), (min(zs), max(zs))


def main() -> None:
    with zipfile.ZipFile(INPUT, "r") as zf_in:
        names = zf_in.namelist()
        files = {name: zf_in.read(name) for name in names}

    obj_xml = files[OBJ_KEY].decode("utf-8")
    modified_xml = VERTEX_PATTERN.sub(transform_vertex, obj_xml)
    files[OBJ_KEY] = modified_xml.encode("utf-8")

    (xb, _, zb) = get_bounds(modified_xml)
    width_mm = (xb[1] - xb[0]) * BUILD_SCALE_XY
    depth_mm = (zb[1] - zb[0]) * BUILD_SCALE_XY

    with zipfile.ZipFile(OUTPUT, "w", zipfile.ZIP_DEFLATED) as zf_out:
        for name in names:
            zf_out.writestr(name, files[name])

    print(f"Saved: {OUTPUT}")
    print(f"Width: {width_mm:.1f}mm, Depth: {depth_mm:.1f}mm")
    print(f"Two side-by-side width: {2 * width_mm:.1f}mm (shelf width 250mm)")


if __name__ == "__main__":
    main()
