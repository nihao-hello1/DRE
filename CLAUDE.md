# DRE 项目自身说明

> 这是一个帮助 AI Agent 做文档渲染的工具项目，不是独立应用程序。

## 你在本项目中扮演的角色

你在本仓库中的角色是 **DRE 的维护者和使用者**。当用户要求你渲染文档时：

### 作为使用者

DRE 已配置 MCP Server，你可以直接调用：

- `render_document(markdown_content, template_name, output_path)` — 渲染 DOCX
- `validate_document(markdown_content)` — 预检文档
- `list_templates()` — 查看模板

### 作为维护者

Python 后端位于 `dre/` 目录下。

### 文档状态流

```
起草(draft) → 撰写(developing) → 审阅(reviewing) → 可渲染(ready) → 已交付(rendered)
```

当用户说"可以了"、"定稿"、"生成正式版"时，主动询问是否需要渲染。
