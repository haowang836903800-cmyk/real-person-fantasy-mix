# 提示词模板

按当前照片具体填写，不机械复制全部字段。

```text
Use case: compositing
Asset type: travel photo with flat 2D fantasy illustration overlays

INPUT ROLES:
Image 1 is the sole edit target and authority for the person, scene and composition.
Image 2, if present, is only a style reference for the new illustration layer. Do not copy its person, clothing, pose, architecture, text or layout.

CRITICAL PERSON LOCK — highest priority:
Keep the photographed person fully realistic and unchanged. Preserve the exact face, skin texture, hair strands, eyewear, clothing fabric and folds, body proportions, pose, hands, feet, crop and original shadow. Do not redraw, stylize, retouch, beautify, replace, move, rescale or outline the person. No fantasy paint may cover identity features or clothing.

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

CONSTRAINTS:
No title, added words, new logos, QR code, watermark or border.
Avoid illustrated person, cartoon skin, painted clothing, changed identity or pose, 3D, clay, vinyl toy, photoreal fantasy creature, white sticker outlines, full-image cartoon conversion and repeated same-size icons.
```

## 人物恢复修正

```text
Image 1 is the current fantasy composite and edit target.
Image 2 is the original photograph and authoritative source for the person.

Restore the entire person from Image 2 into Image 1 as a genuinely photographic, unillustrated subject. Preserve the exact face, hair, skin, eyewear, clothing, limbs, pose, scale, position, crop and original shadow. Remove drawn contours, cel shading, painted texture and cartoon edges from the person.

Keep all satisfactory fantasy elements and the background from Image 1. Move any conflicting fantasy segment behind the restored photographic silhouette. Change nothing else.
```
