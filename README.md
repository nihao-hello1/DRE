# DRE — Document Rendering Engine

> **解决AI Agent 写作出的文档是Markdown格式或者使用python-docx写出来的文件排版格式不友好经过DRE处理后 → 专业 DOCX文档。**

Agent 负责写内容，DRE 负责套格式、加编号、出文档。

---

## 快速开始

```bash
# 1. 克隆
https://github.com/nihao-hello1/DRE.git
cd DRE

# 2. 安装（可编辑模式，代码更新自动生效）
pip install -e .

# 3. 生成 MCP 配置（自动检测 Python 路径，避免 PATH 问题）
python -m dre.cli setup claude     # Claude Code
python -m dre.cli setup codex      # Codex CLI
python -m dre.cli setup hermes     # Hermes
python -m dre.cli setup trae       # Trae

# 4. 安装 Skill 到 Agent skills 目录
cp -r skills/dre-render ~/.claude/skills/dre-render   # Claude Code
cp -r skills/dre-render ~/.codex/skills/dre-render    # Codex CLI

# 5. 重启 Agent
```

完成以上后，用 Agent 写一篇文档，写完它会主动问你要不要导出 Word。

---

## Agent 完整工作流

```
Agent 写 Markdown  →  写完主动问"要不要导出 Word？"
                          ↓
                   选排版风格（标准/正式/紧凑/现代）
                          ↓
                   调用 DRE MCP 工具渲染 DOCX
```

Agent 写的标题**不需要带编号**（写 `## 概述` 而不是 `## 1.1 概述`），DRE 自动加 Word 原生多级编号。

---

## 可用模板

| 模板 | 风格 | 正文 | 行距 | 首行缩进 | 适用场景 |
|:-----|:-----|:-----|:-----|:---------|:---------|
| `standard` | 标准 | SimSun 12pt | 1.5x | 2字符 | 日常技术文档（默认） |
| `formal` | 正式 | FangSong 14pt | 1.5x | 2字符 | 投标文件、正式报告 |
| `compact` | 紧凑 | SimSun 12pt | 1.25x | 无 | 草稿打印、内部审核 |
| `modern` | 现代 | MS YaHei 11pt | 1.3x | 无 | 科技公司、屏幕阅读 |

---

## 创建自定义模板

模板是 YAML 文件，放在 `src/dre/templates/` 下即可。复制并修改任意现有模板：

```bash
cp src/dre/templates/standard.yaml src/dre/templates/my_style.yaml
```

模板结构说明：

```yaml
name: "我的模板"
description: "一句话描述"

page:
  size: A4
  margins:
    top: "2.54cm"       # 上边距
    bottom: "2.54cm"    # 下边距
    left: "3.17cm"      # 左边距
    right: "3.17cm"     # 右边距

styles:
  heading1:             # 一级标题（H1）
    font_name: "SimHei"
    font_size: "16pt"
    bold: true
    alignment: left
    space_before: "12pt"
    space_after: "12pt"
    line_spacing: 1.5
    outline_level: 1
  heading2:             # 二级标题（H2）
    font_name: "SimHei"
    font_size: "14pt"
    bold: true
    # ... 同上结构
  heading3:             # 三级标题（H3）
    # ...
  body:                 # 正文
    font_name: "SimSun"
    font_size: "12pt"
    line_spacing: 1.5
    first_line_indent: "0.74cm"   # 首行缩进，0cm 则无
  list_item:            # 列表项
    # ...
  code_block:           # 代码块
    font_name: "Consolas"
    font_size: "10pt"
  blockquote:           # 引用块
    # ...

table:
  font_name: "SimSun"
  font_size: "10.5pt"
  header_bg: "4472C4"           # 表头背景色（hex）
  header_font_color: "FFFFFF"   # 表头字体色
  row_alt_color: "F2F2F2"       # 隔行背景色

toc:
  title: "目  录"
  levels: 3                     # 目录包含的标题级别数
```

创建后无需重启，DRE 自动读取。通过 `list_templates` 即可看到新模板。

---

## MCP 工具

| 工具 | 说明 |
|:----|:-----|
| `render_document(markdown_content, template_name)` | 核心渲染，Markdown → DOCX |
| `validate_document(markdown_content)` | 预检结构，不生成文件 |
| `list_templates()` | 列出所有可用模板 |
| `document_info(docx_path)` | 查看已渲染文档的信息 |

---

## CLI 命令

```bash
dre render input.md --template standard --output output.docx
dre render input.md -t formal -o output.docx --no-postprocess
dre validate input.md
dre list-templates
dre show-template standard
dre setup claude           # 生成 MCP 配置
```

---

## 项目结构

```
DRE/
├── skills/dre-render/SKILL.md   # Agent Skill 文件
├── src/dre/                      # Python 包
│   ├── mcp_server/              #   MCP Server（FastMCP）
│   ├── renderer/                #   DOCX 渲染引擎（python-docx）
│   ├── parser/                  #   Markdown 解析（markdown-it-py）
│   ├── style/                   #   样式引擎（YAML 模板）
│   └── templates/               #   4 种内置 YAML 模板
├── tests/fixtures/              # 测试用例
├── references/                  # 参考企业文档分析
├── pyproject.toml               # pip install 入口
└── .claude/settings.local.json  # Claude Code MCP 参考配置
```

---

## 技术栈

| 层 | 方案 |
|:--|:-----|
| Markdown 解析 | markdown-it-py |
| DOCX 生成 | python-docx + lxml（OOXML 域代码） |
| 模板系统 | PyYAML |
| MCP Server | FastMCP（stdio 传输） |
| 后处理 | OfficeCLI（刷新 TOC 页码，可选） |

---

## 需求

- Python ≥ 3.10
- `pip install -e .` 自动安装 python-docx / markdown-it-py / pyyaml / lxml / fastmcp
- （可选）OfficeCLI `refresh` 刷新目录页码
