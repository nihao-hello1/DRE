"""Main DOCX renderer — walks the AST and produces a python-docx Document."""

from __future__ import annotations

from pathlib import Path

from docx import Document as DocxDocument

from dre.ast.nodes import (
    BlockQuote,
    BulletList,
    CodeBlock,
    Document,
    DocumentNode,
    Heading,
    Image,
    OrderedList,
    Paragraph,
    Table as TableNode,
    TableOfContents,
)
from dre.renderer.code_block import CodeBlockRenderer
from dre.renderer.image import ImageRenderer, reset_image_counter
from dre.renderer.list import ListRenderer
from dre.renderer.paragraph import ParagraphRenderer
from dre.renderer.sections import setup_footer, setup_header, setup_page
from dre.renderer.table import TableRenderer
from dre.renderer.toc import add_toc_title, insert_toc
from dre.style.defaults import (
    DEFAULT_FOOTER,
    DEFAULT_HEADER,
    DEFAULT_PAGE_SETUP,
    DEFAULT_TABLE_STYLE,
    DEFAULT_TOC_CONFIG,
    ParagraphStyle,
)
from dre.style.template import StyleTemplate


class DocxRenderer:
    """Orchestrator that walks a Document AST and renders it to DOCX.

    Usage::

        renderer = DocxRenderer(template)
        renderer.render(document, "output.docx")
    """

    def __init__(self, template: StyleTemplate) -> None:
        self._template = template
        self._heading_counters: list[int] = [0] * 7  # index 1-6 for H1-H6

    def _heading_number(self, level: int) -> str:
        """Generate heading number like '1.' or '1.1.' or '1.1.1.' based on level."""
        if level < 1 or level > 6:
            return ""
        self._heading_counters[level] += 1
        for l in range(level + 1, 7):
            self._heading_counters[l] = 0
        parts = [str(self._heading_counters[l]) for l in range(1, level + 1) if self._heading_counters[l] > 0]
        return ".".join(parts) + ". "

    def render(self, document: Document, output_path: str | Path) -> Path:
        """Render *document* AST to a DOCX file at *output_path*.

        Returns the resolved output path.
        """
        output_path = Path(output_path)
        docx = DocxDocument()

        self._setup_document(docx)

        # Track whether we've placed the TOC
        toc_inserted = False
        has_toc_placeholder = any(
            isinstance(c, TableOfContents) for c in document.children
        )

        # Insert TOC title + field at the beginning if needed
        if has_toc_placeholder:
            toc_cfg = self._template.get_toc_config()
            add_toc_title(docx, toc_cfg)
            title_style = self._template.resolve_paragraph("heading1")
            insert_toc(docx, toc_cfg, title_style)
            # Add a blank paragraph after TOC
            docx.add_paragraph()
            toc_inserted = True

        # Render children
        for child in document.children:
            self._render_node(docx, child)

        # Save
        docx.save(str(output_path))
        return output_path

    # ------------------------------------------------------------------
    #  Internal dispatch
    # ------------------------------------------------------------------

    def _setup_document(self, docx: DocxDocument) -> None:
        """Apply page-level setup from the template."""
        page_setup = self._template.get_page_setup()
        setup_page(docx, page_setup)

        header = self._template.get_header_content()
        if header.text or header.show_page_number:
            setup_header(docx, header)

        footer = self._template.get_footer_content()
        setup_footer(docx, footer)

        reset_image_counter()

    def _render_node(self, docx: DocxDocument, node: DocumentNode) -> None:
        """Dispatch a single AST node to the appropriate renderer."""
        if isinstance(node, Heading):
            style_key = f"heading{min(node.level, 6)}"
            style = self._template.resolve_paragraph(style_key)
            # Auto-number the heading
            number = self._heading_number(node.level)
            node.numbering = number.rstrip('. ')
            node.text = number + node.text
            pr = ParagraphRenderer(docx)
            pr.render_heading(node, style)

        elif isinstance(node, Paragraph):
            style = self._template.resolve_paragraph("body")
            pr = ParagraphRenderer(docx)
            pr.render_paragraph(node, style)

        elif isinstance(node, BulletList):
            style = self._template.resolve_paragraph("list_item")
            lr = ListRenderer(docx)
            lr.render_bullet_list(node, style)

        elif isinstance(node, OrderedList):
            style = self._template.resolve_paragraph("list_item")
            lr = ListRenderer(docx)
            lr.render_ordered_list(node, style)

        elif isinstance(node, TableNode):
            table_style = self._template.get_table_style()
            caption_style = self._template.resolve_paragraph("caption")
            body_style = self._template.resolve_paragraph("body")
            tr = TableRenderer(docx)
            tr.render_table(node, table_style, caption_style, body_style)

        elif isinstance(node, Image):
            caption_style = self._template.resolve_paragraph("caption")
            ir = ImageRenderer(docx)
            ir.render_image(node, caption_style)

        elif isinstance(node, CodeBlock):
            style = self._template.resolve_paragraph("code_block")
            cr = CodeBlockRenderer(docx)
            cr.render_code_block(node, style)

        elif isinstance(node, BlockQuote):
            style = self._template.resolve_paragraph("blockquote")
            pr = ParagraphRenderer(docx)
            text = node.text
            # Wrap in a paragraph with blockquote style
            from dre.ast.nodes import Paragraph as ParaNode
            pseudo = ParaNode(text=text)
            pr.render_paragraph(pseudo, style)

        elif isinstance(node, TableOfContents):
            # Already inserted at setup time — skip here
            pass

        elif isinstance(node, Document):
            for child in node.children:
                self._render_node(docx, child)
