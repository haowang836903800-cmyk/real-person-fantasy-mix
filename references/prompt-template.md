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
[one complete impossible event, not a list of objects: subject + impossible change + real-scene anchor + real occlusion/contact + relation to the photographed person. After placement its bounding box must span at least 28% of canvas width or 22% of canvas height, and remain recognizable in a 25% thumbnail. Do not copy the subject matter of a style reference]

SCENE-SPECIFIC VISUAL BLUEPRINT:
Story verb: [meeting / departure / guiding / waiting / crossing / returning / another scene-specific action]
Material relationship: [how the fantasy subject borrows shape, color or motion from actual cloud / water / foliage / architecture / steam / food]
Visual path: [a continuous curve, light route, procession or gaze path that leads from the main wonder back to the photographed person]
Depth plan: [foreground real contact] / [midground person interaction] / [background main wonder]
Density map: [highest-detail zones] / [medium-detail connectors] / [quiet negative space]
Single light event: [one event consistent with the source-photo light direction]

MEDIUM STORY ELEMENTS:
1) ...
2) ...
3) ...
4) ...
5) ...

FANTASY IMPACT GATE:
There must be exactly one dominant main wonder and 4–6 supporting story groups. At least three different fantasy objects must physically contact a real surface or be occluded by a real structure. Color matching, blur, opacity, glow and scattered particles do not count as physical integration. A normal-sized tram, paper planes and light dots floating separately are decorative stickers, not a fantasy event. The result must communicate one impossible on-location event within three seconds at thumbnail size.

REQUIRED SPATIAL RELATIONSHIPS:
A) [element] passes behind [real object/person] and reappears at [location].
B) [character] is partly occluded by [actual rail/rock/wall].
C) [plant/path] grows from [actual surface] and alternates front/back.

STYLE:
Only new fantasy elements use cinematic 2D hand-painted editorial illustration: clear large shapes, clean contours, layered cel painting, controlled soft gradients, optional restrained grain, and a four-part light structure of base color, lit plane, shadow plane and translucent/highlight accent. Focus and contact edges are crisp; distant and backlit edges are softer. The person and environment remain photography.

OPTIONAL AESTHETIC MODE:
When routed to `luminous-cinematic-wonder.md`, insert its compact module here after adapting it to the photograph. Omit this block for scenes that do not qualify; never use an artist name as a shortcut.

CONSTRAINTS:
No title, added words, new logos, QR code, watermark or border.
Avoid illustrated person, beauty-poster face, cartoon skin, painted clothing, changed identity or pose, 3D, clay, vinyl toy, glass or golden-wireframe fantasy subject, game-effect light trails, webtoon or motion-comic poster aesthetics, photoreal fantasy creature, white sticker outlines, full-image cartoon conversion and repeated same-size icons.
```

## 人物恢复修正

```text
Image 1 is the current fantasy composite and edit target.
Image 2 is the original photograph and authoritative source for the person.

Do not regenerate, reconstruct or enhance the person. Use a mask to composite the original person pixels and original shadow from Image 2 back into Image 1. Preserve the exact face, pores, hair strands, skin, eyewear, clothing texture and folds, limbs, pose, scale, position, crop, sharpness, depth of field, grain and camera noise. Remove any generated person pixels, beauty retouching, drawn contours, cel shading, painted texture, invented light and cartoon edges.

Keep all satisfactory fantasy elements and the background from Image 1. Move any conflicting fantasy segment behind the restored original photographic silhouette. A restrained global color grade may be applied consistently after compositing; do not locally retouch the person. Change nothing else.
```

## 豆包独立素材表模板

豆包增量模式不能直接使用完整场景提示词生成最终画面。先根据蓝图生成一张统一素材表，再使用空间清单放置：

```text
使用当前可用的最新高质量静态生图模型，只生成一张二维手绘幻想素材表，不生成完整场景，不重绘用户照片。

本素材表包含：恰好一个【大型主奇观】和【中型元素 1】至【中型元素 4—6】。大型主奇观必须表现【填写不可能变化】，不是普通物件或正常交通工具的孤立图标。所有对象属于同一套视觉体系：相同线条粗细、相同四层光色、相同笔触密度、相同成熟度、相同光源方向，色板取自原照片的【环境色】并使用【强调色】。采用高清二维手绘电影光色，清楚大形、细腻色阶、焦点边缘清楚、背光边缘柔和；不是儿童绘本、漫剧贴纸、网文海报、折纸素材包或 3D 游戏资产。

每个对象完整显示，彼此不接触、不重叠，四周至少保留对象宽度 10% 的透明余量。输出真正透明的 RGBA PNG；透明区域不得包含渐变底色、粉色底、白底、烟雾、光斑或场景纹理。对象底部必须自然完整，不得出现水平裁切线或矩形画布边。只绘制对象自身，不绘制街道、建筑、天空、山、水、路人、原照片人物、展示台、边框、标题或说明文字。

对象的接触阴影不要画进素材，由合成阶段根据真实落点添加。需要发光的对象只保留贴近形体的局部亮边，不生成大面积背景光晕。
```

若工具不能输出真正透明 PNG，可改用完全均匀的单色背景，但必须明确“纯色、无渐变、无纹理、无投影、无环境光晕”；去背后逐个检查边缘。出现粉色渐变、背景残留、彩边或透明噪点时整张素材表失败，不能继续合成。
