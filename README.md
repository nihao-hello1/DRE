# DRE — Document Rendering Engine

> **AI Agent 最后一公里文档交付。Agent 负责写内容，DRE 负责套格式、加编号、出文档。**

---

## v0.2.0 新功能

### 🔗 模板继承

新建模板只需写**差异项**，20 行 YAML 搞定，不用从 130 行写起：

```yaml
# academic.yaml — 继承 standard，只改左边距
inherits: standard
name: "学术论文"
page:
  margins:
    left: "3.5cm"      # 装订线，其余边距继承 standard
```

- 支持递归继承链，带循环检测
- 深度合并，子模板只覆盖差异项
- 完全向后兼容，旧模板不受影响

### 🏷 图表自动编号

```yaml
numbering:
  enabled: true
  mode: chapter        # sequential: 图1/图2 | chapter: 图1-1/图1-2
  figures:
    prefix: "图"
  tables:
    prefix: "表"
```

- 遇到章节标题自动重置章内计数器
- 图片和表格独立编号
- 默认开启，无需模板显式配置

### 📑 TOC 页码自刷新

不再依赖 OfficeCLI。TOC 域代码已在 DOCX 中正确插入，打开文档后按 **Ctrl+A → F9** 即可刷新目录和页码。

- OfficeCLI 回归为可选工具
- 新增 `dre toc-refresh` 命令给有 OfficeCLI 的用户手动调用

### 🛒 模板市场

```bash
dre template search 投标          # 搜索远程模板
dre template list-remote          # 列出所有远程模板
dre template install minutes      # 一键安装
```

模板托管在 [DRE-templates](https://github.com/nihao-hello1/DRE-templates)，欢迎贡献。

---

## 快速开始

### 安装

```bash
git clone https://github.com/nihao-hello1/DRE.git
cd DRE
pip install -e .
```

### 配置

```bash
# 生成 MCP 配置（自动检测 Python 路径）
python -m dre.cli setup claude     # Claude Code
python -m dre.cli setup codex      # Codex CLI

# 安装 Skill 到 Agent skills 目录
cp -r skills/dre-render ~/.claude/skills/dre-render   # Claude Code
```

重启 Agent 后，写完文档它会主动问你要不要导出 Word。

---

## 可用模板

| 模板 | 风格 | 正文 | 行距 | 首行缩进 | 适用场景 |
|:-----|:-----|:-----|:-----|:---------|:---------|
| `standard` | 标准 | SimSun 12pt | 1.5x | 2字符 | 日常技术文档（默认） |
| `formal` | 正式 | FangSong 14pt | 1.5x | 2字符 | 投标文件、正式报告 |
| `compact` | 紧凑 | SimSun 12pt | 1.25x | 无 | 草稿打印、内部审核 |
| `modern` | 现代 | MS YaHei 11pt | 1.3x | 无 | 科技公司、屏幕阅读 |
| `mac_standard` | 标准(Mac) | STSongti-SC 12pt | 1.5x | 2字符 | macOS 用户 |
| `academic` 🆕 | 学术论文 | SimSun 12pt | 1.5x | 2字符 | GB/T 7713.1 学位论文 |
| `bid` 🆕 | 投标文件 | FangSong 14pt | 1.5x | 2字符 | 招投标文档 |

**模板市场预览**（需联网安装）：

| 模板 | 风格 | 适用场景 |
|:-----|:-----|:---------|
| `government` 🆕 | 党政公文 | GB/T 9704 红头文件 |
| `minutes` 🆕 | 会议纪要 | 简洁会议记录 |
| `weekly_report` 🆕 | 周报月报 | 技术团队汇报 |

```bash
dre template install government   # 安装党政公文模板
```

---

## 使用方式

### Agent 工作流（推荐）

```
Agent 写 Markdown  →  写完主动问"要不要导出 Word？"
                          ↓
                   选排版风格（标准/正式/紧凑/现代/学术/投标/...）
                          ↓
                   调用 DRE MCP 工具渲染 DOCX
```

Agent 写的标题**不需要带编号**（写 `## 概述` 而不是 `## 1.1 概述`），DRE 自动加 Word 原生多级编号。

### CLI 直接使用

```bash
dre render input.md --template standard --output output.docx
dre render input.md -t formal -o output.docx
dre render input.md -t academic -o thesis.docx
dre validate input.md
dre list-templates
dre show-template standard
dre toc-refresh output.docx        # 用 OfficeCLI 刷新目录页码（需安装 OfficeCLI）
```

---

## 创建自定义模板

模板是 YAML 文件，推荐**继承现有模板**：

```bash
# 新建一个仅改字体的模板
cat > src/dre/templates/my_style.yaml << 'EOF'
inherits: standard
name: "我的模板"
description: "仅改正文字体为楷体"
styles:
  body:
    font_name: "KaiTi"
EOF
```

创建后无需重启，`list_templates` 即可看到新模板。

### 完整模板结构

```yaml
inherits: standard                # 🆕 继承父模板（可选）
name: "我的模板"
description: "一句话描述"

page:
  size: A4
  margins:
    top: "2.54cm"
    bottom: "2.54cm"
    left: "3.17cm"
    right: "3.17cm"

styles:
  heading1:             # 一级标题（H1）
    font_name: "SimHei"
    font_size: "16pt"
    bold: true
    alignment: left
    line_spacing: 1.5
    outline_level: 1
  heading2:             # 二级标题（H2）
    # ...
  heading3:             # 三级标题（H3）
    # ...
  heading4:             # 四级标题（H4）
    # ...
  body:                 # 正文
    font_name: "SimSun"
    font_size: "12pt"
    line_spacing: 1.5
    first_line_indent: "0.74cm"
  list_item:            # 列表项
    # ...
  code_block:           # 代码块
    font_name: "Consolas"
    font_size: "10pt"
  blockquote:           # 引用块
    # ...
  caption:              # 图表标题
    font_name: "SimSun"
    font_size: "10.5pt"

table:
  font_name: "SimSun"
  font_size: "10.5pt"
  header_bg: "4472C4"
  header_font_color: "FFFFFF"
  row_alt_color: "F2F2F2"

numbering: 🆕            # 图表自动编号
  enabled: true
  mode: chapter          # "sequential" | "chapter"
  figures:
    prefix: "图"
  tables:
    prefix: "表"
  separator: " "

toc:
  title: "目  录"
  levels: 3
```

---

## MCP 工具

| 工具 | 说明 |
|:----|:-----|
| `render_document(markdown_content, template_name)` | 核心渲染，Markdown → DOCX |
| `validate_document(markdown_content)` | 预检文档结构，不生成文件 |
| `list_templates()` | 列出所有可用模板（含继承链） |
| `document_info(docx_path)` | 查看已渲染文档的信息 |

---

## CLI 命令

```bash
dre parse input.md              # 解析 Markdown 并打印 AST
dre validate input.md           # 验证文档结构
dre list-templates              # 列出本地模板
dre show-template standard      # 查看模板详情（含继承链）
dre render input.md -t formal -o output.docx   # 渲染 DOCX
dre setup claude                # 生成 MCP 配置
dre toc-refresh output.docx     # 刷新目录页码（需 OfficeCLI）
dre template search 投标         # 🆕 搜索远程模板
dre template list-remote        # 🆕 列出市场模板
dre template install minutes    # 🆕 安装远程模板
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
│   ├── style/                   #   样式引擎 + 模板继承
│   └── templates/               #   7 种内置 YAML 模板
├── tests/                       # 测试用例
├── pyproject.toml               # pip install 入口
└── DRE-templates/               # 🆕 模板市场（独立仓库）
```

---

## 技术栈

| 层 | 方案 |
|:--|:-----|
| Markdown 解析 | markdown-it-py |
| DOCX 生成 | python-docx + lxml（OOXML 域代码） |
| 模板系统 | PyYAML + 递归继承 + 深度合并 |
| MCP Server | FastMCP（stdio 传输） |
| 模板市场 | GitHub raw YAML + JSON 索引 |

---

## 需求

- Python ≥ 3.10
- `pip install -e .` 自动安装 python-docx / markdown-it-py / pyyaml / lxml / fastmcp
- （可选）OfficeCLI `refresh` 刷新目录页码
