# DRE — Document Rendering Engine

> **一个为 AI Agent 提供文档渲染能力的 MCP 工具。**
>
> Agent 负责写内容，DRE 负责把 Markdown 变成正式可交付的 DOCX。

---

## 这是什么

DRE 是一个 MCP Server，提供了一组文档渲染工具。**主流 AI Agent（Claude Code、Codex、Hermes、OpenClaw、Trae 等）** 通过 MCP 协议连接 DRE，就能在写文档的场景中自动获得专业的 DOCX 输出能力。

```
你的 Agent ──MCP──→ DRE MCP Server ──→ 专业 DOCX 文档
                      │
                      ├─ 解析 Markdown
                      ├─ 应用样式模板
                      ├─ 渲染 DOCX
                      └─ 目录/页码/页眉页脚
```

## 快速接入

所有支持 MCP 的 Agent 通用，只需两步：

**1. 安装 Skill** — 把 `skills/dre-render/` 目录复制到 Agent 的 skills 目录下：

```bash
# Claude Code（全局）
cp -r skills/dre-render ~/.claude/skills/dre-render

# Codex CLI（全局）
cp -r skills/dre-render ~/.codex/skills/dre-render

# 或项目级
cp -r skills/dre-render .claude/skills/dre-render   # Claude Code
cp -r skills/dre-render .codex/skills/dre-render    # Codex CLI
```

Claude Code 配置好后输入 `/dre-render` 即可加载。

**2. 配置 MCP** — 在 Agent 的 MCP 配置中添加：

```json
{
  "mcpServers": {
    "dre": {
      "command": "python",
      "args": ["-m", "dre.mcp_server.server"],
      "cwd": "F:/DRE"
    }
  }
}
```

> 部分 Agent 使用 TOML 或 YAML 格式，参见 `SKILL.md` 中的说明。

### Agent 集成后的工作流

当你使用 Agent 撰写技术文档时，写完后 Agent 会主动问：

> "文档写好了，需要我帮你导出为正式的 Word 文档吗？"

选好排版风格后，Agent 调用 DRE 的 `render_document` 工具，一键输出 DOCX。

## DRE 提供的能力

| 工具 | 作用 |
|:----|:------|
| `render_document` | Markdown → 专业 DOCX（含样式、目录、页码） |
| `validate_document` | 预检文档结构，不生成文件 |
| `list_templates` | 查看可用样式模板 |
| `document_info` | 查看已渲染 DOCX 的信息 |

## 默认模板

`tech_design` — 专为中文技术设计文档优化（SimHei 标题 + SimSun 正文 + 自动目录 + 页码 + 页眉页脚 + 表格样式 + 代码块样式）。

## 项目结构

```
F:\DRE\
├── skills/                        # ← 各 Agent 的 Skill 文件
│   ├── dre-skill.md              #   通用 Prompt Pack
│   ├── claude-code/              #   Claude Code 专用
│   ├── codex/                    #   Codex 专用
│   ├── hermes/                   #   Hermes 专用
│   ├── openclaw/                 #   OpenClaw 专用
│   └── trae/                     #   Trae 专用
├── dre/                          # MCP Server 后端实现
│   └── mcp_server/               #   FastMCP server
├── templates/                     # YAML 样式模板
└── CONNECT.md                     # 各 Agent 连接指南
```

## 前提条件

- Python 3.10+
- 已有依赖：python-docx / markdown-it-py / pyyaml / lxml / fastmcp
- （可选）OfficeCLI，用于自动刷新目录页码
