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

Tell the user DRE needs to be installed. If they agree, run the following steps in order.
Stop at any step that fails and report the error.

**Step 1 — Check Python:**
```bash
python3 --version || python --version
```
Must be ≥ 3.10. If not found, tell the user to install Python from https://python.org.

**Step 2 — Check git:**
```bash
git --version
```
If not found, tell the user to install git from https://git-scm.com.

**Step 3 — Download & install:**

Via git:
```bash
git clone <DRE_REPO_URL> && cd DRE
pip install -e .
```

Or direct download (no git needed):
```bash
curl -L -o DRE.zip <DRE_REPO_URL>/archive/refs/tags/v0.1.0.zip
unzip DRE.zip && cd DRE-0.1.0
pip install -e .
```

If `pip install -e .` fails with permission errors, retry with `--user`:
```bash
pip install -e . --user
```

**Step 4 — Generate MCP config:**
```bash
python -m dre.cli setup codex    # or: claude, hermes, trae
```

> **OpenClaw 用户注意**: 需要先安装 `openclaw-mcp-adapter` 插件，再运行 `python -m dre.cli setup openclaw`。

**Step 5 — Install the Skill and restart the Agent.**

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

Call `list_templates`. It returns **both** local and marketplace templates in one call:

```json
{
  "local": [ ... ],
  "marketplace": [ ... ],
  "all_names": ["academic", "bid", "compact", "formal", "government", ...]
}
```

- Show the user the most relevant 3-5 options based on their document type
- Match keywords: "投标" → bid/formal, "论文" → academic, "公文" → government, "会议" → minutes, "周报" → weekly_report
- Default to `standard` (or `mac_standard` on macOS)

**If the user picks a marketplace template** (source="marketplace"):
Call `install_template(name)` first, then `render_document`.

### 3. Custom template

If the user wants a style not listed:

> "模板是 YAML 文件，放在 DRE 的 `src/dre/templates/` 目录下就能被识别。"
> "新建 20 行就够了，用 `inherits: standard` 继承，只改你要的字体/字号。"

```bash
cat > src/dre/templates/my_style.yaml << 'EOF'
inherits: standard
name: "我的模板"
description: "仅改正文字体为楷体"
styles:
  body:
    font_name: "KaiTi"
EOF
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
