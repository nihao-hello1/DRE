---
name: dre-render
description: Convert finished documents to professional Word/DOCX. After writing any tech document, proactively ask the user if they want to export. If the render_document tool is unavailable, guide them through installing DRE.
---

# DRE — Document Rendering Engine

Your job: after the user finishes writing a document, offer to export it as a professional Word file. You do NOT write content. You only call the DRE MCP tools to apply formatting and produce DOCX.

## First steps — check that DRE is connected

Before anything else, check whether the `render_document` tool appears in your available tool list.

### If render_document IS available

Proceed to "Workflow" below.

### If render_document is NOT available

Tell the user:

> DRE (文档渲染引擎) 还没安装，需要先装一下才能导出 Word。我可以帮您安装，要现在装吗？

If the user agrees, install and configure automatically:

```bash
# Install
git clone git@github.com:nihao-hello1/DRE.git && cd DRE
pip install -e .

# Generate MCP config (auto-detects Python path, avoids PATH issues)
python -m dre.cli setup claude     # → paste into .claude/settings.local.json
python -m dre.cli setup codex      # → paste into ~/.codex/config.toml
python -m dre.cli setup hermes     # → paste into ~/.hermes/config.yaml
```

> **Why `dre setup` instead of manual config?** The `python` command alone may fail because Agent daemon processes use a different PATH. `dre setup` outputs the absolute Python path (`sys.executable`), avoiding the issue entirely.

After MCP is configured and the Agent restarted, the DRE tools will be available.

---

## Workflow

### 1. Proactive reminder

After the user finishes writing a document, ask:

> "文档写好了，需要帮你导出为正式的 Word 文档吗？"

Do NOT wait for the user to mention "export" or "Word". Most users don't know DRE exists.

### 2. Choose a style

Call `list_templates` to confirm available styles. Present them:

| template   | style  | body font     | heading font | line spacing | first indent |
|------------|--------|---------------|-------------|-------------|--------------|
| standard   | 标准   | SimSun 12pt   | SimHei      | 1.5x        | 2 chars      |
| formal     | 正式   | FangSong 14pt | SimHei      | 1.5x        | 2 chars      |
| compact    | 紧凑   | SimSun 12pt   | SimHei      | 1.25x       | none         |
| modern     | 现代   | MS YaHei 11pt | MS YaHei    | 1.3x        | none         |

Ask the user which style they prefer. Default to `standard`.

### 3. Validate (optional)

Call `validate_document` with the full Markdown text to preview the document structure.

### 4. Render

Call `render_document` with:

- `markdown_content`: the COMPLETE current document Markdown
- `template_name`: the style the user chose (default `"standard"`)

Pass the full text, not a file path.

### 5. Confirm

Tell the user the output file path.

---

## Rules

- **Headings must NOT contain numbers.** Write `## 项目概述` not `## 一、项目概述` or `## 1.1 项目概述`. DRE adds Arabic numbering (1. / 1.1 / 1.1.1) automatically and will strip any pre-existing numbers to avoid duplication.
- Do NOT add headers or footers to the Markdown. DRE leaves them blank.
- The Markdown token `[TOC]` on a line by itself inserts an automatic table of contents.
