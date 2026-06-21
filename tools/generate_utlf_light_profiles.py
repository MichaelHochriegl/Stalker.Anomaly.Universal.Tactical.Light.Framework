#!/usr/bin/env python3
"""Generate neutral grayscale UTLF tactical light beam masks."""

from __future__ import annotations

import argparse
import hashlib
import math
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


SIZE = 256
ROOT = Path(__file__).resolve().parents[1]
PREVIEW_DIR = ROOT / "tools" / "light_profile_previews"
DDS_DIR = ROOT / "gamedata" / "textures" / "utlf" / "lights"
MAGICK = Path("/usr/bin/magick")

PROFILES = {
    "spot_throw": {
        "seed": 0x5448524F,
        "components": (
            (1.00, 0.060, 0.210),
            (0.54, 0.120, 0.500),
            (0.16, 0.280, 0.940),
        ),
        "dither": 3.0,
    },
    "spot_flood": {
        "seed": 0x464C4F4F,
        "components": (
            (0.94, 0.180, 0.440),
            (0.62, 0.250, 0.800),
            (0.20, 0.420, 0.985),
        ),
        "dither": 2.0,
    },
    "spot_balanced": {
        "seed": 0x42414C4E,
        "components": (
            (0.98, 0.100, 0.285),
            (0.56, 0.160, 0.610),
            (0.16, 0.340, 0.950),
        ),
        "dither": 2.5,
    },
}


def magick_path() -> str:
    found = shutil.which("magick")
    if found:
        return found
    if MAGICK.exists():
        return str(MAGICK)
    raise RuntimeError("ImageMagick 'magick' was not found")


def run_magick(args: list[str]) -> None:
    subprocess.run([magick_path(), *args], check=True)


def smoothstep(edge0: float, edge1: float, value: float) -> float:
    if value <= edge0:
        return 0.0
    if value >= edge1:
        return 1.0
    t = (value - edge0) / (edge1 - edge0)
    return t * t * (3.0 - 2.0 * t)


def profile_noise(seed: int, x: int, y: int) -> float:
    n = (seed ^ (x * 0x45D9F3B) ^ (y * 0x119DE1F3)) & 0xFFFFFFFF
    n ^= n >> 16
    n = (n * 0x7FEB352D) & 0xFFFFFFFF
    n ^= n >> 15
    n = (n * 0x846CA68B) & 0xFFFFFFFF
    n ^= n >> 16
    return ((n & 0xFF) / 127.5) - 1.0


def render_profile(name: str) -> bytes:
    spec = PROFILES[name]
    seed = spec["seed"]
    dither = spec["dither"]
    pixels = bytearray()
    half = SIZE / 2.0

    for y in range(SIZE):
        ny = ((y + 0.5) - half) / half
        for x in range(SIZE):
            nx = ((x + 0.5) - half) / half
            radius = math.sqrt(nx * nx + ny * ny)

            if radius >= 1.0:
                value = 0.0
            else:
                value = 0.0
                for strength, inner, outer in spec["components"]:
                    value = max(value, strength * (1.0 - smoothstep(inner, outer, radius)))

                edge_fade = 1.0 - smoothstep(0.965, 1.0, radius)
                value *= edge_fade

                if value > 0.0:
                    value = (value * 255.0) + (profile_noise(seed, x, y) * dither)
                else:
                    value = 0.0

            gray = max(0, min(255, int(round(value))))
            pixels.extend((gray, gray, gray))

    return bytes(pixels)


def write_ppm(path: Path, pixels: bytes, width: int, height: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as handle:
        handle.write(f"P6\n{width} {height}\n255\n".encode("ascii"))
        handle.write(pixels)


def contact_sheet(profile_pixels: dict[str, bytes]) -> tuple[bytes, int, int]:
    gutter = 16
    width = (SIZE * len(PROFILES)) + (gutter * (len(PROFILES) + 1))
    height = SIZE + (gutter * 2)
    sheet = bytearray([24] * width * height * 3)

    for index, name in enumerate(PROFILES):
        offset_x = gutter + index * (SIZE + gutter)
        offset_y = gutter
        pixels = profile_pixels[name]
        for y in range(SIZE):
            src_row = y * SIZE * 3
            dst_row = ((offset_y + y) * width + offset_x) * 3
            sheet[dst_row : dst_row + SIZE * 3] = pixels[src_row : src_row + SIZE * 3]

    return bytes(sheet), width, height


def generate(root: Path) -> None:
    preview_dir = root / "tools" / "light_profile_previews"
    dds_dir = root / "gamedata" / "textures" / "utlf" / "lights"
    preview_dir.mkdir(parents=True, exist_ok=True)
    dds_dir.mkdir(parents=True, exist_ok=True)

    profile_pixels = {name: render_profile(name) for name in PROFILES}

    with tempfile.TemporaryDirectory(prefix="utlf_light_profiles_") as temp_name:
        temp = Path(temp_name)

        for name, pixels in profile_pixels.items():
            source = temp / f"{name}.ppm"
            write_ppm(source, pixels, SIZE, SIZE)
            run_magick([str(source), str(preview_dir / f"{name}.png")])
            run_magick(
                [
                    str(source),
                    "-define",
                    "dds:compression=dxt1",
                    str(dds_dir / f"{name}.dds"),
                ]
            )

        sheet_pixels, sheet_width, sheet_height = contact_sheet(profile_pixels)
        sheet_source = temp / "utlf_beam_profiles.ppm"
        write_ppm(sheet_source, sheet_pixels, sheet_width, sheet_height)
        run_magick([str(sheet_source), str(preview_dir / "utlf_beam_profiles.png")])


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def expected_files(root: Path) -> list[Path]:
    files = []
    for name in PROFILES:
        files.append(root / "tools" / "light_profile_previews" / f"{name}.png")
        files.append(root / "gamedata" / "textures" / "utlf" / "lights" / f"{name}.dds")
    files.append(root / "tools" / "light_profile_previews" / "utlf_beam_profiles.png")
    return files


def raw_rgb(path: Path) -> bytes:
    return subprocess.check_output(
        [magick_path(), str(path), "-alpha", "off", "-depth", "8", "rgb:-"]
    )


def assert_neutral_pngs(root: Path) -> None:
    for name in PROFILES:
        path = root / "tools" / "light_profile_previews" / f"{name}.png"
        data = raw_rgb(path)
        for index in range(0, len(data), 3):
            if data[index] != data[index + 1] or data[index] != data[index + 2]:
                raise RuntimeError(f"{path} contains a non-neutral pixel")


def assert_hot_core_order(root: Path) -> None:
    counts = {}
    for name in PROFILES:
        path = root / "tools" / "light_profile_previews" / f"{name}.png"
        data = raw_rgb(path)
        counts[name] = sum(1 for index in range(0, len(data), 3) if data[index] >= 220)

    if not counts["spot_throw"] < counts["spot_balanced"] < counts["spot_flood"]:
        raise RuntimeError(f"unexpected hot-core order: {counts}")


def assert_dds_format(root: Path) -> None:
    for name in PROFILES:
        path = root / "gamedata" / "textures" / "utlf" / "lights" / f"{name}.dds"
        output = subprocess.check_output(["file", str(path)], text=True)
        if "256 x 256" not in output or "DXT1" not in output:
            raise RuntimeError(f"{path} is not reported as 256x256 DXT1: {output.strip()}")


def check(root: Path) -> None:
    missing = [path for path in expected_files(root) if not path.exists()]
    if missing:
        raise RuntimeError("missing generated files: " + ", ".join(str(path) for path in missing))

    with tempfile.TemporaryDirectory(prefix="utlf_light_profiles_check_") as temp_name:
        temp_root = Path(temp_name)
        generate(temp_root)
        mismatches = []
        for current in expected_files(root):
            expected = temp_root / current.relative_to(root)
            if current.suffix == ".png":
                if raw_rgb(current) != raw_rgb(expected):
                    mismatches.append(str(current))
            elif sha256(current) != sha256(expected):
                mismatches.append(str(current))
        if mismatches:
            raise RuntimeError("generated files differ from specs: " + ", ".join(mismatches))

    assert_neutral_pngs(root)
    assert_hot_core_order(root)
    assert_dds_format(root)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="verify generated outputs match the deterministic profile specs",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        if args.check:
            check(ROOT)
            print("UTLF light profile outputs match generator specs.")
        else:
            generate(ROOT)
            print("Generated UTLF light profile masks and previews.")
    except (OSError, RuntimeError, subprocess.CalledProcessError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
