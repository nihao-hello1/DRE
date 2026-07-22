"""Style template loader — loads, validates, holds YAML style definitions.

A StyleTemplate converts the raw YAML dict into the style data classes
used by the resolver, falling back to built-in defaults for any values
the YAML omits.

Template inheritance::

    # academic.yaml — only 20 lines of YAML, not 130
    inherits: standard
    name: "学术论文"
    styles:
      body:
        font_size: "12pt"        # override body; everything else from standard

A child template inherits all settings from its parent and only needs
to specify what differs.  Inheritance chains are resolved recursively
with cycle detection.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

import yaml

from dre.style.defaults import (
    DEFAULT_CAPTION_NUMBERING,
    DEFAULT_FOOTER,
    DEFAULT_HEADER,
    DEFAULT_PAGE_SETUP,
    DEFAULT_PARAGRAPH_STYLES,
    DEFAULT_TABLE_STYLE,
    DEFAULT_TOC_CONFIG,
    CaptionNumberingConfig,
    HeaderFooterContent,
    PageSetup,
    ParagraphStyle,
    TableStyle,
    TOCConfig,
)


# ---------------------------------------------------------------------------
#  Error classes
# ---------------------------------------------------------------------------

class TemplateError(Exception):
    """Raised when a template file is invalid or cannot be loaded."""


class TemplateValidationError(TemplateError):
    """Raised when a template fails validation checks."""


class TemplateInheritanceError(TemplateError):
    """Raised when template inheritance has a problem (cycle, missing parent, etc.)."""


# ---------------------------------------------------------------------------
#  StyleTemplate
# ---------------------------------------------------------------------------

class StyleTemplate:
    """Holds all style rules parsed from a YAML template file.

    Typical usage::

        template = StyleTemplate.from_yaml("templates/tech_design.yaml")
        h1_style = template.resolve_paragraph("heading1")
        page = template.get_page_setup()
    """

    def __init__(self) -> None:
        self._raw: dict[str, Any] = {}
        self._paragraph_styles: dict[str, ParagraphStyle] = {}
        self._table_style: TableStyle = DEFAULT_TABLE_STYLE
        self._page_setup: PageSetup = DEFAULT_PAGE_SETUP
        self._header: HeaderFooterContent = DEFAULT_HEADER
        self._footer: HeaderFooterContent = DEFAULT_FOOTER
        self._toc_config: TOCConfig = DEFAULT_TOC_CONFIG
        self._caption_numbering: CaptionNumberingConfig = DEFAULT_CAPTION_NUMBERING

    # ---- Factory methods --------------------------------------------------

    @classmethod
    def from_yaml(cls, path: str | Path, _chain: Optional[set[str]] = None) -> "StyleTemplate":
        """Load and validate a YAML template file.

        Supports ``inherits: <parent_name>`` — when present, the parent
        template is loaded first and the child only overrides what it
        specifies.  Inheritance chains are resolved recursively with
        cycle detection.

        Raises:
            TemplateError: If the file cannot be read or parsed.
            TemplateValidationError: If required fields are missing.
            TemplateInheritanceError: If inheritance chain is circular or broken.
        """
        path = Path(path)
        if not path.exists():
            raise TemplateError(f"Template file not found: {path}")

        try:
            raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            raise TemplateError(f"YAML parse error in {path.name}: {exc}") from exc

        if not isinstance(raw, dict):
            raise TemplateError(f"{path.name}: expected a mapping (dict) at top level")

        # --- template inheritance ------------------------------------------
        parent_name = raw.pop("inherits", None)
        if parent_name is not None:
            if not isinstance(parent_name, str) or not parent_name.strip():
                raise TemplateInheritanceError(
                    f"{path.name}: 'inherits' must be a non-empty string (parent template name)"
                )

            # Cycle detection
            if _chain is None:
                _chain = set()
            canonical = str(Path(path).resolve())
            if parent_name in _chain:
                raise TemplateInheritanceError(
                    f"Circular template inheritance detected: "
                    f"{' → '.join(sorted(_chain))} → {parent_name}"
                )
            _chain.add(canonical)

            # Try to find parent template in the same directory
            parent_path = path.parent / f"{parent_name}.yaml"
            if not parent_path.exists():
                raise TemplateInheritanceError(
                    f"{path.name}: inherits from '{parent_name}' but "
                    f"'{parent_name}.yaml' not found in {path.parent}"
                )

            # Recursively load parent
            parent = cls.from_yaml(parent_path, _chain)
            parent_raw = parent._raw  # parent already resolved its own chain

            # Deep-merge: parent provides defaults, child overrides
            raw = _deep_merge(parent_raw, raw)

        return cls._from_dict(raw)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "StyleTemplate":
        """Build a template from an in-memory dict (useful for testing)."""
        return cls._from_dict(data)

    @classmethod
    def _from_dict(cls, raw: dict[str, Any]) -> "StyleTemplate":
        tmpl = cls()
        tmpl._raw = raw

        # Page setup
        if "page" in raw:
            tmpl._page_setup = _parse_page(raw["page"])

        # Paragraph styles
        if "styles" in raw:
            tmpl._paragraph_styles = _parse_styles(raw["styles"])
        else:
            tmpl._paragraph_styles = dict(DEFAULT_PARAGRAPH_STYLES)

        # Table style
        if "table" in raw:
            tmpl._table_style = _parse_table(raw["table"])

        # Header / Footer
        if "header" in raw:
            tmpl._header = _parse_header_footer(raw["header"])
        if "footer" in raw:
            tmpl._footer = _parse_header_footer(raw["footer"])

        # TOC
        if "toc" in raw:
            tmpl._toc_config = _parse_toc(raw["toc"])

        # Caption numbering
        if "numbering" in raw:
            tmpl._caption_numbering = _parse_caption_numbering(raw["numbering"])

        return tmpl

    # ---- Accessors --------------------------------------------------------

    def resolve_paragraph(self, style_key: str) -> ParagraphStyle:
        """Return a ParagraphStyle for the given style key (e.g. "heading1").

        Falls back to the built-in default if the key is not defined in the
        template; falls further to a generic body ParagraphStyle if even the
        built-in dict lacks this key.
        """
        # 1. Template-defined
        if style_key in self._paragraph_styles:
            return self._paragraph_styles[style_key]
        # 2. Built-in default
        if style_key in DEFAULT_PARAGRAPH_STYLES:
            return DEFAULT_PARAGRAPH_STYLES[style_key]
        # 3. Absolute fallback
        return DEFAULT_PARAGRAPH_STYLES.get("body", ParagraphStyle())

    def get_page_setup(self) -> PageSetup:
        return self._page_setup

    def get_table_style(self) -> TableStyle:
        return self._table_style

    def get_header_content(self) -> HeaderFooterContent:
        return self._header

    def get_footer_content(self) -> HeaderFooterContent:
        return self._footer

    def get_toc_config(self) -> TOCConfig:
        return self._toc_config

    def get_caption_numbering(self) -> CaptionNumberingConfig:
        """Return the figure/table auto-numbering configuration."""
        return self._caption_numbering

    def get_metadata(self) -> dict[str, Any]:
        """Return the non-style metadata (name, description)."""
        return {
            "name": self._raw.get("name", ""),
            "description": self._raw.get("description", ""),
        }

    def to_debug_dict(self) -> dict[str, Any]:
        """Return a JSON-friendly representation for debugging."""
        return {
            "metadata": self.get_metadata(),
            "page": {
                "size": self._page_setup.size,
                "orientation": self._page_setup.orientation,
                "margins": {
                    "top": self._page_setup.margin_top,
                    "bottom": self._page_setup.margin_bottom,
                    "left": self._page_setup.margin_left,
                    "right": self._page_setup.margin_right,
                },
            },
            "paragraph_styles": {
                k: {
                    "font_name": v.font_name,
                    "font_size": v.font_size,
                    "bold": v.bold,
                    "color": v.color,
                    "alignment": v.alignment,
                    "space_before": v.space_before,
                    "space_after": v.space_after,
                    "line_spacing": v.line_spacing,
                    "first_line_indent": v.first_line_indent,
                    "outline_level": v.outline_level,
                }
                for k, v in sorted(self._paragraph_styles.items())
            },
            "table": {
                "font_name": self._table_style.font_name,
                "font_size": self._table_style.font_size,
                "header_bg": self._table_style.header_bg,
                "header_font_color": self._table_style.header_font_color,
            },
            "header": {
                "text": self._header.text,
                "alignment": self._header.alignment,
            },
            "footer": {
                "show_page_number": self._footer.show_page_number,
                "alignment": self._footer.alignment,
            },
            "toc": {
                "title": self._toc_config.title,
                "levels": self._toc_config.levels,
            },
            "numbering": {
                "enabled": self._caption_numbering.enabled,
                "mode": self._caption_numbering.mode,
                "figure_prefix": self._caption_numbering.figure_prefix,
                "table_prefix": self._caption_numbering.table_prefix,
            },
        }


# ===================================================================
#  Template inheritance: deep-merge helper
# ===================================================================

def _deep_merge(base: dict, override: dict) -> dict:
    """Recursively merge *override* into *base*.

    - Keys only in *override* are added.
    - Keys in both: if both values are dicts, recurse; else *override* wins.
    - Keys only in *base* stay unchanged.

    Returns a new dict — neither *base* nor *override* is mutated.
    """
    result = dict(base)  # shallow copy
    for key, val in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(val, dict):
            result[key] = _deep_merge(result[key], val)
        else:
            result[key] = val
    return result


# ===================================================================
#  Internal parsing helpers
# ===================================================================

def _parse_page(data: Any) -> PageSetup:
    if not isinstance(data, dict):
        return DEFAULT_PAGE_SETUP

    setup = PageSetup()
    if "size" in data:
        setup.size = str(data["size"])
    if "orientation" in data:
        setup.orientation = str(data["orientation"])
    margins = data.get("margins", {})
    if isinstance(margins, dict):
        setup.margin_top = str(margins.get("top", setup.margin_top))
        setup.margin_bottom = str(margins.get("bottom", setup.margin_bottom))
        setup.margin_left = str(margins.get("left", setup.margin_left))
        setup.margin_right = str(margins.get("right", setup.margin_right))
    return setup


def _parse_styles(data: Any) -> dict[str, ParagraphStyle]:
    if not isinstance(data, dict):
        return dict(DEFAULT_PARAGRAPH_STYLES)

    styles: dict[str, ParagraphStyle] = {}
    for key, value in data.items():
        if not isinstance(value, dict):
            continue
        default = DEFAULT_PARAGRAPH_STYLES.get(key, ParagraphStyle())
        styles[key] = ParagraphStyle(
            font_name=_str(value, "font_name", default.font_name),
            font_size=_str(value, "font_size", default.font_size),
            bold=_bool(value, "bold", default.bold),
            italic=_bool(value, "italic", default.italic),
            color=_str(value, "color", default.color),
            alignment=_str(value, "alignment", default.alignment),
            space_before=_str(value, "space_before", default.space_before),
            space_after=_str(value, "space_after", default.space_after),
            line_spacing=_float(value, "line_spacing", default.line_spacing),
            first_line_indent=_str(value, "first_line_indent", default.first_line_indent),
            left_indent=_str(value, "left_indent", default.left_indent),
            outline_level=_int_or_none(value, "outline_level", default.outline_level),
            keep_with_next=_bool(value, "keep_with_next", default.keep_with_next),
            page_break_before=_bool(value, "page_break_before", default.page_break_before),
        )
    # Merge with defaults — template values win, but any key the template
    # doesn't define still gets a fallback
    merged = dict(DEFAULT_PARAGRAPH_STYLES)
    merged.update(styles)
    return merged


def _parse_table(data: Any) -> TableStyle:
    if not isinstance(data, dict):
        return DEFAULT_TABLE_STYLE
    return TableStyle(
        font_name=_str(data, "font_name", DEFAULT_TABLE_STYLE.font_name),
        font_size=_str(data, "font_size", DEFAULT_TABLE_STYLE.font_size),
        header_bg=_str(data, "header_bg", DEFAULT_TABLE_STYLE.header_bg),
        header_font_color=_str(data, "header_font_color", DEFAULT_TABLE_STYLE.header_font_color),
        header_bold=_bool(data, "header_bold", DEFAULT_TABLE_STYLE.header_bold),
        row_alt_color=_str(data, "row_alt_color", DEFAULT_TABLE_STYLE.row_alt_color),
        border_color=_str(data, "border_color", DEFAULT_TABLE_STYLE.border_color),
    )


def _parse_header_footer(data: Any) -> HeaderFooterContent:
    if not isinstance(data, dict):
        return HeaderFooterContent()
    return HeaderFooterContent(
        text=_str(data, "text", ""),
        font_name=_str(data, "font_name", "SimSun"),
        font_size=_str(data, "font_size", "9pt"),
        alignment=_str(data, "alignment", "center"),
        show_page_number=_bool(data, "show_page_number", False),
        page_number_format=_str(data, "page_number_format", "{page} / {numpages}"),
    )


def _parse_toc(data: Any) -> TOCConfig:
    if not isinstance(data, dict):
        return DEFAULT_TOC_CONFIG
    return TOCConfig(
        title=_str(data, "title", DEFAULT_TOC_CONFIG.title),
        title_font_name=_str(data, "title_font_name", DEFAULT_TOC_CONFIG.title_font_name),
        title_font_size=_str(data, "title_font_size", DEFAULT_TOC_CONFIG.title_font_size),
        levels=_int(data, "levels", DEFAULT_TOC_CONFIG.levels),
    )


def _parse_caption_numbering(data: Any) -> CaptionNumberingConfig:
    """Parse the ``numbering`` section of a template YAML.

    Expected shape::

        numbering:
          figures:
            enabled: true
            prefix: "图"
            mode: "chapter"
          tables:
            enabled: true
            prefix: "表"
            mode: "sequential"
    """
    if not isinstance(data, dict):
        return DEFAULT_CAPTION_NUMBERING

    fig_data = data.get("figures", {}) if isinstance(data.get("figures", None), dict) else {}
    tbl_data = data.get("tables", {}) if isinstance(data.get("tables", None), dict) else {}

    return CaptionNumberingConfig(
        enabled=_bool(data, "enabled", DEFAULT_CAPTION_NUMBERING.enabled),
        mode=_str(data, "mode", DEFAULT_CAPTION_NUMBERING.mode),
        figure_prefix=_str(fig_data, "prefix", DEFAULT_CAPTION_NUMBERING.figure_prefix),
        table_prefix=_str(tbl_data, "prefix", DEFAULT_CAPTION_NUMBERING.table_prefix),
        separator=_str(data, "separator", DEFAULT_CAPTION_NUMBERING.separator),
    )


# ===================================================================
#  Type-coercion helpers (lenient on values from YAML)
# ===================================================================

def _str(d: dict, key: str, default: str) -> str:
    v = d.get(key)
    return str(v) if v is not None else default


def _bool(d: dict, key: str, default: bool) -> bool:
    v = d.get(key)
    return bool(v) if v is not None else default


def _int(d: dict, key: str, default: int) -> int:
    v = d.get(key)
    return int(v) if v is not None else default


def _float(d: dict, key: str, default: float) -> float:
    v = d.get(key)
    return float(v) if v is not None else default


def _int_or_none(d: dict, key: str, default: Optional[int]) -> Optional[int]:
    v = d.get(key)
    return int(v) if v is not None else default
