# 提示词模板

按当前照片具体填写，不机械复制全部字段。

```text
Use case: compositing
Asset type: travel photo with flat 2D fantasy illustration overlays

INPUT ROLES:
Image 1 is the sole edit target and authority for the person, scene and composition.
Image 2, if present, is only a style reference for the new illustration layer. Do not copy its person, clothing, pose, architecture, text or layout.

CRITICAL PERSON LOCK — highest priority:
Keep the actual photographed person from Image 1, not a regenerated likeness. Preserve the source pixels and exact face, pores and skin texture, hair strands and hairline, eyewear, clothing fabric, folds and patterns, body proportions, pose, hands, feet, crop and original shadow. Do not redraw, reconstruct, stylize, retouch, beautify, denoise, relight, replace, move, rescale or outline the person. Do not synthesize new pixels inside the protected person silhouette. If masking or layered compositing is available, exclude the person and original shadow from generative editing and composite the original photographic pixels back on top. No fantasy paint may cover identity features, skin or clothing.

PERMITTED COLOR WORK:
Restrained global color grading is allowed: white balance, exposure, contrast, curves, color tone, saturation and grain may be adjusted consistently across the photograph. Apply only the same non-generative color transform to the original person pixels. Preserve local skin shading, pores, hair, fabric, camera noise, sharpness and depth of field. No local beauty filter, skin smoothing, face enhancement, invented rim light or portrait relighting.

SCENE LOCK:
Preserve [list 3–5 actual anchors], perspective, lighting, weather, depth of field and photographic textures. Do not globally repaint the photograph.

LARGE FANTASY SUBJECT:
[one scene-specific subject, location, scale, palette and movement]

MEDIUM STORY ELEMENTS:
1) ...
2) ...
3) ...
4) ...
5) ...

REQUIRED SPATIAL RELATIONSHIPS:
A) [element] passes behind [real object/person] and reappears at [location].
B) [character] is partly occluded by [actual rail/rock/wall].
C) [plant/path] grows from [actual surface] and alternates front/back.

STYLE:
Only new fantasy elements are flat 2D editorial illustration: clean contours, opaque solid colors, minimal cel shading and optional restrained print grain. The person and environment remain photography.

OPTIONAL AESTHETIC MODE:
When routed to `luminous-cinematic-wonder.md`, insert its compact module here after adapting it to the photograph. Omit this block for scenes that do not qualify; never use an artist name as a shortcut.

CONSTRAINTS:
No title, added words, new logos, QR code, watermark or border.
Avoid illustrated person, cartoon skin, painted clothing, changed identity or pose, 3D, clay, vinyl toy, photoreal fantasy creature, white sticker outlines, full-image cartoon conversion and repeated same-size icons.
```

## 人物恢复修正

```text
Image 1 is the current fantasy composite and edit target.
Image 2 is the original photograph and authoritative source for the person.

Do not regenerate, reconstruct or enhance the person. Use a mask to composite the original person pixels and original shadow from Image 2 back into Image 1. Preserve the exact face, pores, hair strands, skin, eyewear, clothing texture and folds, limbs, pose, scale, position, crop, sharpness, depth of field, grain and camera noise. Remove any generated person pixels, beauty retouching, drawn contours, cel shading, painted texture, invented light and cartoon edges.

Keep all satisfactory fantasy elements and the background from Image 1. Move any conflicting fantasy segment behind the restored original photographic silhouette. A restrained global color grade may be applied consistently after compositing; do not locally retouch the person. Change nothing else.
```
