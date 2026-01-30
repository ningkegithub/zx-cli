---
name: ppt_master
description: 将 Markdown 格式的大纲转换为 PowerPoint (.pptx) 演示文稿。
---

# PPT 渲染大师 (PPT Master)

此技能负责将结构化的 Markdown 内容渲染为可编辑的 PowerPoint 文件。

## 🌟 核心功能
- **自动化排版**：自动识别 Markdown 标题并创建对应幻灯片。
- **模板支持**：支持基于默认模板或自定义模板生成。
- **演讲备注**：自动将 `Speaker Notes` 写入 PPT 备注栏。

## 📝 Markdown 格式要求
为了获得最佳效果，Markdown 应遵循以下格式：
```markdown
---
## Slide 1｜封面标题
- 副标题或要点
**Speaker Notes：**
- 演讲备注内容
---
## Slide 2｜目录
- 第一章
- 第二章
```

## 🚀 使用方法

### 基础转换（使用默认空白模板）
```bash
python3 {SKILL_DIR}/scripts/md2pptx.py input.md output.pptx
```

### 专业转换（使用企业模板 - 推荐 🌟）
通过 `--template` 参数指定公司母版。
*金蝶模板默认路径*: `skills/ppt_master/templates/2024金蝶集团PPT模板.pptx`

```bash
python3 {SKILL_DIR}/scripts/md2pptx.py result.md my_ppt.pptx --template skills/ppt_master/templates/2024金蝶集团PPT模板.pptx
```


