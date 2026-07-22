"""Built-in fallback style values when the YAML template omits optional fields."""

from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
#  Style data classes
# ---------------------------------------------------------------------------

@dataclass
class ParagraphStyle:
    """Paragraph-level formatting properties."""

    font_name: str = "SimSun"
    font_size: str = "12pt"
    bold: bool = False
    italic: bool = False
    color: str = "000000"
    alignment: str = "justify"  # left / center / right / justify
    space_before: str = "0pt"
    space_after: str = "0pt"
    line_spacing: float = 1.5
    first_line_indent: str = "0cm"
    left_indent: str = "0cm"
    outline_level: Optional[int] = None
    keep_with_next: bool = False
    page_break_before: bool = False


@dataclass
class TableStyle:
    """Table formatting properties."""

    font_name: str = "SimSun"
    font_size: str = "10.5pt"
    header_bg: str = "1F4E79"
    header_font_color: str = "FFFFFF"
    header_bold: bool = True
    row_alt_color: str = "F2F2F2"
    border_color: str = "D9D9D9"


@dataclass
class PageSetup:
    """Page dimensions and margins."""

    size: str = "A4"
    orientation: str = "portrait"
    margin_top: str = "2.54cm"
    margin_bottom: str = "2.54cm"
    margin_left: str = "3.17cm"
    margin_right: str = "3.17cm"


@dataclass
class HeaderFooterContent:
    """Header / footer text and formatting."""

    text: str = ""
    font_name: str = "SimSun"
    font_size: str = "9pt"
    alignment: str = "center"
    show_page_number: bool = False
    page_number_format: str = "{page} / {numpages}"


@dataclass
class TOCConfig:
    """Table-of-contents generation settings."""

    title: str = "目  录"
    title_font_name: str = "SimHei"
    title_font_size: str = "16pt"
    levels: int = 3


@dataclass
class CaptionNumberingConfig:
    """Auto-numbering settings for figures and tables."""

    enabled: bool = True
    mode: str = "sequential"  # "sequential" (Fig 1, Fig 2) | "chapter" (Fig 1-1)
    figure_prefix: str = "图"
    table_prefix: str = "表"
    separator: str = " "       # between prefix and caption text


# ---------------------------------------------------------------------------
#  Default template (used when no YAML template is specified)
# ---------------------------------------------------------------------------

DEFAULT_PARAGRAPH_STYLES: dict[str, ParagraphStyle] = {
    "heading1": ParagraphStyle(
        font_name="SimHei", font_size="16pt", bold=True,
        space_before="18pt", space_after="12pt", outline_level=1,
    ),
    "heading2": ParagraphStyle(
        font_name="SimHei", font_size="14pt", bold=True,
        space_before="12pt", space_after="8pt", outline_level=2,
    ),
    "heading3": ParagraphStyle(
        font_name="SimHei", font_size="13pt", bold=True,
        space_before="10pt", space_after="6pt", outline_level=3,
    ),
    "heading4": ParagraphStyle(
        font_name="SimHei", font_size="12pt", bold=True,
        space_before="8pt", space_after="4pt", outline_level=4,
    ),
    "heading5": ParagraphStyle(
        font_name="SimHei", font_size="12pt", bold=True,
        space_before="6pt", space_after="3pt", outline_level=5,
    ),
    "heading6": ParagraphStyle(
        font_name="SimHei", font_size="12pt", bold=True,
        space_before="6pt", space_after="3pt", outline_level=6,
    ),
    "body": ParagraphStyle(
        font_name="SimSun", font_size="12pt",
        first_line_indent="0.74cm",
    ),
    "list_item": ParagraphStyle(
        font_name="SimSun", font_size="12pt",
        space_before="2pt", space_after="2pt",
    ),
    "code_block": ParagraphStyle(
        font_name="Consolas", font_size="10pt",
        color="1E1E1E", line_spacing=1.2,
        space_before="6pt", space_after="6pt",
    ),
    "blockquote": ParagraphStyle(
        font_name="SimSun", font_size="11pt",
        italic=True, color="666666",
        space_before="6pt", space_after="6pt",
        left_indent="1cm",
    ),
    "caption": ParagraphStyle(
        font_name="SimSun", font_size="10.5pt",
    ),
}

DEFAULT_TABLE_STYLE = TableStyle()
DEFAULT_PAGE_SETUP = PageSetup()
DEFAULT_HEADER = HeaderFooterContent()
DEFAULT_FOOTER = HeaderFooterContent(show_page_number=True)
DEFAULT_TOC_CONFIG = TOCConfig()
DEFAULT_CAPTION_NUMBERING = CaptionNumberingConfig()
