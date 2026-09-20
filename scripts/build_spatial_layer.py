#!/usr/bin/env python3
"""Build a canvas-aligned RGBA fantasy layer from a spatial placement manifest."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    from PIL import Image, ImageChops, ImageColor, ImageDraw, ImageEnhance, ImageFilter, ImageOps
except ImportError as exc:  # pragma: no cover
    raise SystemExit("Pillow is required: python3 -m pip install Pillow") from exc


DEPTH_DEFAULTS = {
    "far": {"opacity": 0.82, "blur": 0.8, "saturation": 0.82},
    "mid": {"opacity": 0.94, "blur": 0.25, "saturation": 0.94},
    "near": {"opacity": 1.0, "blur": 0.0, "saturation": 1.0},
}


def fail(message: str) -> "NoReturn":
    raise SystemExit(f"error: {message}")


def load_image(path: Path) -> Image.Image:
    try:
        with Image.open(path) as image:
            return ImageOps.exif_transpose(image).copy()
    except Exception as exc:
        fail(f"cannot decode {path}: {exc}")


def resolve(root: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else root / path


def validate_isolated_asset(asset: Image.Image, name: str, allow_border_touch: bool) -> None:
    if "A" not in asset.getbands():
        fail(f"asset {name} has no alpha channel")
    bbox = asset.getchannel("A").getbbox()
    if bbox is None:
        fail(f"asset {name} is fully transparent")
    if not allow_border_touch:
        left, top, right, bottom = bbox
        if left == 0 or top == 0 or right == asset.width or bottom == asset.height:
            fail(
                f"asset {name} touches its source-image border; probable crop or background residue. "
                "Regenerate it with transparent margin."
            )


def apply_tint(image: Image.Image, color: str | None, strength: float) -> Image.Image:
    if not color or strength <= 0:
        return image
    if not 0 <= strength <= 1:
        fail("tint_strength must be between 0 and 1")
    alpha = image.getchannel("A")
    rgb = image.convert("RGB")
    tint = Image.new("RGB", image.size, ImageColor.getrgb(color))
    rgb = Image.blend(rgb, tint, strength)
    rgb.putalpha(alpha)
    return rgb


def apply_opacity(image: Image.Image, opacity: float) -> Image.Image:
    if not 0 <= opacity <= 1:
        fail("opacity must be between 0 and 1")
    alpha = image.getchannel("A").point(lambda value: round(value * opacity))
    image.putalpha(alpha)
    return image


def load_canvas_mask(path: Path, size: tuple[int, int]) -> Image.Image:
    mask = load_image(path).convert("L")
    if mask.size != size:
        fail(f"occlusion mask {path} is {mask.size}, expected canvas {size}")
    return mask


def validate_integration(item: dict, name: str) -> list[str]:
    space = item.get("space")
    if space not in {"sky", "ground", "ledge", "wall", "behind_structure"}:
        fail(f"asset {name} needs space: sky, ground, ledge, wall or behind_structure")
    mechanisms: list[str] = []
    if item.get("shadow"):
        mechanisms.append("contact_shadow")
    if item.get("occlusion_masks"):
        mechanisms.append("real_structure_occlusion")
    if item.get("tint"):
        mechanisms.append("local_color_adaptation")
    if item.get("depth"):
        mechanisms.append("depth_treatment")
    if space in {"ground", "ledge"} and not item.get("shadow"):
        fail(f"asset {name} is on {space} but has no contact shadow")
    if space == "behind_structure" and not item.get("occlusion_masks"):
        fail(f"asset {name} is behind_structure but has no occlusion mask")
    if space == "wall" and not (item.get("shadow") or item.get("occlusion_masks")):
        fail(f"asset {name} is on a wall but has neither attachment shadow nor occlusion mask")
    if len(mechanisms) < 2:
        fail(f"asset {name} needs at least two integration mechanisms, found {mechanisms}")
    return mechanisms


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Place isolated fantasy assets using an integration manifest.")
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path, help="canvas-aligned RGBA PNG")
    parser.add_argument("--report", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.output.suffix.lower() != ".png":
        fail("output must be PNG")
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    root = args.manifest.parent
    width = int(manifest["canvas"]["width"])
    height = int(manifest["canvas"]["height"])
    if width <= 0 or height <= 0:
        fail("invalid canvas dimensions")
    canvas = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    report_items = []

    items = manifest.get("assets") or []
    if not items:
        fail("manifest contains no assets")

    for index, item in enumerate(items):
        name = item.get("name") or f"asset-{index + 1}"
        mechanisms = validate_integration(item, name)
        source_path = resolve(root, item["path"])
        asset = load_image(source_path)
        validate_isolated_asset(asset, name, bool(item.get("allow_border_touch", False)))
        asset = asset.convert("RGBA")

        target_width = int(item["width"])
        if target_width <= 0:
            fail(f"asset {name} has invalid width")
        target_height = int(item.get("height") or round(asset.height * target_width / asset.width))
        if target_height <= 0:
            fail(f"asset {name} has invalid height")
        asset = asset.resize((target_width, target_height), Image.Resampling.LANCZOS)
        if item.get("mirror"):
            asset = ImageOps.mirror(asset)

        depth = item.get("depth", "mid")
        if depth not in DEPTH_DEFAULTS:
            fail(f"asset {name} has invalid depth {depth}")
        defaults = DEPTH_DEFAULTS[depth]
        saturation = float(item.get("saturation", defaults["saturation"]))
        rgb = ImageEnhance.Color(asset.convert("RGB")).enhance(saturation)
        rgb.putalpha(asset.getchannel("A"))
        asset = rgb
        asset = apply_tint(asset, item.get("tint"), float(item.get("tint_strength", 0.0)))

        blur = float(item.get("blur", defaults["blur"]))
        if blur < 0 or blur > 10:
            fail(f"asset {name} blur must be between 0 and 10")
        if blur:
            asset = asset.filter(ImageFilter.GaussianBlur(blur))
        asset = apply_opacity(asset, float(item.get("opacity", defaults["opacity"])))

        rotation = float(item.get("rotation", 0.0))
        if rotation:
            asset = asset.rotate(rotation, resample=Image.Resampling.BICUBIC, expand=True)

        x = int(item["x"])
        y = int(item["y"])
        if x >= width or y >= height or x + asset.width <= 0 or y + asset.height <= 0:
            fail(f"asset {name} lies outside the canvas")

        shadow = item.get("shadow")
        if shadow:
            shadow_layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
            shadow_alpha = Image.new("L", canvas.size, 0)
            draw = ImageDraw.Draw(shadow_alpha)
            ellipse = tuple(int(value) for value in shadow["ellipse"])
            draw.ellipse(ellipse, fill=round(255 * float(shadow.get("opacity", 0.18))))
            shadow_alpha = shadow_alpha.filter(ImageFilter.GaussianBlur(float(shadow.get("blur", 8.0))))
            color = ImageColor.getrgb(shadow.get("color", "#1b1b1b"))
            shadow_layer.paste((*color, 255), (0, 0, width, height), shadow_alpha)
            canvas = Image.alpha_composite(canvas, shadow_layer)

        layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        layer.alpha_composite(asset, (x, y))
        for mask_value in item.get("occlusion_masks", []):
            mask = load_canvas_mask(resolve(root, mask_value), canvas.size)
            layer.putalpha(ImageChops.multiply(layer.getchannel("A"), ImageOps.invert(mask)))
        canvas = Image.alpha_composite(canvas, layer)
        report_items.append(
            {
                "name": name,
                "space": item["space"],
                "depth": depth,
                "placement": [x, y, asset.width, asset.height],
                "integration_mechanisms": mechanisms,
            }
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(args.output, format="PNG", optimize=True)
    report = {"status": "PASS", "output": str(args.output), "canvas": [width, height], "assets": report_items}
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
