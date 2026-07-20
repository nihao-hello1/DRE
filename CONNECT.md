# DRE 连接指南

> 将 DRE 接入你的 AI Agent。

## 所有 Agent 的通用步骤

### 1. 启动 MCP Server

确保 DRE 目录下的 Python 依赖齐全，然后 MCP Server 通过以下方式运行：

```bash
cd F:/DRE
python -m dre.mcp_server.server
```

MCP Server 使用 **stdio 传输**，Agent 通过子进程的方式启动它。

### 2. 配置 MCP

所有主流 Agent 都支持 MCP 协议，配置格式基本一致：

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

### 3. 加载 Skill

将 `skills/dre-skill.md` 的内容加载到 Agent 的指令中，让它知道：
- DRE 是什么
- 什么时候该用（文档状态流 + 触发信号）
- 怎么调用 MCP 工具

---

## Agent 专用配置

### Claude Code

**MCP 配置位置**：`.claude/settings.local.json`

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

**Skill 加载**：配置文件中的 `CLAUDE.md` 已包含 DRE 说明，也可手动输入 `/dre-render`。

### Codex

**MCP 配置**：在 Codex 的 MCP 配置中添加上述 JSON 区块。

**Skill 加载**：将 `skills/codex/` 中的内容添加到 Custom Instructions。

### Trae

**MCP 配置**：在 Trae 的 MCP Server 配置中添加。

**Skill 加载**：将 `skills/trae/` 中的内容添加到 Agent 指令。

### Hermes

**MCP 配置**：在 `config.yaml` 中添加：

```yaml
mcp_servers:
  dre:
    command: python
    args: ["-m", "dre.mcp_server.server"]
    cwd: "F:/DRE"
```

**Skill 加载**：将 `skills/hermes/` 中的内容添加到 System Prompt。

### OpenClaw

**MCP 配置**：在 OpenClaw 配置文件中添加 MCP Server。

**Skill 加载**：将 `skills/openclaw/` 中的内容作为 Rule 加载。

---

## 验证连接

在 Agent 中输入以下内容测试 DRE 是否正常工作：

> "帮我验证一下 DRE 是否可用，列出可用模板。"

如果返回了模板列表，说明连接成功。
