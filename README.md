# DRE — Document Rendering Engine

**让 AI Agent 写完的文档，一键导出为可直接交付的专业 Word 文件。**

AI 负责写内容，DRE 负责排版——字体、字号、行距、多级编号、目录、页眉页码，全部自动完成。十个模板开箱即用，无需手动排版。

---

## 安装

```bash
git clone https://github.com/nihao-hello1/DRE.git
cd DRE
pip install -e .
```

## 配置

```bash
# 生成 MCP 配置
python -m dre.cli setup claude     # Claude Code
python -m dre.cli setup codex      # Codex CLI
python -m dre.cli setup hermes     # Hermes

# 安装 Skill
cp -r skills/dre-render ~/.claude/skills/dre-render
```

| Agent | 配置方式 |
|-------|---------|
| Claude Code | 运行 `dre setup claude` 输出的 `claude mcp add` 命令 |
| Codex CLI | `dre setup codex` → 复制 TOML 到 `~/.codex/config.toml` |
| Hermes | `dre setup hermes` → 复制 YAML 到 `~/.hermes/config.yaml` |

配置后重启 Agent 即可使用。

---

## 可用模板（10 个，全部内置）

| 模板 | 正文 | 行距 | 首行缩进 | 适用场景 |
|:-----|:-----|:-----|:---------|:---------|
| `standard` | SimSun 12pt | 1.5x | 2 字符 | 技术文档（默认） |
| `formal` | FangSong 14pt | 1.5x | 2 字符 | 投标文件、正式报告 |
| `compact` | SimSun 12pt | 1.25x | 无 | 草稿、内部审核 |
| `modern` | MS YaHei 11pt | 1.3x | 无 | 科技公司、屏幕阅读 |
| `mac_standard` | STSongti-SC 12pt | 1.5x | 2 字符 | macOS |
| `academic` | SimSun 12pt | 1.5x | 2 字符 | GB/T 7713.1 学位论文 |
| `bid` | FangSong 14pt | 1.5x | 2 字符 | 招投标文档 |
| `government` | FangSong 16pt | 1.5x | 2 字符 | GB/T 9704 党政公文 |
| `minutes` | SimSun 12pt | 1.5x | 2 字符 | 会议纪要 |
| `weekly_report` | SimSun 12pt | 1.25x | 无 | 周报 / 月报 |

---

## 使用方式

### Agent 工作流

Skill 安装后，Agent 在文档撰写完成时会提示导出。标题无需手动编号——DRE 使用 Word 原生多级编号。

### CLI

```bash
dre render input.md -t standard -o output.docx
dre render input.md -t formal -o output.docx
dre validate input.md
dre list-templates
dre show-template standard
```

---

## MCP 工具

| 工具 | 说明 |
|:----|:-----|
| `list_templates()` | 列出可用模板 |
| `install_template(name)` | 从市场安装新模板 |
| `render_document(markdown, template)` | 渲染 Markdown → DOCX |
| `validate_document(markdown)` | 校验文档结构 |
| `document_info(path)` | 查看已渲染文档信息 |

---

## CLI 命令

```bash
dre render input.md -t <name> -o out.docx  # 渲染 DOCX
dre list-templates                          # 列出模板
dre show-template <name>                    # 查看模板详情
dre validate input.md                       # 校验文档结构
dre setup <agent>                           # 生成 MCP 配置
dre template search <keyword>               # 搜索市场模板
dre template install <name>                 # 安装市场模板
dre toc-refresh <file.docx>                 # 刷新目录页码（需 OfficeCLI）
```

---

## 自定义模板

模板为 YAML 文件，置于 `src/dre/templates/` 目录即可被识别。推荐使用 `inherits` 继承已有模板，只写差异项：

```yaml
# 仅 7 行，继承 standard 全部默认值，只改左边距
inherits: standard
name: "学术论文"
page:
  margins:
    left: "3.5cm"
```

### 完整模板结构

```yaml
inherits: standard          # 继承父模板（可选）
name: "我的模板"
description: "自定义样式"

page:
  size: A4
  margins:
    top: "2.54cm"
    bottom: "2.54cm"
    left: "3.17cm"
    right: "3.17cm"

styles:
  heading1:
    font_name: "SimHei"
    font_size: "16pt"
    bold: true
    alignment: left
    line_spacing: 1.5
    outline_level: 1
  heading2:
    font_name: "SimHei"
    font_size: "14pt"
    bold: true
  heading3:
    font_name: "SimHei"
    font_size: "13pt"
    bold: true
  heading4:
    font_name: "SimHei"
    font_size: "12pt"
    bold: true
  body:
    font_name: "SimSun"
    font_size: "12pt"
    line_spacing: 1.5
    first_line_indent: "0.74cm"
  list_item:
    font_name: "SimSun"
    font_size: "12pt"
    line_spacing: 1.5
  code_block:
    font_name: "Consolas"
    font_size: "10pt"
    line_spacing: 1.2
  blockquote:
    font_name: "SimSun"
    font_size: "11pt"
    italic: true
  caption:
    font_name: "SimSun"
    font_size: "10.5pt"

table:
  font_name: "SimSun"
  font_size: "10.5pt"
  header_bg: "4472C4"
  header_font_color: "FFFFFF"
  row_alt_color: "F2F2F2"

numbering:
  enabled: true
  mode: chapter             # sequential | chapter
  figures:
    prefix: "图"
  tables:
    prefix: "表"

toc:
  title: "目  录"
  levels: 3
```

---

## 功能

**图表自动编号** — 配置 `numbering` 段后，渲染时自动生成"图 1-1"格式编号。`sequential` 模式全文连续编号；`chapter` 模式按章重置。

**模板继承** — `inherits` 字段指定父模板，子模板只声明覆盖项。支持递归继承，带循环检测。

**TOC 自刷新** — 目录域代码在 DOCX 中正确插入，打开文档后 **Ctrl+A → F9** 刷新页码。OfficeCLI 为可选后处理。

**模板市场** — `dre template search` 搜索、`dre template install` 安装社区贡献的额外模板（10 个内置模板已覆盖常见场景）。

---

## 项目结构

```
DRE/
├── skills/dre-render/SKILL.md   # Agent Skill
├── src/dre/
│   ├── mcp_server/              # FastMCP Server（5 个工具）
│   ├── renderer/                # DOCX 渲染引擎（python-docx + OOXML）
│   ├── parser/                  # Markdown 解析（markdown-it-py）
│   ├── style/                   # 样式引擎 + 模板继承
│   └── templates/               # 10 个内置 YAML 模板
├── marketplace/                 # 模板市场索引（社区贡献）
└── pyproject.toml
```

---

## 技术栈

| 层 | 方案 |
|:--|:-----|
| Markdown 解析 | markdown-it-py |
| DOCX 生成 | python-docx + lxml (OOXML) |
| 模板系统 | PyYAML + 模板继承 |
| MCP Server | FastMCP (stdio) |
| 市场分发 | GitHub + jsDelivr CDN |

## 依赖

- Python ≥ 3.10
- `pip install -e .` 自动安装所需依赖
- OfficeCLI 为可选项，仅用于自动刷新目录页码
