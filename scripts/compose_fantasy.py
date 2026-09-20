#!/usr/bin/env python3
"""Losslessly restore protected source-photo pixels while compositing RGBA fantasy layers."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    from PIL import Image, ImageChops, ImageFilter, ImageOps
except ImportError as exc:  # pragma: no cover - dependency message is the behavior
    raise SystemExit("Pillow is required: python3 -m pip install Pillow") from exc


def fail(message: str) -> "NoReturn":
    raise SystemExit(f"error: {message}")


def open_oriented(path: Path) -> Image.Image:
    try:
        with Image.open(path) as image:
            return ImageOps.exif_transpose(image).copy()
    except Exception as exc:
        fail(f"cannot decode {path}: {exc}")


def load_mask(path: Path, size: tuple[int, int]) -> Image.Image:
    mask = open_oriented(path).convert("L")
    if mask.size != size:
        fail(f"mask {path} is {mask.size}, expected {size}; do not resize a protection mask implicitly")
    return mask.point(lambda value: 255 if value >= 128 else 0, mode="L")


def union_masks(masks: list[Image.Image], size: tuple[int, int], dilation: int) -> Image.Image:
    result = Image.new("L", size, 0)
    for mask in masks:
        result = ImageChops.lighter(result, mask)
    if dilation:
        result = result.filter(ImageFilter.MaxFilter(dilation * 2 + 1))
    return result.point(lambda value: 255 if value else 0, mode="L")


def load_overlay(path: Path, size: tuple[int, int], max_coverage: float) -> tuple[Image.Image, float]:
    overlay = open_oriented(path)
    if overlay.size != size:
        fail(f"overlay {path} is {overlay.size}, expected {size}; align it before compositing")
    if "A" not in overlay.getbands():
        fail(f"overlay {path} has no alpha channel; it must be a transparent PNG")
    overlay = overlay.convert("RGBA")
    alpha = overlay.getchannel("A")
    histogram = alpha.histogram()
    visible = sum(histogram[1:])
    coverage = visible / (size[0] * size[1])
    if coverage > max_coverage:
        fail(
            f"overlay {path} covers {coverage:.1%} of the canvas, above the "
            f"{max_coverage:.1%} safety limit; probable full-frame generation"
        )
    return overlay, coverage


def restore_source(result: Image.Image, source: Image.Image, protected: Image.Image) -> Image.Image:
    return Image.composite(source, result, protected)


def changed_inside_mask(source: Image.Image, result: Image.Image, protected: Image.Image) -> bool:
    difference = ImageChops.difference(source, result)
    for channel in difference.split():
        if ImageChops.multiply(channel, protected).getbbox() is not None:
            return True
    return False


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Composite transparent fantasy layers while preserving protected source pixels exactly."
    )
    parser.add_argument("--base", required=True, type=Path, help="authoritative original photograph")
    parser.add_argument("--person-mask", required=True, type=Path, help="white person / black background mask")
    parser.add_argument("--protect-mask", action="append", default=[], type=Path, help="additional white protected area")
    parser.add_argument("--back", action="append", default=[], type=Path, help="RGBA fantasy layer behind the person")
    parser.add_argument("--front", action="append", default=[], type=Path, help="RGBA foreground layer; clipped away from protected pixels")
    parser.add_argument("--output", required=True, type=Path, help="lossless .png output")
    parser.add_argument("--report", type=Path, help="optional JSON verification report")
    parser.add_argument("--dilate", type=int, default=2, help="expand protected masks by this many pixels (default: 2)")
    parser.add_argument(
        "--max-overlay-coverage",
        type=float,
        default=0.60,
        help="reject an overlay covering more than this canvas fraction (default: 0.60)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.output.suffix.lower() != ".png":
        fail("output must be PNG; JPEG cannot preserve protected pixels exactly")
    if args.dilate < 0 or args.dilate > 50:
        fail("--dilate must be between 0 and 50")
    if not 0 < args.max_overlay_coverage <= 1:
        fail("--max-overlay-coverage must be in (0, 1]")
    if not args.back and not args.front:
        fail("provide at least one --back or --front transparent fantasy layer")

    source = open_oriented(args.base).convert("RGBA")
    masks = [load_mask(args.person_mask, source.size)]
    masks.extend(load_mask(path, source.size) for path in args.protect_mask)
    protected = union_masks(masks, source.size, args.dilate)

    result = source.copy()
    coverages: dict[str, float] = {}

    for path in args.back:
        layer, coverage = load_overlay(path, source.size, args.max_overlay_coverage)
        coverages[str(path)] = coverage
        result = Image.alpha_composite(result, layer)

    result = restore_source(result, source, protected)

    for path in args.front:
        layer, coverage = load_overlay(path, source.size, args.max_overlay_coverage)
        coverages[str(path)] = coverage
        safe_alpha = ImageChops.multiply(layer.getchannel("A"), ImageOps.invert(protected))
        layer.putalpha(safe_alpha)
        result = Image.alpha_composite(result, layer)

    result = restore_source(result, source, protected)
    if changed_inside_mask(source, result, protected):
        fail("protected pixels changed; refusing to write a false-preservation result")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    result.save(args.output, format="PNG", optimize=True)

    protected_pixels = protected.histogram()[255]
    report = {
        "status": "PASS",
        "output": str(args.output),
        "dimensions": list(source.size),
        "protected_pixels": protected_pixels,
        "changed_protected_pixels": 0,
        "protected_pixels_exact": True,
        "overlay_coverage": coverages,
    }
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
