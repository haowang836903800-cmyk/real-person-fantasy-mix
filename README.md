# real-person-fantasy-mix

一个 Codex Skill：把旅行、街拍或生活照片制作成“真实摄影人物与场景 + 二维幻想元素”的混合画面。

它专门解决一个容易发生的风格漂移：幻想元素加入照片后，生成模型常会顺手把真人也画成插画。本 Skill 把真人摄影质感设为最高优先级，并通过空间关系设计、提示词约束和一次有限修正，让幻想层围绕真人与真实物体生长。

## 安装

将仓库目录复制或克隆到 Codex Skills 目录：

```bash
git clone https://github.com/haowang836903800-cmyk/real-person-fantasy-mix.git ~/.codex/skills/real-person-fantasy-mix
```

重新启动或刷新 Codex 后，可显式调用：

```text
用 $real-person-fantasy-mix 处理这张旅行照片，人物保持真人摄影质感。
```

## 输入建议

- 至少一张包含真人与真实场景的清晰照片。
- 可选一张风格参考；它只决定新增插画层，不替换人物身份与场景。
- 需要系列统一时，可把上一张成图作为风格参考，并明确不复制构图。

## 隐私

仓库不包含作者或使用者的原始肖像照片与生成结果。请确认自己有权处理和分享输入图片。

## 许可

MIT。详见 [LICENSE](LICENSE)。
