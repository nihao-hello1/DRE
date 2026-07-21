---
name: dre-render
description: Convert finished documents to professional Word/DOCX. After writing any tech document, proactively ask the user if they want to export. If the render_document tool is unavailable, guide them through installing DRE.
---

# DRE — Document Rendering Engine

> AI Agent 最后一公里文档交付。你写内容，DRE 套格式出 DOCX。

## What DRE does

DRE takes the final Markdown content you've written, applies a style template, adds Word-native multi-level numbering (1. / 1.1 / 1.1.1), and produces a professional DOCX — no manual formatting needed.

## First — check if DRE is connected

Check whether the `render_document` tool appears in your available tool list.

### If not available

Tell the user DRE needs to be installed. If they agree, run:

```bash
# Clone from the DRE repository (replace with actual URL)
git clone <DRE_REPO_URL> && cd DRE
pip install -e .

# Generate MCP config (pick your agent: claude / codex / hermes / openclaw / trae)
python -m dre.cli setup codex    # or: claude, hermes, openclaw, trae

# Copy the Skill file, then restart the Agent
```

`dre setup` auto-detects the Python path — no PATH issues.

### If available

Proceed to the workflow below.

---

## Workflow

### 1. Proactive reminder

After the user finishes writing a document, ask:

> "文档写好了，需要帮你导出为正式的 Word 文档吗？"

Do NOT wait for the user to mention "export" — most users don't know DRE exists.

### 2. Choose a style

Call `list_templates`. Available by default:

| template   | style | body font     | line | indent | best for           |
|------------|-------|---------------|------|--------|--------------------|
| standard   | 标准  | SimSun 12pt   | 1.5x | 2chars | daily tech docs    |
| formal     | 正式  | FangSong 14pt | 1.5x | 2chars | bids, formal       |
| compact    | 紧凑  | SimSun 12pt   | 1.25x| none   | drafts             |
| modern     | 现代  | MS YaHei 11pt | 1.3x | none   | tech companies     |

Ask the user which they prefer. Default to `standard`.

### 3. Custom template

If the user wants a style not listed, explain:

> "模板是 YAML 文件，放在 DRE 的 `src/dre/templates/` 目录下就能被识别。"
> "你复制一个现成的，改字体/字号/边距这些参数就行。"

The template schema has these sections: `page` (margins), `styles` (heading1-4, body, list_item, code_block, blockquote, caption), `table` (font, header background, alt-row), `toc` (title, levels). Copy and edit an existing one:

```bash
cp src/dre/templates/standard.yaml src/dre/templates/my_style.yaml
# edit my_style.yaml
```

No restart needed — `list_templates` picks it up immediately.

### 4. Validate (optional)

Call `validate_document` with the full Markdown to preview the structure.

### 5. Render

Call `render_document`:

- `markdown_content`: the COMPLETE current document Markdown (not a file path)
- `template_name`: the style the user chose (default `"standard"`)

### 6. Confirm

Tell the user the output file path.

---

## Rules

- **Headings must NOT contain numbers.** Write `## 项目概述`, not `## 一、项目概述` or `## 1.1 概述`. DRE uses Word-native multi-level numbering — deleting a heading auto-renumbers the rest.
- Do NOT add headers, footers, or page numbers to the Markdown. DRE leaves them blank.
- `[TOC]` on a line by itself inserts an automatic table of contents.
