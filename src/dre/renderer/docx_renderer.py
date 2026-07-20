"""Main DOCX renderer — walks the AST and produces a python-docx Document."""

from __future__ import annotations

from pathlib import Path

from docx import Document as DocxDocument
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

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

    # ------------------------------------------------------------------
    #  Word multi-level heading numbering (OOXML)
    # ------------------------------------------------------------------

    def _setup_heading_numbering(self, docx: DocxDocument) -> None:
        """Register a multi-level list definition for headings.

        Levels: H1=1.  H2=1.1.  H3=1.1.1.  H4=1.1.1.1.
        The numbering font and size match each heading level from the
        active template so numbers blend seamlessly with heading text.
        """
        numbering_part = docx.part.numbering_part
        root = numbering_part._element

        # Remove old definitions
        for stale in root.findall(qn("w:abstractNum")):
            if stale.get(qn("w:abstractNumId")) == "10":
                root.remove(stale)
        for stale in root.findall(qn("w:num")):
            if stale.get(qn("w:numId")) == "10":
                root.remove(stale)

        abn = OxmlElement("w:abstractNum")
        abn.set(qn("w:abstractNumId"), "10")
        mlt = OxmlElement("w:multiLevelType")
        mlt.set(qn("w:val"), "hybridMultilevel")
        abn.append(mlt)

        for ilvl, fmt in enumerate(["%1.", "%1.%2.", "%1.%2.%3.", "%1.%2.%3.%4."]):
            # Resolve the style for this heading level
            h_style = self._template.resolve_paragraph(f"heading{ilvl + 1}")

            lvl = OxmlElement("w:lvl")
            lvl.set(qn("w:ilvl"), str(ilvl))

            start = OxmlElement("w:start")
            start.set(qn("w:val"), "1"); lvl.append(start)

            nf = OxmlElement("w:numFmt")
            nf.set(qn("w:val"), "decimal"); lvl.append(nf)

            lt = OxmlElement("w:lvlText")
            lt.set(qn("w:val"), fmt); lvl.append(lt)

            jc = OxmlElement("w:lvlJc")
            jc.set(qn("w:val"), "left"); lvl.append(jc)

            # Number font matches heading font
            rPr = OxmlElement("w:rPr")
            rFonts = OxmlElement("w:rFonts")
            rFonts.set(qn("w:ascii"), h_style.font_name)
            rFonts.set(qn("w:hAnsi"), h_style.font_name)
            rFonts.set(qn("w:eastAsia"), h_style.font_name)
            rFonts.set(qn("w:cs"), h_style.font_name)
            rPr.append(rFonts)
            sz = OxmlElement("w:sz")
            # Python-docx stores sizes in EMU / 12700 -> Pt. Our template uses
            # strings like "14pt". Strip, convert to half-points for OOXML.
            sz_val = str(int(float(h_style.font_size.replace("pt", "")) * 2))
            sz.set(qn("w:val"), sz_val)
            rPr.append(sz)
            if h_style.bold:
                b = OxmlElement("w:b")
                rPr.append(b)
            lvl.append(rPr)

            pp = OxmlElement("w:pPr")
            ind = OxmlElement("w:ind")
            ind.set(qn("w:left"), "0")
            ind.set(qn("w:hanging"), "0")
            pp.append(ind); lvl.append(pp)

            abn.append(lvl)

        root.append(abn)

        nm = OxmlElement("w:num")
        nm.set(qn("w:numId"), "10")
        ref = OxmlElement("w:abstractNumId")
        ref.set(qn("w:val"), "10")
        nm.append(ref)
        root.append(nm)

    @staticmethod
    def _apply_heading_numbering(paragraph, level: int) -> None:
        """Tag a heading paragraph with Word auto-numbering.

        ``level`` is 1-indexed (H1=1, H2=2, ...).
        """
        pPr = paragraph._p.get_or_add_pPr()
        numPr = OxmlElement("w:numPr")
        ilvl_el = OxmlElement("w:ilvl")
        ilvl_el.set(qn("w:val"), str(level - 1))
        numId_el = OxmlElement("w:numId")
        numId_el.set(qn("w:val"), "10")
        numPr.append(ilvl_el)
        numPr.append(numId_el)
        pPr.append(numPr)

    @staticmethod
    def _strip_existing_number(text: str) -> str:
        """Remove any pre-existing numbering from heading text."""
        import re
        patterns = [
            r'^第[一二三四五六七八九十\d]+[章节篇]\s*',
            r'^[一二三四五六七八九十]+[、．]\s*',
            r'^（[一二三四五六七八九十]+）\s*',
            r'^\d+(\.\d+)*[\.、．\s]\s*',
        ]
        for pat in patterns:
            text = re.sub(pat, '', text, count=1)
        return text.strip()

    # ------------------------------------------------------------------
    #  Public API
    # ------------------------------------------------------------------

    def render(self, document: Document, output_path: str | Path) -> Path:
        """Render *document* AST to a DOCX file at *output_path*.

        Returns the resolved output path.
        """
        output_path = Path(output_path)
        docx = DocxDocument()

        self._setup_document(docx)

        # Insert TOC if requested
        has_toc = any(isinstance(c, TableOfContents) for c in document.children)
        if has_toc:
            toc_cfg = self._template.get_toc_config()
            add_toc_title(docx, toc_cfg)
            insert_toc(docx, toc_cfg, self._template.resolve_paragraph("heading1"))
            docx.add_paragraph()

        for child in document.children:
            self._render_node(docx, child)

        docx.save(str(output_path))
        return output_path

    # ------------------------------------------------------------------
    #  Internal
    # ------------------------------------------------------------------

    def _setup_document(self, docx: DocxDocument) -> None:
        page = self._template.get_page_setup()
        setup_page(docx, page)
        hdr = self._template.get_header_content()
        if hdr.text or hdr.show_page_number:
            setup_header(docx, hdr)
        ftr = self._template.get_footer_content()
        if ftr.text or ftr.show_page_number:
            setup_footer(docx, ftr)
        self._setup_heading_numbering(docx)
        reset_image_counter()

    def _render_node(self, docx: DocxDocument, node: DocumentNode) -> None:
        if isinstance(node, Heading):
            style_key = f"heading{min(node.level, 6)}"
            style = self._template.resolve_paragraph(style_key)
            node.text = self._strip_existing_number(node.text)
            pr = ParagraphRenderer(docx)
            para = pr.render_heading(node, style)
            self._apply_heading_numbering(para, node.level)

        elif isinstance(node, Paragraph):
            style = self._template.resolve_paragraph("body")
            ParagraphRenderer(docx).render_paragraph(node, style)

        elif isinstance(node, BulletList):
            ListRenderer(docx).render_bullet_list(
                node, self._template.resolve_paragraph("list_item"))

        elif isinstance(node, OrderedList):
            ListRenderer(docx).render_ordered_list(
                node, self._template.resolve_paragraph("list_item"))

        elif isinstance(node, TableNode):
            TableRenderer(docx).render_table(
                node, self._template.get_table_style(),
                self._template.resolve_paragraph("caption"),
                self._template.resolve_paragraph("body"))

        elif isinstance(node, Image):
            ImageRenderer(docx).render_image(
                node, self._template.resolve_paragraph("caption"))

        elif isinstance(node, CodeBlock):
            CodeBlockRenderer(docx).render_code_block(
                node, self._template.resolve_paragraph("code_block"))

        elif isinstance(node, BlockQuote):
            ParagraphRenderer(docx).render_paragraph(
                Paragraph(text=node.text),
                self._template.resolve_paragraph("blockquote"))

        elif isinstance(node, TableOfContents):
            pass  # handled in render()

        elif isinstance(node, Document):
            for child in node.children:
                self._render_node(docx, child)
