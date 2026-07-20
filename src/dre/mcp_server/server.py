"""DRE MCP Server — exposes document rendering as MCP tools.

Usage:
    python -m dre.mcp_server.server              # start stdio server

Claude Code configuration (settings.local.json)::

    "mcpServers": {
        "dre": {
            "command": "python",
            "args": ["-m", "dre.mcp_server.server"],
            "cwd": "F:/DRE"
        }
    }
"""

from __future__ import annotations

import sys
from pathlib import Path

from fastmcp import FastMCP

from dre.mcp_server.tools import (
    get_document_info,
    list_templates,
    render_document,
    validate_document,
)

# ---------------------------------------------------------------------------
#  FastMCP server instance
# ---------------------------------------------------------------------------

mcp = FastMCP("dre")


# ---------------------------------------------------------------------------
#  Tool registrations
# ---------------------------------------------------------------------------

@mcp.tool(
    name="render_document",
    description="Convert Markdown content to a professional DOCX document. "
    "This is the main tool. Call after the user confirms the content is final.",
)
async def tool_render_document(
    markdown_content: str,
    template_name: str = "standard",
    output_path: str | None = None,
    no_postprocess: bool = False,
) -> str:
    """Render Markdown to DOCX.

    Args:
        markdown_content: The full Markdown text to render.
        template_name: Style template name (default: tech_design).
        output_path: Optional output file path.
        no_postprocess: Skip OfficeCLI refresh if True.

    Returns:
        A JSON string with the result.
    """
    import json
    result = render_document(
        markdown_content=markdown_content,
        template_name=template_name,
        output_path=output_path,
        no_postprocess=no_postprocess,
    )
    return json.dumps(result, ensure_ascii=False)


@mcp.tool(
    name="validate_document",
    description="Parse and validate Markdown content. "
    "Returns a summary of the document structure (node counts, title, etc.). "
    "Does NOT produce any output file.",
)
async def tool_validate_document(
    markdown_content: str,
) -> str:
    """Validate Markdown content structure."""
    import json
    result = validate_document(markdown_content=markdown_content)
    return json.dumps(result, ensure_ascii=False)


@mcp.tool(
    name="list_templates",
    description="List all available style templates. "
    "Returns template names and descriptions.",
)
async def tool_list_templates() -> str:
    """List available style templates."""
    import json
    result = list_templates()
    return json.dumps(result, ensure_ascii=False)


@mcp.tool(
    name="document_info",
    description="Get metadata about a previously rendered DOCX file. "
    "Returns paragraph count, tables, headings, and file size.",
)
async def tool_document_info(
    docx_path: str,
) -> str:
    """Get metadata about a DOCX file."""
    import json
    result = get_document_info(docx_path=docx_path)
    return json.dumps(result, ensure_ascii=False)


# ---------------------------------------------------------------------------
#  Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """Run the MCP server on stdio transport."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
