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

REQUIRED_STORY_FIELDS = ("verb", "fantasy_event", "visual_path", "person_relation")
MIN_MAIN_ALPHA_FRACTION = 0.025
MIN_TOTAL_ALPHA_FRACTION = 0.04
MIN_MAIN_WIDTH_FRACTION = 0.28
MIN_MAIN_HEIGHT_FRACTION = 0.22


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


def validate_fantasy_plan(manifest: dict, items: list[dict]) -> dict:
    story = manifest.get("story") or {}
    missing_story = [field for field in REQUIRED_STORY_FIELDS if not str(story.get(field, "")).strip()]
    if missing_story:
        fail(f"story is missing required fields: {missing_story}")
    if not str(manifest.get("style_group", "")).strip():
        fail("manifest needs one non-empty style_group for the complete fantasy layer")

    roles = {"main": [], "support": [], "detail": []}
    physical_items: list[str] = []
    for index, item in enumerate(items):
        name = item.get("name") or f"asset-{index + 1}"
        role = item.get("role")
        if role not in roles:
            fail(f"asset {name} needs role: main, support or detail")
        roles[role].append(name)
        if not str(item.get("anchor", "")).strip():
            fail(f"asset {name} needs a real-scene anchor description")
        if not str(item.get("narrative_relation", "")).strip():
            fail(f"asset {name} needs narrative_relation")
        if item.get("shadow") or item.get("occlusion_masks"):
            physical_items.append(name)

    if len(roles["main"]) != 1:
        fail(f"fantasy layer needs exactly one main asset, found {len(roles['main'])}")
    if not 4 <= len(roles["support"]) <= 6:
        fail(f"fantasy layer needs 4-6 support assets, found {len(roles['support'])}")
    if len(physical_items) < 3:
        fail(
            "fantasy layer needs at least three assets with real occlusion or contact shadow; "
            f"found {physical_items}"
        )

    main_item = next(item for item in items if item.get("role") == "main")
    main_name = main_item.get("name") or "main"
    if not str(main_item.get("impossible_change", "")).strip():
        fail(f"main asset {main_name} needs impossible_change")
    if not (main_item.get("shadow") or main_item.get("occlusion_masks")):
        fail(f"main asset {main_name} must touch a real surface or be occluded by a real structure")

    return {
        "story": {field: str(story[field]).strip() for field in REQUIRED_STORY_FIELDS},
        "style_group": str(manifest["style_group"]).strip(),
        "main_asset": main_name,
        "support_assets": roles["support"],
        "physical_integration_assets": physical_items,
    }


def nonzero_alpha_pixels(image: Image.Image) -> int:
    histogram = image.getchannel("A").histogram()
    return image.width * image.height - histogram[0]


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
    fantasy_plan = validate_fantasy_plan(manifest, items)
    main_visible_pixels = 0
    main_placement: list[int] | None = None

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

        if item.get("role") == "main":
            width_fraction = asset.width / width
            height_fraction = asset.height / height
            if width_fraction < MIN_MAIN_WIDTH_FRACTION and height_fraction < MIN_MAIN_HEIGHT_FRACTION:
                fail(
                    f"main asset {name} is too small for a thumbnail-visible fantasy event: "
                    f"width={width_fraction:.3f}, height={height_fraction:.3f}; need width >= "
                    f"{MIN_MAIN_WIDTH_FRACTION:.2f} or height >= {MIN_MAIN_HEIGHT_FRACTION:.2f}"
                )

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
        visible_pixels = nonzero_alpha_pixels(layer)
        if item.get("role") == "main":
            main_visible_pixels = visible_pixels
            main_placement = [x, y, asset.width, asset.height]
        canvas = Image.alpha_composite(canvas, layer)
        report_items.append(
            {
                "name": name,
                "role": item["role"],
                "space": item["space"],
                "depth": depth,
                "placement": [x, y, asset.width, asset.height],
                "visible_alpha_pixels": visible_pixels,
                "integration_mechanisms": mechanisms,
            }
        )

    canvas_pixels = width * height
    main_alpha_fraction = main_visible_pixels / canvas_pixels
    total_alpha_fraction = nonzero_alpha_pixels(canvas) / canvas_pixels
    if main_alpha_fraction < MIN_MAIN_ALPHA_FRACTION:
        fail(
            f"main asset remains too visually weak after occlusion: alpha_fraction={main_alpha_fraction:.4f}, "
            f"need >= {MIN_MAIN_ALPHA_FRACTION:.4f}"
        )
    if total_alpha_fraction < MIN_TOTAL_ALPHA_FRACTION:
        fail(
            f"fantasy layer is too sparse: alpha_fraction={total_alpha_fraction:.4f}, "
            f"need >= {MIN_TOTAL_ALPHA_FRACTION:.4f}"
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(args.output, format="PNG", optimize=True)
    report = {
        "status": "PASS",
        "output": str(args.output),
        "canvas": [width, height],
        "fantasy_impact": {
            "status": "PASS",
            **fantasy_plan,
            "main_placement": main_placement,
            "main_alpha_fraction": round(main_alpha_fraction, 6),
            "total_alpha_fraction": round(total_alpha_fraction, 6),
        },
        "assets": report_items,
    }
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
