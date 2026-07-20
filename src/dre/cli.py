"""DRE 命令行入口。

Usage:
    python -m dre.cli parse <input.md>        解析 Markdown 并打印 AST
    python -m dre.cli validate <input.md>      验证 Markdown 结构
    python -m dre.cli list-templates           列出可用模板（Phase 2）
    python -m dre.cli render <input.md>        渲染 DOCX（Phase 3）
"""

import json
import sys
from pathlib import Path

from dre.ast.nodes import Document
from dre.parser.markdown_parser import MarkdownParser


def cmd_parse(args: list[str]) -> int:
    """Parse a Markdown file and print the AST as JSON."""
    if not args:
        print("Usage: python -m dre.cli parse <input.md>", file=sys.stderr)
        return 1

    md_path = Path(args[0])
    if not md_path.exists():
        print(f"Error: file not found: {md_path}", file=sys.stderr)
        return 1

    parser = MarkdownParser()
    doc = parser.parse_file(md_path)
    print(json.dumps(doc.to_dict(), ensure_ascii=False, indent=2))
    return 0


def cmd_validate(args: list[str]) -> int:
    """Parse Markdown and print a summary report."""
    if not args:
        print("Usage: python -m dre.cli validate <input.md>", file=sys.stderr)
        return 1

    md_path = Path(args[0])
    if not md_path.exists():
        print(f"Error: file not found: {md_path}", file=sys.stderr)
        return 1

    parser = MarkdownParser()
    doc = parser.parse_file(md_path)
    flat = doc.walk()
    summary: dict[str, int] = {}
    for node in flat:
        t = node.node_type
        summary[t] = summary.get(t, 0) + 1

    print(f"Document: {md_path.name}")
    print(f"  Title:      {doc.title or '(none)'}")
    print(f"  Paragraphs: {summary.get('paragraph', 0)}")
    print(f"  Headings:   {summary.get('heading', 0)}")
    print(f"  Lists:      {summary.get('bullet_list', 0) + summary.get('ordered_list', 0)}")
    print(f"  Tables:     {summary.get('table', 0)}")
    print(f"  Images:     {summary.get('image', 0)}")
    print(f"  CodeBlocks: {summary.get('code_block', 0)}")
    print(f"  Quotes:     {summary.get('block_quote', 0)}")
    print(f"  Total nodes: {len(flat)}")
    return 0


def cmd_list_templates(args: list[str]) -> int:
    """List available style templates."""
    from dre.config import templates_dir

    td = templates_dir()
    if not td.exists():
        print("No templates directory found.", file=sys.stderr)
        return 1

    yaml_files = sorted(td.glob("*.yaml"))
    if not yaml_files:
        print("No templates found.")
        return 0

    print("Available templates:")
    for f in yaml_files:
        print(f"  {f.stem}")
    return 0


def cmd_show_template(args: list[str]) -> int:
    """Load and display a template's resolved styles."""
    if not args:
        print("Usage: python -m dre.cli show-template <name>", file=sys.stderr)
        return 1

    from dre.config import templates_dir

    tmpl_name = args[0]
    tmpl_path = templates_dir() / f"{tmpl_name}.yaml"
    if not tmpl_path.exists():
        print(f"Error: template '{tmpl_name}' not found", file=sys.stderr)
        return 1

    from dre.style.template import StyleTemplate

    tmpl = StyleTemplate.from_yaml(tmpl_path)
    print(json.dumps(tmpl.to_debug_dict(), ensure_ascii=False, indent=2))
    return 0


def cmd_render(args: list[str]) -> int:
    """Render a Markdown file to DOCX."""
    import argparse

    parser = argparse.ArgumentParser(prog="dre render", description="Render Markdown to DOCX")
    parser.add_argument("input", help="Input Markdown file (.md)")
    parser.add_argument("--template", "-t", default="standard", help="Template name (standard/formal/compact/modern)")
    parser.add_argument("--output", "-o", default=None, help="Output DOCX path")
    parser.add_argument("--no-postprocess", action="store_true", help="Skip OfficeCLI post-processing")

    parsed = parser.parse_args(args)

    md_path = Path(parsed.input)
    if not md_path.exists():
        print(f"Error: file not found: {md_path}", file=sys.stderr)
        return 1

    # Resolve template
    from dre.config import templates_dir

    tmpl_name = parsed.template
    tmpl_path = templates_dir() / f"{tmpl_name}.yaml"
    if not tmpl_path.exists():
        print(f"Error: template '{tmpl_name}' not found", file=sys.stderr)
        return 1

    # Resolve output path
    output_path = parsed.output
    if output_path is None:
        output_path = md_path.with_suffix(".docx").name

    # Parse
    from dre.parser.markdown_parser import MarkdownParser
    from dre.style.template import StyleTemplate
    from dre.renderer.docx_renderer import DocxRenderer

    print(f"Parsing: {md_path.name} ...")
    parser = MarkdownParser()
    doc = parser.parse_file(md_path)

    print(f"Loading template: {tmpl_name} ...")
    template = StyleTemplate.from_yaml(tmpl_path)

    print(f"Rendering: {output_path} ...")
    renderer = DocxRenderer(template)
    renderer.render(doc, output_path)

    print(f"[OK] Done: {output_path}")

    # Post-processing
    if not parsed.no_postprocess:
        from dre.postprocess.officecli import OfficePostProcessor
        pp = OfficePostProcessor()
        if pp.is_available():
            print("Running OfficeCLI post-processing ...")
            pp.refresh(output_path)
            print("[OK] Post-processing complete")
        else:
            print("(OfficeCLI not available — TOC will need manual update in Word)")

    return 0


def cmd_setup(args: list[str]) -> int:
    """Generate MCP configuration for the current agent platform."""
    if not args:
        print("Usage: python -m dre.cli setup <agent>")
        print("Supported agents: claude, codex, hermes, openclaw, trae")
        return 1

    agent = args[0].lower()
    configs = {
        "claude": {
            "file": ".claude/settings.local.json",
            "format": "json",
            "config": {
                "mcpServers": {
                    "dre": {
                        "command": "python",
                        "args": ["-m", "dre.mcp_server.server"]
                    }
                }
            }
        },
        "codex": {
            "file": "~/.codex/config.toml",
            "format": "toml",
            "config": '[mcp_servers.dre]\ncommand = "python"\nargs = ["-m", "dre.mcp_server.server"]\n'
        },
        "hermes": {
            "file": "~/.hermes/config.yaml",
            "format": "yaml",
            "config": "mcp_servers:\n  dre:\n    command: python\n    args: [\"-m\", \"dre.mcp_server.server\"]\n"
        },
        "openclaw": {
            "file": "~/.openclaw/openclaw.json",
            "format": "json",
            "config": {
                "plugins": {
                    "entries": {
                        "mcp-adapter": {
                            "enabled": True,
                            "config": {
                                "servers": [{
                                    "name": "dre",
                                    "transport": "stdio",
                                    "command": "python",
                                    "args": ["-m", "dre.mcp_server.server"]
                                }]
                            }
                        }
                    }
                }
            }
        },
        "trae": {
            "file": "Trae Settings → MCP → Manual Config",
            "format": "json",
            "config": {
                "mcpServers": {
                    "dre": {
                        "command": "python",
                        "args": ["-m", "dre.mcp_server.server"]
                    }
                }
            }
        },
    }

    import json
    if agent not in configs:
        print(f"Unknown agent: {agent}", file=sys.stderr)
        print(f"Supported: {', '.join(configs)}", file=sys.stderr)
        return 1

    c = configs[agent]
    print(f"Add this to {c['file']}:")
    print()
    if c["format"] == "json":
        print(json.dumps(c["config"], indent=2, ensure_ascii=False))
    else:
        print(c["config"])
    print()
    print("Then install the DRE Skill:")
    print("  1. Copy skills/dre-render/SKILL.md to your Agent's skills directory")
    print("  2. Restart the Agent")
    return 0


def cmd_setup_main() -> None:
    """Entry point for `dre-setup` console script."""
    raise SystemExit(cmd_setup(sys.argv[1:]))


def main() -> int:
    commands = {
        "parse": cmd_parse,
        "validate": cmd_validate,
        "list-templates": cmd_list_templates,
        "show-template": cmd_show_template,
        "render": cmd_render,
        "setup": cmd_setup,
    }

    if len(sys.argv) < 2:
        print("Usage: python -m dre.cli <command> [args...]", file=sys.stderr)
        print(f"Commands: {', '.join(commands)}", file=sys.stderr)
        return 1

    cmd = sys.argv[1]
    if cmd in ("-h", "--help"):
        print("Usage: python -m dre.cli <command> [args...]")
        print(f"Commands: {', '.join(commands)}")
        return 0

    handler = commands.get(cmd)
    if handler is None:
        print(f"Unknown command: {cmd}", file=sys.stderr)
        print(f"Available: {', '.join(commands)}", file=sys.stderr)
        return 1

    return handler(sys.argv[2:])


if __name__ == "__main__":
    sys.exit(main())
