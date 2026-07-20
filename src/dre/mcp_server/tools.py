"""MCP tool handlers — each maps to a DRE capability.

These functions are called by the FastMCP server in server.py.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional


def render_document(
    markdown_content: str,
    template_name: str = "standard",
    output_path: Optional[str] = None,
    no_postprocess: bool = False,
) -> dict[str, Any]:
    """Convert markdown content to a DOCX file.

    Args:
        markdown_content: The full Markdown text to render.
        template_name: Name of the style template (without .yaml).
        output_path: Optional path for the output DOCX.
        no_postprocess: Skip OfficeCLI post-processing if True.

    Returns:
        dict with keys: success, output_path, errors, warnings
    """
    errors: list[str] = []
    warnings: list[str] = []

    try:
        from dre.parser.markdown_parser import MarkdownParser
        from dre.style.template import StyleTemplate
        from dre.renderer.docx_renderer import DocxRenderer

        # Determine template path
        tmpl_path = _template_path(template_name)
        if not tmpl_path.exists():
            return {
                "success": False,
                "output_path": "",
                "errors": [f"Template '{template_name}' not found"],
                "warnings": [],
            }

        # Parse
        parser = MarkdownParser()
        doc = parser.parse(markdown_content)

        # Load template
        template = StyleTemplate.from_yaml(tmpl_path)

        # Determine output path
        if not output_path:
            output_path = _default_output_name()

        # Render
        renderer = DocxRenderer(template)
        renderer.render(doc, output_path)
        output_path = str(Path(output_path).resolve())

        # Post-processing
        if not no_postprocess:
            from dre.postprocess.officecli import OfficePostProcessor
            pp = OfficePostProcessor()
            if pp.is_available():
                pp.refresh(output_path)
            else:
                warnings.append("OfficeCLI not available — TOC needs manual update in Word")

        return {
            "success": True,
            "output_path": output_path,
            "errors": errors,
            "warnings": warnings,
        }

    except Exception as exc:
        errors.append(str(exc))
        return {
            "success": False,
            "output_path": output_path or "",
            "errors": errors,
            "warnings": warnings,
        }


def validate_document(markdown_content: str) -> dict[str, Any]:
    """Parse and validate markdown content without rendering.

    Returns a summary of the document structure.
    """
    from dre.parser.markdown_parser import MarkdownParser

    errors: list[str] = []
    warnings: list[str] = []

    try:
        parser = MarkdownParser()
        doc = parser.parse(markdown_content)
        flat = doc.walk()

        summary: dict[str, int] = {}
        for node in flat:
            t = node.node_type
            summary[t] = summary.get(t, 0) + 1

        return {
            "valid": True,
            "title": doc.title or "",
            "node_count": len(flat),
            "summary": summary,
            "errors": errors,
            "warnings": warnings,
        }
    except Exception as exc:
        errors.append(str(exc))
        return {
            "valid": False,
            "title": "",
            "node_count": 0,
            "summary": {},
            "errors": errors,
            "warnings": warnings,
        }


def list_templates() -> dict[str, Any]:
    """List available style templates."""
    from dre.config import templates_dir
    td = templates_dir()
    if not td.exists():
        return {"templates": [], "error": "Templates directory not found"}

    yaml_files = sorted(td.glob("*.yaml"))
    result = []
    for f in yaml_files:
        try:
            from dre.style.template import StyleTemplate
            tmpl = StyleTemplate.from_yaml(f)
            meta = tmpl.get_metadata()
            result.append({
                "name": f.stem,
                "description": meta.get("description", ""),
                "file": str(f.resolve()),
            })
        except Exception:
            result.append({
                "name": f.stem,
                "description": "(failed to load)",
                "file": str(f.resolve()),
            })

    return {"templates": result}


def get_document_info(docx_path: str) -> dict[str, Any]:
    """Return metadata about a rendered DOCX file."""
    from docx import Document as DocxDocument

    path = Path(docx_path)
    if not path.exists():
        return {"error": f"File not found: {docx_path}"}

    try:
        doc = DocxDocument(str(path))
        para_count = len(doc.paragraphs)
        table_count = len(doc.tables)
        section_count = len(doc.sections)
        char_count = sum(len(p.text) for p in doc.paragraphs)

        headings = []
        for p in doc.paragraphs:
            if p.style and p.style.name.startswith("Heading"):
                headings.append({
                    "text": p.text[:100],
                    "style": p.style.name,
                })

        return {
            "file": str(path.resolve()),
            "file_size_bytes": path.stat().st_size,
            "paragraphs": para_count,
            "tables": table_count,
            "sections": section_count,
            "characters": char_count,
            "headings": headings[:20],
        }
    except Exception as exc:
        return {"error": str(exc)}


# ---------------------------------------------------------------------------
#  Internal helpers
# ---------------------------------------------------------------------------

def _template_path(template_name: str) -> Path:
    from dre.config import templates_dir
    return templates_dir() / f"{template_name}.yaml"


def _default_output_name() -> str:
    import time
    return f"dre_output_{int(time.time())}.docx"
