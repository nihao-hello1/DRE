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
    """List available style templates (local + marketplace)."""
    from dre.mcp_server.tools import list_templates as _list_all

    result = _list_all()
    local = result.get("local", [])
    marketplace = result.get("marketplace", [])

    print(f"Local templates ({len(local)}):")
    for t in local:
        print(f"  {t['name']:20s}  {t.get('description', '')}")

    if marketplace:
        print(f"\nMarketplace ({len(marketplace)}):")
        for t in marketplace:
            tags = ", ".join(t.get("tags", [])[:3])
            tag_str = f"  [{tags}]" if tags else ""
            print(f"  {t['name']:20s}  {t.get('description', '')} {tag_str}")
        print(f"\n  Install with: dre template install <name>")

    return 0


def cmd_show_template(args: list[str]) -> int:
    """Load and display a template's resolved styles."""
    if not args:
        print("Usage: python -m dre.cli show-template <name>", file=sys.stderr)
        return 1

    from dre.config import templates_dir

    tmpl_name = args[0]
    if tmpl_name == "tech_design": tmpl_name = "standard"  # backward compat
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
    if tmpl_name == "tech_design": tmpl_name = "standard"  # backward compat
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
    print()
    print("  TIP: Open the document and press Ctrl+A -> F9 to refresh TOC and page numbers.")

    # OfficeCLI post-processing is an explicit opt-in for automation-heavy users
    if not parsed.no_postprocess:
        from dre.postprocess.officecli import OfficePostProcessor
        pp = OfficePostProcessor()
        if pp.is_available():
            print("  OfficeCLI detected, auto-refreshing...")
            try:
                pp.refresh(output_path)
                print("  [OK] TOC and page numbers refreshed.")
            except Exception:
                pass  # Fall through — TOC works after manual refresh in Word

    return 0


def cmd_setup(args: list[str]) -> int:
    """Generate MCP configuration for the current agent platform."""
    if not args:
        print("Usage: python -m dre.cli setup <agent>")
        print("Supported agents: claude, codex, hermes, openclaw, trae")
        return 1

    import sys
    python = sys.executable  # absolute path to the current Python interpreter

    agent = args[0].lower()
    configs = {
        "claude": {
            "file": ".claude/settings.local.json",
            "format": "json",
            "config": {
                "mcpServers": {
                    "dre": {
                        "command": python,
                        "args": ["-m", "dre.mcp_server.server"]
                    }
                }
            }
        },
        "codex": {
            "file": "~/.codex/config.toml",
            "format": "toml",
            "config": f"[mcp_servers.dre]\ncommand = '{python}'\nargs = [\"-m\", \"dre.mcp_server.server\"]\nstartup_timeout_sec = 15\n"
        },
        "hermes": {
            "file": "~/.hermes/config.yaml",
            "format": "yaml",
            "config": f"mcp_servers:\n  dre:\n    command: '{python}'\n    args: ['-m', 'dre.mcp_server.server']\n"
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
                                    "command": python,
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
                        "command": python,
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


def cmd_toc_refresh(args: list[str]) -> int:
    """Refresh TOC and page-number fields in a DOCX using OfficeCLI (explicit opt-in)."""
    if not args:
        print("Usage: python -m dre.cli toc-refresh <file.docx>", file=sys.stderr)
        return 1

    docx_path = Path(args[0])
    if not docx_path.exists():
        print(f"Error: file not found: {docx_path}", file=sys.stderr)
        return 1

    from dre.postprocess.officecli import OfficePostProcessor
    pp = OfficePostProcessor()
    if not pp.is_available():
        print(
            "OfficeCLI 未安装。请从 https://clio.officecli.com 安装，\n"
            "或直接在 Word 中打开文档 → Ctrl+A → F9 手动刷新。",
            file=sys.stderr,
        )
        return 1

    print(f"刷新中: {docx_path} ...")
    try:
        pp.refresh(docx_path)
        print("[OK] 目录和页码已刷新。")
    except Exception as exc:
        print(f"刷新失败: {exc}", file=sys.stderr)
        return 1

    return 0


def cmd_template_search(args: list[str]) -> int:
    """Search remote templates from the DRE template marketplace."""
    if not args:
        print("Usage: python -m dre.cli template search <keyword>", file=sys.stderr)
        return 1

    keyword = args[0].strip()
    _print_template_search(keyword)
    return 0


def cmd_template_install(args: list[str]) -> int:
    """Install a template from the DRE template marketplace."""
    if not args:
        print("Usage: python -m dre.cli template install <name>", file=sys.stderr)
        return 1

    template_name = args[0].strip()
    return _install_remote_template(template_name)


def cmd_template_list_remote(args: list[str]) -> int:
    """List all templates available in the DRE template marketplace."""
    _print_template_search("")  # empty keyword = list all
    return 0


def main() -> int:
    commands = {
        "parse": cmd_parse,
        "validate": cmd_validate,
        "list-templates": cmd_list_templates,
        "show-template": cmd_show_template,
        "render": cmd_render,
        "setup": cmd_setup,
        "toc-refresh": cmd_toc_refresh,
        "template": cmd_template_dispatch,
    }

    if len(sys.argv) < 2:
        print("Usage: python -m dre.cli <command> [args...]", file=sys.stderr)
        print(f"Commands: {', '.join(sorted(commands))}", file=sys.stderr)
        return 1

    cmd = sys.argv[1]
    if cmd in ("-h", "--help"):
        print("Usage: python -m dre.cli <command> [args...]")
        print(f"Commands: {', '.join(sorted(commands))}")
        return 0

    handler = commands.get(cmd)
    if handler is None:
        print(f"Unknown command: {cmd}", file=sys.stderr)
        print(f"Available: {', '.join(sorted(commands))}", file=sys.stderr)
        return 1

    return handler(sys.argv[2:])


def cmd_template_dispatch(args: list[str]) -> int:
    """Dispatch ``dre template <subcommand>``."""
    if not args:
        print("Usage: python -m dre.cli template <search|install|list-remote>", file=sys.stderr)
        return 1

    sub = args[0]
    rest = args[1:]
    if sub == "search":
        return cmd_template_search(rest)
    elif sub == "install":
        return cmd_template_install(rest)
    elif sub in ("list-remote", "list_remote", "remote"):
        return cmd_template_list_remote(rest)
    else:
        print(f"Unknown template subcommand: {sub}", file=sys.stderr)
        print("Available: search, install, list-remote", file=sys.stderr)
        return 1


# ===================================================================
#  Template Marketplace helpers
# ===================================================================

# Official DRE template marketplace — GitHub repo serving raw YAML templates.
_MARKETPLACE_INDEX_URL = (
    "https://raw.githubusercontent.com/nihao-hello1/DRE-templates/main/index.json"
)
_MARKETPLACE_RAW_BASE = (
    "https://raw.githubusercontent.com/nihao-hello1/DRE-templates/main/templates"
)


def _fetch_marketplace_index() -> list[dict]:
    """Download the marketplace template index.

    Returns a list of dicts, each with keys: name, description, tags, version.
    Returns an empty list on any error (network, parsing, etc.).
    """
    try:
        import urllib.request
        import json
        req = urllib.request.Request(_MARKETPLACE_INDEX_URL)
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        if isinstance(data, list):
            return data
        if isinstance(data, dict) and "templates" in data:
            return data["templates"]
        return []
    except Exception:
        return []


def _print_template_search(keyword: str) -> None:
    """Search the marketplace index and print matching templates."""
    templates = _fetch_marketplace_index()
    if not templates:
        print("Cannot connect to template marketplace.")
        print(f"   Visit: {_MARKETPLACE_INDEX_URL.replace('/index.json', '')}")
        return

    keyword_lower = keyword.lower()
    results = [
        t for t in templates
        if not keyword_lower
        or keyword_lower in t.get("name", "").lower()
        or keyword_lower in t.get("description", "").lower()
        or keyword_lower in " ".join(t.get("tags", [])).lower()
    ]

    if not results:
        print(f"No templates matching '{keyword}'.")
        print(f"\nAvailable templates ({len(templates)}):")
        for t in templates:
            print(f"  {t['name']:20s} - {t.get('description', '')}")
        return

    print(f"Found {len(results)} template(s):\n")
    for t in results:
        tags = ", ".join(t.get("tags", [])[:3])
        print(f"  {t['name']:20s}  v{t.get('version', '0.1.0')}")
        print(f"  {t.get('description', '')}")
        if tags:
            print(f"  Tags: {tags}")
        print()


def _install_remote_template(name: str) -> int:
    """Download a remote template YAML and save it locally."""
    import urllib.request

    from dre.config import templates_dir

    # Check if already installed
    local_path = templates_dir() / f"{name}.yaml"
    if local_path.exists():
        resp = input(f"Template '{name}' already exists. Overwrite? [y/N] ")
        if resp.lower() not in ("y", "yes"):
            print("Cancelled.")
            return 0

    url = f"{_MARKETPLACE_RAW_BASE}/{name}.yaml"
    print(f"Downloading: {url} ...")

    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=15) as resp:
            content = resp.read()
    except Exception as exc:
        print(f"Download failed: {exc}", file=sys.stderr)
        print(f"Check that template name '{name}' is correct.", file=sys.stderr)
        return 1

    local_path.write_bytes(content)
    print(f"[OK] Installed: {local_path}")
    print(f"     Usage: python -m dre.cli render input.md --template {name} -o output.docx")
    return 0


def cmd_template_search(args: list[str]) -> int:
    """Search remote templates from the DRE template marketplace."""
    if not args:
        print("Usage: python -m dre.cli template search <keyword>", file=sys.stderr)
        return 1

    keyword = args[0].strip()
    _print_template_search(keyword)
    return 0


def cmd_template_install(args: list[str]) -> int:
    """Install a template from the DRE template marketplace."""
    if not args:
        print("Usage: python -m dre.cli template install <name>", file=sys.stderr)
        return 1

    template_name = args[0].strip()
    return _install_remote_template(template_name)


def cmd_template_list_remote(args: list[str]) -> int:
    """List all templates available in the DRE template marketplace."""
    _print_template_search("")  # empty keyword = list all
    return 0


if __name__ == "__main__":
    sys.exit(main())
