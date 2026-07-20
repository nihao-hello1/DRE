# DRE — Document Rendering Engine

> **AI Agent 的文档交付工具。** Agent 负责写内容，DRE 负责输出专业 DOCX。

---

## 快速开始

```bash
git clone git@github.com:YOUR_USERNAME/DRE.git
cd DRE
pip install -e .
```

生成 MCP 配置（自动检测 Python 路径，**避免 PATH 问题**）：

```bash
python -m dre.cli setup claude   # Claude Code
python -m dre.cli setup codex    # Codex CLI
python -m dre.cli setup hermes   # Hermes
python -m dre.cli setup trae     # Trae
```

安装 Skill 文件到 Agent 的 skills 目录：

```bash
cp -r skills/dre-render ~/.claude/skills/dre-render    # Claude Code
cp -r skills/dre-render ~/.codex/skills/dre-render     # Codex CLI
```

重启 Agent，写完文档后会主动问要不要导出 Word。

---

## 工作流

```
Agent 写 Markdown → DRE 加编号 + 套格式 → 输出专业 DOCX
```

- Agent 写标题**不需要写编号**（写 `## 概述`，不是 `## 1.1 概述`）
- 写完文档后 Agent 主动问：*"需要导出 Word 吗？"*
- 用户选择排版风格（标准/正式/紧凑/现代）
- 一键渲染出 DOCX

---

## MCP 工具

| 工具 | 说明 |
|:----|:-----|
| `render_document(markdown_content, template_name)` | 核心渲染 |
| `validate_document(markdown_content)` | 预检结构 |
| `list_templates()` | 查看可用模板 |
| `document_info(docx_path)` | 查看文档信息 |

---

## 4 种排版模板

| 模板 | 风格 | 正文 | 行距 | 首行缩进 |
|:-----|:-----|:-----|:-----|:---------|
| `standard` | 标准 | SimSun 12pt | 1.5x | 2 字符 |
| `formal` | 正式 | FangSong 14pt | 1.5x | 2 字符 |
| `compact` | 紧凑 | SimSun 12pt | 1.25x | 无 |
| `modern` | 现代 | MS YaHei 11pt | 1.3x | 无 |

---

## 项目结构

```
DRE/
├── skills/dre-render/SKILL.md    # Agent 指令（Skill）
├── src/dre/                       # Python 包
│   ├── mcp_server/               #   MCP Server
│   ├── renderer/                 #   DOCX 渲染引擎
│   ├── parser/                   #   Markdown 解析
│   ├── style/                    #   样式引擎
│   └── templates/               #   4 种 YAML 模板
├── pyproject.toml                 # pip install 入口
├── tests/fixtures/               # 测试用例
└── references/                   # 参考文档分析
```

---

## 依赖

- Python ≥ 3.10
- python-docx, markdown-it-py, pyyaml, lxml, fastmcp
- （可选）OfficeCLI — 自动刷新 TOC 页码
